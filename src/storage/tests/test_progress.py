from collections.abc import AsyncIterator, Iterator
from pathlib import Path
from types import SimpleNamespace
from typing import override

import httpx
import pytest
from httpx import AsyncClient, Client, MockTransport, Request, Response
from supabase_utils.http import io
from supabase_utils.http.adapters.httpx import AsyncHttpxSession, HttpxSession
from supabase_utils.http.body import CHUNK_SIZE, FileContent
from supabase_utils.http.retry import RetryPolicy

from storage3 import (
    AsyncStorageClient,
    ProgressCallback,
    StorageApiError,
    SyncStorageClient,
)
from storage3.progress import _counted_upload

from .utils import STORAGE_URL

BODY = b"0123456789"

type Reports = list[tuple[int, int | None]]


class DroppedStream(httpx.SyncByteStream, httpx.AsyncByteStream):
    @override
    def __iter__(self) -> Iterator[bytes]:
        yield BODY[:5]
        raise httpx.ReadError("connection dropped")

    @override
    async def __aiter__(self) -> AsyncIterator[bytes]:
        yield BODY[:5]
        raise httpx.ReadError("connection dropped")


class Storage:
    def __init__(self, failures: int = 0) -> None:
        self.failures = failures
        self.bodies: list[bytes] = []
        self.requests: list[Request] = []

    def __call__(self, request: Request) -> Response:
        self.requests.append(request)
        self.bodies.append(request.read())
        if len(self.requests) <= self.failures:
            return Response(
                503, json={"statusCode": "503", "error": "x", "message": "down"}
            )
        if request.method != "GET":
            return Response(200, json={"Key": "bucket/file.txt", "Id": "id"})
        match request.url.path.rsplit("/", 1)[-1]:
            case "missing.txt":
                return Response(
                    400,
                    json={"statusCode": "404", "error": "x", "message": "missing"},
                )
            case "encoded.txt":
                return Response(
                    200,
                    content=BODY,
                    headers={"Content-Length": "10", "Content-Encoding": "custom"},
                )
            case "dropped.txt" if len(self.requests) == 1:
                return Response(
                    200, stream=DroppedStream(), headers={"Content-Length": "10"}
                )
            case "unsized.txt":
                return Response(200, content=iter([BODY]))
            case _:
                return Response(200, content=BODY)

    def sync_client(self, retry: RetryPolicy | None = None) -> SyncStorageClient:
        return SyncStorageClient(
            STORAGE_URL,
            {},
            http_session=HttpxSession(Client(transport=MockTransport(self))),
            retry=retry,
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
def reports() -> Reports:
    return []


def record(reports: Reports) -> ProgressCallback:
    def on_progress(moved: int, total: int | None) -> None:
        reports.append((moved, total))

    return on_progress


def test_upload_reports_bytes_with_the_total(
    storage: Storage, reports: Reports
) -> None:
    storage.sync_client().from_("bucket").upload(
        "file.txt", b"hello world", on_progress=record(reports)
    )
    assert reports == [(0, 11), (11, 11)]
    assert storage.bodies == [b"hello world"]
    assert storage.requests[0].headers["content-length"] == "11"


def test_upload_of_a_file_reports_every_chunk(
    storage: Storage, reports: Reports, tmp_path: Path
) -> None:
    size = 2 * CHUNK_SIZE + 1
    path = tmp_path / "large.bin"
    path.write_bytes(b"x" * size)
    storage.sync_client().from_("bucket").update(
        "file.txt", path, on_progress=record(reports)
    )
    assert reports == [
        (0, size),
        (CHUNK_SIZE, size),
        (2 * CHUNK_SIZE, size),
        (size, size),
    ]
    assert storage.requests[0].headers["content-length"] == str(size)


def test_upload_of_an_iterator_has_no_total(storage: Storage, reports: Reports) -> None:
    storage.sync_client().from_("bucket").upload_to_signed_url(
        "file.txt", "token", chunks(), on_progress=record(reports)
    )
    assert reports == [(0, None), (6, None), (11, None)]
    assert storage.bodies == [b"hello world"]


def test_an_empty_upload_reports_once(storage: Storage, reports: Reports) -> None:
    storage.sync_client().from_("bucket").upload(
        "file.txt", b"", on_progress=record(reports)
    )
    assert reports == [(0, 0)]


def test_a_retried_upload_counts_again_from_zero(
    reports: Reports, monkeypatch: pytest.MonkeyPatch
) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr(io, "time", SimpleNamespace(sleep=sleeps.append))
    storage = Storage(failures=1)
    policy = RetryPolicy(retryable_methods={"POST"}, jitter=0)
    storage.sync_client(retry=policy).from_("bucket").upload(
        "file.txt", b"hello", on_progress=record(reports)
    )
    assert reports == [(0, 5), (5, 5), (0, 5), (5, 5)]
    assert storage.bodies == [b"hello", b"hello"]


async def test_async_upload_reports_every_kind_of_body(
    storage: Storage, tmp_path: Path
) -> None:
    path = tmp_path / "file.txt"
    path.write_bytes(b"hello world")
    bucket = storage.async_client().from_("bucket")
    for body in (b"hello world", path, chunks(), async_chunks()):
        reports: Reports = []
        await bucket.upload("file.txt", body, on_progress=record(reports))
        total = None if isinstance(body, (Iterator, AsyncIterator)) else 11
        assert reports[0] == (0, total)
        assert reports[-1] == (11, total)
    assert storage.bodies == [b"hello world"] * 4


def test_reports_stop_once_the_upload_ended(reports: Reports) -> None:
    content, progress = _counted_upload(b"hello", record(reports))
    assert isinstance(content, FileContent)
    first = iter(content)
    next(first)
    second = iter(content)
    next(second)
    next(first, None)
    progress.end()
    next(second, None)
    assert reports == [(0, 5), (0, 5)]


def test_download_reports_bytes_received(storage: Storage, reports: Reports) -> None:
    body = (
        storage.sync_client()
        .from_("bucket")
        .download("a.txt", on_progress=record(reports))
    )
    assert body == BODY
    assert reports == [(0, 10), (10, 10)]


def test_download_stream_reports_bytes_read(storage: Storage, reports: Reports) -> None:
    bucket = storage.sync_client().from_("bucket")
    with bucket.download_stream("a.txt", on_progress=record(reports)) as download:
        assert reports == []
        assert download.read() == BODY
    assert reports == [(0, 10), (10, 10)]


def test_download_reports_a_chunk_when_it_is_handed_over(
    storage: Storage, reports: Reports
) -> None:
    bucket = storage.sync_client().from_("bucket")
    with bucket.download_stream("a.txt", on_progress=record(reports)) as download:
        assert next(iter(download)) == BODY
        assert reports == [(0, 10), (10, 10)]


@pytest.mark.parametrize("name", ["encoded.txt", "unsized.txt"])
def test_download_without_a_usable_length_has_no_total(
    storage: Storage, reports: Reports, name: str
) -> None:
    storage.sync_client().from_("bucket").download(name, on_progress=record(reports))
    assert reports == [(0, None), (10, None)]


def test_a_failed_download_reports_nothing(storage: Storage, reports: Reports) -> None:
    with pytest.raises(StorageApiError):
        storage.sync_client().from_("bucket").download(
            "missing.txt", on_progress=record(reports)
        )
    assert reports == []


async def test_async_download_reports_bytes_received(
    storage: Storage, reports: Reports, tmp_path: Path
) -> None:
    bucket = storage.async_client().from_("bucket")
    assert await bucket.download("a.txt", on_progress=record(reports)) == BODY
    async with bucket.download_stream("a.txt", on_progress=record(reports)) as d:
        await d.write_to(tmp_path / "out.txt")
    assert reports == [(0, 10), (10, 10)] * 2


def test_a_retried_download_counts_again_from_zero(
    storage: Storage, reports: Reports, monkeypatch: pytest.MonkeyPatch
) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr(io, "time", SimpleNamespace(sleep=sleeps.append))
    body = (
        storage.sync_client()
        .from_("bucket")
        .download("dropped.txt", on_progress=record(reports))
    )
    assert body == BODY
    assert reports == [(0, 10), (5, 10), (0, 10), (10, 10)]
    assert len(storage.requests) == 2


async def test_a_retried_async_download_counts_again_from_zero(
    storage: Storage, reports: Reports, monkeypatch: pytest.MonkeyPatch
) -> None:
    async def fake_sleep(delay: float) -> None:
        pass

    monkeypatch.setattr(io, "asyncio", SimpleNamespace(sleep=fake_sleep))
    body = (
        await storage.async_client()
        .from_("bucket")
        .download("dropped.txt", on_progress=record(reports))
    )
    assert body == BODY
    assert reports == [(0, 10), (5, 10), (0, 10), (10, 10)]
