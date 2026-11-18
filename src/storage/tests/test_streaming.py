import os
import zlib
from collections.abc import AsyncIterator, Iterator
from pathlib import Path
from typing import override

import httpx
import pytest
from httpx import AsyncClient, Client, MockTransport, Request, Response
from supabase_utils.http.adapters.httpx import AsyncHttpxSession, HttpxSession
from supabase_utils.http.errors import SupabaseTransportError

from storage3 import (
    AsyncStorageClient,
    StorageApiError,
    StorageDownloadTooLargeError,
    StorageException,
    StorageRangeIgnoredError,
    SyncStorageClient,
)

from .utils import STORAGE_URL

BODY = b"0123456789"
NOT_FOUND = (
    b'{"statusCode": "404", "error": "not_found", "message": "Object not found",'
    b' "code": "NoSuchKey"}'
)


class FailingStream(httpx.SyncByteStream, httpx.AsyncByteStream):
    @override
    def __iter__(self) -> Iterator[bytes]:
        yield b"01234"
        raise httpx.ReadError("connection dropped")

    @override
    async def __aiter__(self) -> AsyncIterator[bytes]:
        yield b"01234"
        raise httpx.ReadError("connection dropped")


class Storage:
    def __init__(self) -> None:
        self.requests: list[Request] = []
        self.bodies: list[bytes] = []

    def __call__(self, request: Request) -> Response:
        self.requests.append(request)
        self.bodies.append(request.read())
        if request.method != "GET":
            return Response(200, json={"Key": "bucket/file.txt", "Id": "id"})
        match request.url.path.rsplit("/", 1)[-1]:
            case "missing.txt":
                return Response(400, content=NOT_FOUND)
            case "partial.txt":
                return Response(
                    206, content=BODY[:5], headers={"Content-Range": "bytes 0-4/10"}
                )
            case "broken.txt":
                return Response(
                    200, stream=FailingStream(), headers={"Content-Length": "10"}
                )
            case "broken-range.txt":
                return Response(
                    206,
                    stream=FailingStream(),
                    headers={"Content-Range": "bytes 4-9/10"},
                )
            case "ranged.txt" if "range" in request.headers:
                return ranged(request.headers["range"])
            case _:
                return Response(200, content=BODY, headers={"Content-Type": "text/x"})

    def sync_client(self) -> SyncStorageClient:
        return SyncStorageClient(
            STORAGE_URL,
            {},
            http_session=HttpxSession(Client(transport=MockTransport(self))),
        )

    def async_client(self) -> AsyncStorageClient:
        return AsyncStorageClient(
            STORAGE_URL,
            {},
            http_session=AsyncHttpxSession(AsyncClient(transport=MockTransport(self))),
        )


def ranged(header: str) -> Response:
    first, last = header.removeprefix("bytes=").split("-")
    end = min(int(last), len(BODY) - 1) if last else len(BODY) - 1
    return Response(
        206,
        content=BODY[int(first) : end + 1],
        headers={"Content-Range": f"bytes {first}-{end}/{len(BODY)}"},
    )


def chunks() -> Iterator[bytes]:
    yield b"hello "
    yield b"world"


async def async_chunks() -> AsyncIterator[bytes]:
    yield b"hello "
    yield b"world"


@pytest.fixture
def storage() -> Storage:
    return Storage()


@pytest.fixture
def file(tmp_path: Path) -> Path:
    path = tmp_path / "upload.txt"
    path.write_bytes(b"hello world")
    return path


def test_upload_streams_a_file_at_a_path(storage: Storage, file: Path) -> None:
    bucket = storage.sync_client().from_("bucket")
    bucket.upload("file.txt", file)
    bucket.upload("file.txt", str(file))
    assert storage.bodies == [b"hello world", b"hello world"]
    assert [r.headers["content-length"] for r in storage.requests] == ["11", "11"]


def test_upload_streams_an_open_file_from_its_position(
    storage: Storage, file: Path
) -> None:
    with file.open("rb") as opened:
        opened.seek(6)
        storage.sync_client().from_("bucket").update("file.txt", opened)
        assert not opened.closed
    assert storage.bodies == [b"world"]
    assert storage.requests[0].headers["content-length"] == "5"


def test_upload_streams_an_iterator(storage: Storage) -> None:
    storage.sync_client().from_("bucket").upload_to_signed_url(
        "file.txt", "token", chunks()
    )
    assert storage.bodies == [b"hello world"]
    assert storage.requests[0].headers["transfer-encoding"] == "chunked"


