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