async def test_async_upload_streams_every_kind_of_body(
    storage: Storage, file: Path
) -> None:
    bucket = storage.async_client().from_("bucket")
    await bucket.upload("file.txt", file)
    with file.open("rb") as opened:
        await bucket.upload("file.txt", opened)
    await bucket.upload("file.txt", chunks())
    await bucket.upload("file.txt", async_chunks())
    assert storage.bodies == [b"hello world"] * 4


def test_sync_upload_rejects_an_async_iterator(storage: Storage) -> None:
    with pytest.raises(TypeError, match="async iterable"):
        storage.sync_client().from_("bucket").upload("file.txt", async_chunks())


def test_download_stream_gives_the_head_and_then_the_body(storage: Storage) -> None:
    with storage.sync_client().from_("bucket").download_stream("a.txt") as download:
        assert download.status == 200
        assert download.content_length == 10
        assert download.content_type == "text/x"
        assert b"".join(download) == BODY


def test_download_stream_sends_the_cache_nonce(storage: Storage) -> None:
    bucket = storage.sync_client().from_("bucket")
    with bucket.download_stream("a.txt", cache_nonce="v2") as download:
        assert download.status == 200
    assert storage.requests[-1].url.params["cacheNonce"] == "v2"


def test_download_stream_sends_the_version_id(storage: Storage) -> None:
    bucket = storage.sync_client().from_("bucket")
    with bucket.download_stream("a.txt", version_id="v1") as download:
        assert download.read() == BODY
    assert storage.requests[-1].url.params["versionId"] == "v1"


async def test_async_download_stream_gives_the_head_and_then_the_body(
    storage: Storage,
) -> None:
    bucket = storage.async_client().from_("bucket")
    async with bucket.download_stream("a.txt") as download:
        assert download.status == 200
        assert b"".join([chunk async for chunk in download]) == BODY


def test_download_stream_returns_a_partial_response(storage: Storage) -> None:
    bucket = storage.sync_client().from_("bucket")
    with bucket.download_stream("partial.txt") as download:
        assert download.status == 206
        assert download.headers.get("content-range") == "bytes 0-4/10"
        assert download.read() == b"01234"


def test_download_stream_raises_the_storage_error(storage: Storage) -> None:
    bucket = storage.sync_client().from_("bucket")
    with (
        pytest.raises(StorageApiError) as caught,
        bucket.download_stream("missing.txt"),
    ):
        pytest.fail("the download must not be returned")
    assert caught.value.code == "NoSuchKey"


async def test_async_download_stream_raises_the_storage_error(
    storage: Storage,
) -> None:
    bucket = storage.async_client().from_("bucket")
    with pytest.raises(StorageApiError) as caught:
        async with bucket.download_stream("missing.txt"):
            pytest.fail("the download must not be returned")
    assert caught.value.code == "NoSuchKey"


def test_read_stops_past_the_cap(storage: Storage) -> None:
    bucket = storage.sync_client().from_("bucket")
    with bucket.download_stream("a.txt") as download:
        with pytest.raises(StorageDownloadTooLargeError) as caught:
            download.read(max_bytes=9)
        assert caught.value.max_bytes == 9
    with bucket.download_stream("a.txt") as download:
        assert download.read(max_bytes=10) == BODY


async def test_async_read_stops_past_the_cap(storage: Storage) -> None:
    bucket = storage.async_client().from_("bucket")
    async with bucket.download_stream("a.txt") as download:
        with pytest.raises(StorageDownloadTooLargeError):
            await download.read(max_bytes=9)


def test_a_failure_in_the_body_is_a_transport_error(storage: Storage) -> None:
    bucket = storage.sync_client().from_("bucket")
    with (
        bucket.download_stream("broken.txt") as download,
        pytest.raises(SupabaseTransportError),
    ):
        download.read()
    assert len(storage.requests) == 1


def test_write_to_replaces_the_destination(storage: Storage, tmp_path: Path) -> None:
    destination = tmp_path / "out.txt"
    destination.write_bytes(b"old")
    bucket = storage.sync_client().from_("bucket")
    with bucket.download_stream("a.txt") as download:
        download.write_to(destination)
    assert destination.read_bytes() == BODY
    assert list(tmp_path.iterdir()) == [destination]


def test_write_to_leaves_the_destination_on_failure(
    storage: Storage, tmp_path: Path
) -> None:
    destination = tmp_path / "out.txt"
    destination.write_bytes(b"old")
    bucket = storage.sync_client().from_("bucket")
    with (
        bucket.download_stream("broken.txt") as download,
        pytest.raises(SupabaseTransportError),
    ):
        download.write_to(destination)
    assert destination.read_bytes() == b"old"
    assert list(tmp_path.iterdir()) == [destination]


async def test_async_write_to_replaces_the_destination(
    storage: Storage, tmp_path: Path
) -> None:
    destination = tmp_path / "out.txt"
    bucket = storage.async_client().from_("bucket")
    async with bucket.download_stream("a.txt") as download:
        await download.write_to(destination)
    assert destination.read_bytes() == BODY
    assert list(tmp_path.iterdir()) == [destination]


async def test_async_write_to_leaves_the_destination_on_failure(
    storage: Storage, tmp_path: Path
) -> None:
    destination = tmp_path / "out.txt"
    destination.write_bytes(b"old")
    bucket = storage.async_client().from_("bucket")
    async with bucket.download_stream("broken.txt") as download:
        with pytest.raises(SupabaseTransportError):
            await download.write_to(destination)
    assert destination.read_bytes() == b"old"
    assert list(tmp_path.iterdir()) == [destination]


def test_write_to_keeps_permissions_and_follows_a_symlink(
    storage: Storage, tmp_path: Path
) -> None:
    target = tmp_path / "target.txt"
    target.write_bytes(b"old")
    target.chmod(0o600)
    link = tmp_path / "link.txt"
    link.symlink_to(target)
    bucket = storage.sync_client().from_("bucket")
    with bucket.download_stream("a.txt") as download:
        download.write_to(link)
    assert link.is_symlink()
    assert target.read_bytes() == BODY
    assert target.stat().st_mode & 0o777 == 0o600


def test_write_to_gives_a_new_file_the_default_mode(
    storage: Storage, tmp_path: Path
) -> None:
    destination = tmp_path / "new.txt"
    umask = os.umask(0o022)
    try:
        with storage.sync_client().from_("bucket").download_stream("a.txt") as download:
            download.write_to(destination)
    finally:
        os.umask(umask)
    assert destination.stat().st_mode & 0o777 == 0o644


@pytest.mark.parametrize(
    ("offset", "length", "header", "body"),
    [
        (2, 3, "bytes=2-4", BODY[2:5]),
        (6, None, "bytes=6-", BODY[6:]),
        (0, 4, "bytes=0-3", BODY[:4]),
        (8, 100, "bytes=8-107", BODY[8:]),
    ],
)
def test_download_sends_the_byte_range(
    storage: Storage, offset: int, length: int | None, header: str, body: bytes
) -> None:
    bucket = storage.sync_client().from_("bucket")
    assert bucket.download("ranged.txt", offset=offset, length=length) == body
    assert storage.requests[0].headers["range"] == header


def test_download_without_a_range_sends_no_range_header(storage: Storage) -> None:
    assert storage.sync_client().from_("bucket").download("ranged.txt") == BODY
    assert "range" not in storage.requests[0].headers


async def test_async_download_sends_the_byte_range(storage: Storage) -> None:
    bucket = storage.async_client().from_("bucket")
    assert await bucket.download("ranged.txt", offset=2, length=3) == BODY[2:5]
    assert storage.requests[0].headers["range"] == "bytes=2-4"


def test_download_raises_when_the_range_is_ignored(storage: Storage) -> None:
    bucket = storage.sync_client().from_("bucket")
    with pytest.raises(StorageRangeIgnoredError) as caught:
        bucket.download("a.txt", offset=2, length=3)
    assert caught.value.byte_range == "bytes=2-4"
    assert caught.value.status == 200
    assert "bytes=2-4" in str(caught.value)
    assert "200" in str(caught.value)
    assert not isinstance(caught.value, StorageApiError)
    assert len(storage.requests) == 1


async def test_async_download_raises_when_the_range_is_ignored(
    storage: Storage,
) -> None:
    bucket = storage.async_client().from_("bucket")
    with pytest.raises(StorageRangeIgnoredError):
        await bucket.download("a.txt", offset=2)


def test_ranged_download_raises_the_storage_error(storage: Storage) -> None:
    bucket = storage.sync_client().from_("bucket")
    with pytest.raises(StorageApiError) as caught:
        bucket.download("missing.txt", offset=2)
    assert caught.value.code == "NoSuchKey"


@pytest.mark.parametrize(("offset", "length"), [(-1, None), (0, 0), (5, -2)])
def test_an_invalid_range_raises_before_sending(
    storage: Storage, offset: int, length: int | None
) -> None:
    bucket = storage.sync_client().from_("bucket")
    with pytest.raises(ValueError, match=r"offset|length"):
        bucket.download("ranged.txt", offset=offset, length=length)
    with pytest.raises(ValueError, match=r"offset|length"):
        bucket.download_stream("ranged.txt", offset=offset, length=length)
    assert storage.requests == []


def test_download_stream_sends_the_byte_range(storage: Storage) -> None:
    bucket = storage.sync_client().from_("bucket")
    with bucket.download_stream("ranged.txt", offset=4, length=2) as download:
        assert download.status == 206
        assert download.headers.get("content-range") == "bytes 4-5/10"
        assert download.read() == BODY[4:6]
    assert storage.requests[0].headers["range"] == "bytes=4-5"


def test_download_stream_returns_an_ignored_range_as_it_is(storage: Storage) -> None:
    bucket = storage.sync_client().from_("bucket")
    with bucket.download_stream("a.txt", offset=4) as download:
        assert download.status == 200
        assert download.read() == BODY


def test_write_to_resumes_a_partial_file(storage: Storage, tmp_path: Path) -> None:
    destination = tmp_path / "out.txt"
    destination.write_bytes(BODY[:4])
    bucket = storage.sync_client().from_("bucket")
    with bucket.download_stream("ranged.txt", offset=4) as download:
        download.write_to(destination, resume=True)
    assert destination.read_bytes() == BODY
    assert storage.requests[0].headers["range"] == "bytes=4-"
    assert list(tmp_path.iterdir()) == [destination]


async def test_async_write_to_resumes_a_partial_file(
    storage: Storage, tmp_path: Path
) -> None:
    destination = tmp_path / "out.txt"
    destination.write_bytes(BODY[:4])
    bucket = storage.async_client().from_("bucket")
    async with bucket.download_stream("ranged.txt", offset=4) as download:
        await download.write_to(destination, resume=True)
    assert destination.read_bytes() == BODY


def test_write_to_resume_replaces_the_file_with_a_whole_body(
    storage: Storage, tmp_path: Path
) -> None:
    destination = tmp_path / "out.txt"
    destination.write_bytes(b"stale")
    bucket = storage.sync_client().from_("bucket")
    with bucket.download_stream("a.txt", offset=5) as download:
        download.write_to(destination, resume=True)
    assert destination.read_bytes() == BODY
    assert list(tmp_path.iterdir()) == [destination]


def test_write_to_resume_creates_a_missing_file(
    storage: Storage, tmp_path: Path
) -> None:
    destination = tmp_path / "out.txt"
    bucket = storage.sync_client().from_("bucket")
    with bucket.download_stream("ranged.txt") as download:
        download.write_to(destination, resume=True)
    assert destination.read_bytes() == BODY


def test_write_to_resume_rejects_a_range_that_does_not_continue_the_file(
    storage: Storage, tmp_path: Path
) -> None:
    destination = tmp_path / "out.txt"
    destination.write_bytes(BODY[:3])
    bucket = storage.sync_client().from_("bucket")
    with (
        bucket.download_stream("ranged.txt", offset=4) as download,
        pytest.raises(StorageException, match="starts at byte 4"),
    ):
        download.write_to(destination, resume=True)
    assert destination.read_bytes() == BODY[:3]


def test_write_to_resume_keeps_what_arrived_on_failure(
    storage: Storage, tmp_path: Path
) -> None:
    destination = tmp_path / "out.txt"
    destination.write_bytes(b"abcd")
    bucket = storage.sync_client().from_("bucket")
    with (
        bucket.download_stream("broken-range.txt", offset=4) as download,
        pytest.raises(SupabaseTransportError),
    ):
        download.write_to(destination, resume=True)
    assert destination.read_bytes() == b"abcd01234"


def test_write_to_without_resume_replaces_the_file_with_a_range(
    storage: Storage, tmp_path: Path
) -> None:
    destination = tmp_path / "out.txt"
    destination.write_bytes(BODY[:4])
    bucket = storage.sync_client().from_("bucket")
    with bucket.download_stream("ranged.txt", offset=4) as download:
        download.write_to(destination)
    assert destination.read_bytes() == BODY[4:]


@pytest.mark.parametrize(
    "content_range",
    ["bytes 4-3/10", "bytes 4-10/10", "bytes 4-/10", "bytes 4-9", "items 4-9/10", ""],
)
def test_write_to_resume_rejects_an_invalid_content_range(
    tmp_path: Path, content_range: str
) -> None:
    def handler(request: Request) -> Response:
        return Response(206, content=BODY[4:], headers={"Content-Range": content_range})

    client = SyncStorageClient(
        STORAGE_URL,
        {},
        http_session=HttpxSession(Client(transport=MockTransport(handler))),
    )
    destination = tmp_path / "out.txt"
    destination.write_bytes(BODY[:4])
    with (
        client.from_("bucket").download_stream("a.txt", offset=4) as download,
        pytest.raises(StorageException, match="invalid Content-Range"),
    ):
        download.write_to(destination, resume=True)
    assert destination.read_bytes() == BODY[:4]


@pytest.mark.parametrize("content_range", ["bytes 4-9/10", "bytes 4-9/*"])
def test_write_to_resume_accepts_a_valid_content_range(
    tmp_path: Path, content_range: str
) -> None:
    def handler(request: Request) -> Response:
        return Response(206, content=BODY[4:], headers={"Content-Range": content_range})

    client = SyncStorageClient(
        STORAGE_URL,
        {},
        http_session=HttpxSession(Client(transport=MockTransport(handler))),
    )
    destination = tmp_path / "out.txt"
    destination.write_bytes(BODY[:4])
    with client.from_("bucket").download_stream("a.txt", offset=4) as download:
        download.write_to(destination, resume=True)
    assert destination.read_bytes() == BODY


def partial_client(
    headers: dict[str, str], content: bytes = BODY[4:]
) -> SyncStorageClient:
    def handler(request: Request) -> Response:
        return Response(206, content=content, headers=headers)

    return SyncStorageClient(
        STORAGE_URL,
        {},
        http_session=HttpxSession(Client(transport=MockTransport(handler))),
    )


def test_a_ranged_request_asks_for_the_identity_encoding(storage: Storage) -> None:
    storage.sync_client().from_("bucket").download("ranged.txt", offset=2)
    assert storage.requests[0].headers["accept-encoding"] == "identity"


def test_write_to_resume_rejects_an_encoded_partial_body(tmp_path: Path) -> None:
    client = partial_client(
        {"Content-Range": "bytes 4-9/10", "Content-Encoding": "deflate"},
        zlib.compress(BODY[4:]),
    )
    destination = tmp_path / "out.txt"
    destination.write_bytes(BODY[:4])
    with (
        client.from_("bucket").download_stream("a.txt", offset=4) as download,
        pytest.raises(StorageException, match="encoded with deflate"),
    ):
        download.write_to(destination, resume=True)
    assert destination.read_bytes() == BODY[:4]


def test_download_rejects_a_partial_body_from_another_offset() -> None:
    client = partial_client({"Content-Range": "bytes 0-5/10"})
    with pytest.raises(StorageException, match="starts at byte 0"):
        client.from_("bucket").download("a.txt", offset=4)


def test_ranged_download_reports_progress(storage: Storage) -> None:
    progress: list[tuple[int, int | None]] = []
    bucket = storage.sync_client().from_("bucket")
    body = bucket.download(
        "ranged.txt",
        offset=4,
        on_progress=lambda moved, total: progress.append((moved, total)),
    )
    assert body == BODY[4:]
    assert progress[-1] == (6, 6)


def test_an_ignored_range_reports_no_progress(storage: Storage) -> None:
    progress: list[tuple[int, int | None]] = []
    bucket = storage.sync_client().from_("bucket")
    with pytest.raises(StorageRangeIgnoredError):
        bucket.download(
            "a.txt",
            offset=4,
            on_progress=lambda moved, total: progress.append((moved, total)),
        )
    assert progress == []
    assert len(storage.requests) == 1


def test_download_sends_if_match(storage: Storage) -> None:
    bucket = storage.sync_client().from_("bucket")
    bucket.download("ranged.txt", offset=4, if_match='"abc"')
    with bucket.download_stream("ranged.txt", offset=4, if_match='"abc"'):
        pass
    bucket.download("a.txt")
    assert [r.headers.get("if-match") for r in storage.requests] == [
        '"abc"',
        '"abc"',
        None,
    ]


def test_download_stream_gives_the_etag() -> None:
    client = partial_client({"Content-Range": "bytes 4-9/10", "ETag": '"abc"'})
    with client.from_("bucket").download_stream("a.txt", offset=4) as download:
        assert download.etag == '"abc"'
