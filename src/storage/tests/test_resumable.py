import base64
import io as stdlib_io
from pathlib import Path
from typing import Any, override

import httpx
import pytest
from httpx import AsyncClient, Client, MockTransport, Request, Response
from supabase_utils.http.adapters.httpx import AsyncHttpxSession, HttpxSession
from supabase_utils.http.errors import SupabaseTransportError
from supabase_utils.http.retry import RetryPolicy

from storage3 import (
    AsyncResumableUpload,
    AsyncStorageClient,
    ResumableUpload,
    ResumableUploadCancelledError,
    ResumableUploadPausedError,
    ResumableUploadSource,
    StorageApiError,
    StorageException,
    SyncStorageClient,
)
from storage3.types import UploadResponse

from .utils import STORAGE_URL, use_async

UPLOADS = f"{STORAGE_URL}upload/resumable"
DATA = bytes(range(10))
NO_WAIT = RetryPolicy(base_delay=0, jitter=0)

type Reports = list[tuple[int, int | None]]


class Unseekable(stdlib_io.RawIOBase):
    @override
    def readable(self) -> bool:
        return True

    @override
    def seekable(self) -> bool:
        return False


class TusServer:
    """A tus endpoint holding uploads in memory. `fail` maps the index of a
    request to the response or exception it gets instead."""

    def __init__(self) -> None:
        self.requests: list[Request] = []
        self.uploads: dict[str, bytearray] = {}
        self.lengths: dict[str, int] = {}
        self.fail: dict[int, Response | Exception] = {}

    @property
    def methods(self) -> list[str]:
        return [request.method for request in self.requests]

    def __call__(self, request: Request) -> Response:
        self.requests.append(request)
        body = request.read()
        failure = self.fail.get(len(self.requests) - 1)
        if isinstance(failure, Exception):
            raise failure
        if failure is not None:
            return failure
        assert request.headers["Tus-Resumable"] == "1.0.0"
        if request.method == "POST":
            upload_id = f"u{len(self.uploads)}"
            self.uploads[upload_id] = bytearray()
            self.lengths[upload_id] = int(request.headers["Upload-Length"])
            if self.lengths[upload_id] == 0:
                return self.completed(upload_id, 201)
            return Response(201, headers={"Location": f"{UPLOADS}/{upload_id}"})
        upload_id = request.url.path.rsplit("/", 1)[-1]
        if upload_id not in self.uploads:
            return Response(404, text="The file for this url was not found")
        held = self.uploads[upload_id]
        if request.method == "DELETE":
            del self.uploads[upload_id]
            return Response(204)
        if request.method == "HEAD":
            if len(held) == self.lengths[upload_id]:
                response = self.completed(upload_id, 200)
                del response.headers["Tus-Complete"]
                return response
            return Response(200, headers={"Upload-Offset": str(len(held))})
        if int(request.headers["Upload-Offset"]) != len(held):
            return Response(409, text="Upload-Offset conflict")
        held.extend(body)
        if len(held) == self.lengths[upload_id]:
            return self.completed(upload_id, 204)
        return Response(204, headers={"Upload-Offset": str(len(held))})

    def completed(self, upload_id: str, status: int) -> Response:
        return Response(
            status,
            headers={
                "Upload-Offset": str(self.lengths[upload_id]),
                "Tus-Complete": "1",
                "Supabase-Object-Id": f"object-{upload_id}",
                "Supabase-Object-Version-Id": "version",
            },
        )

    def sync_client(self) -> SyncStorageClient:
        return SyncStorageClient(
            STORAGE_URL,
            {"Authorization": "Bearer key"},
            http_session=HttpxSession(Client(transport=MockTransport(self))),
            retry=NO_WAIT,
        )

    def async_client(self) -> AsyncStorageClient:
        return AsyncStorageClient(
            STORAGE_URL,
            {"Authorization": "Bearer key"},
            http_session=AsyncHttpxSession(AsyncClient(transport=MockTransport(self))),
            retry=NO_WAIT,
        )


@pytest.fixture
def server() -> TusServer:
    return TusServer()


type Upload = ResumableUpload | AsyncResumableUpload


async def run(upload: Upload) -> UploadResponse:
    if isinstance(upload, AsyncResumableUpload):
        return await upload.run()
    return upload.run()


async def cancel(upload: Upload) -> None:
    if isinstance(upload, AsyncResumableUpload):
        await upload.cancel()
    else:
        upload.cancel()


def upload_of(
    server: TusServer,
    use_async: bool,
    file: ResumableUploadSource = DATA,
    **options: Any,
) -> Upload:
    options.setdefault("chunk_size", 4)
    if use_async:
        bucket = server.async_client().from_("videos")
        return bucket.resumable_upload("folder/clip.bin", file, **options)
    return (
        server.sync_client()
        .from_("videos")
        .resumable_upload("folder/clip.bin", file, **options)
    )


def decoded_metadata(request: Request) -> dict[str, str]:
    pairs = (item.split(" ") for item in request.headers["Upload-Metadata"].split(","))
    return {key: base64.b64decode(value).decode() for key, value in pairs}


@use_async
async def test_uploads_the_file_in_chunks(server: TusServer, use_async: bool) -> None:
    reports: Reports = []

    def record(moved: int, total: int | None) -> None:
        reports.append((moved, total))

    upload = upload_of(
        server,
        use_async,
        metadata={"source": "test"},
        content_type="video/mp4",
        on_progress=record,
    )

    response = await run(upload)

    assert response == UploadResponse(
        id="object-u0",
        path="folder/clip.bin",
        full_path="videos/folder/clip.bin",
        version="version",
    )
    assert server.uploads["u0"] == DATA
    assert server.methods == ["POST", "PATCH", "PATCH", "PATCH"]
    create = server.requests[0]
    assert create.headers["Upload-Length"] == "10"
    assert create.headers["Authorization"] == "Bearer key"
    assert "x-upsert" not in create.headers
    assert decoded_metadata(create) == {
        "bucketName": "videos",
        "objectName": "folder/clip.bin",
        "contentType": "video/mp4",
        "cacheControl": "3600",
        "metadata": '{"source":"test"}',
    }
    patch = server.requests[2]
    assert patch.headers["Upload-Offset"] == "4"
    assert patch.headers["Content-Type"] == "application/offset+octet-stream"
    assert patch.headers["Content-Length"] == "4"
    assert reports[-1] == (10, 10)
    assert [moved for moved, _ in reports] == sorted(moved for moved, _ in reports)
    assert upload.offset == 10
    assert upload.url is None


@use_async
async def test_reads_a_file_from_a_path(
    server: TusServer, use_async: bool, tmp_path: Path
) -> None:
    path = tmp_path / "clip.bin"
    path.write_bytes(DATA)

    await run(upload_of(server, use_async, path, upsert=True))

    assert server.uploads["u0"] == DATA
    assert server.requests[0].headers["x-upsert"] == "true"


@use_async
async def test_reads_a_file_object_from_its_position(
    server: TusServer, use_async: bool
) -> None:
    file = stdlib_io.BytesIO(b"skip" + DATA)
    file.seek(4)

    upload = upload_of(server, use_async, file)
    await run(upload)

    assert server.uploads["u0"] == DATA
    assert upload.fingerprint is None


@use_async
async def test_uploads_an_empty_file_on_create(
    server: TusServer, use_async: bool
) -> None:
    response = await run(upload_of(server, use_async, b""))

    assert response.id == "object-u0"
    assert server.methods == ["POST"]


@use_async
async def test_reads_the_offset_again_after_a_network_error(
    server: TusServer, use_async: bool
) -> None:
    server.fail[2] = httpx.ConnectError("connection dropped")

    await run(upload_of(server, use_async))

    assert server.uploads["u0"] == DATA
    assert server.methods == ["POST", "PATCH", "PATCH", "HEAD", "PATCH", "PATCH"]
    assert server.requests[4].headers["Upload-Offset"] == "4"


@use_async
async def test_reads_the_offset_again_after_an_offset_conflict(
    server: TusServer, use_async: bool
) -> None:
    server.fail[1] = Response(409, text="Upload-Offset conflict")

    await run(upload_of(server, use_async))

    assert server.uploads["u0"] == DATA
    assert server.methods[:3] == ["POST", "PATCH", "HEAD"]


@use_async
async def test_gives_up_once_the_retries_are_used_up(
    server: TusServer, use_async: bool
) -> None:
    for index in range(1, 10):
        server.fail[index] = Response(503, text="Service Unavailable")
    store: dict[str, str] = {}

    upload = upload_of(server, use_async, store=store)
    with pytest.raises(StorageApiError) as caught:
        await run(upload)

    assert caught.value.status_code == 503
    assert caught.value.code == "ServiceUnavailable"
    assert server.methods == ["POST", "PATCH", "HEAD", "HEAD", "HEAD"]
    assert store == {upload.fingerprint: f"{UPLOADS}/u0"}


@use_async
async def test_starts_over_when_the_upload_expired(
    server: TusServer, use_async: bool
) -> None:
    fingerprint = upload_of(server, use_async).fingerprint
    assert fingerprint is not None
    store = {fingerprint: f"{UPLOADS}/expired"}

    await run(upload_of(server, use_async, store=store))

    assert server.methods[:2] == ["HEAD", "POST"]
    assert server.uploads["u0"] == DATA
    assert store == {}


@use_async
async def test_continues_the_upload_kept_in_the_store(
    server: TusServer, use_async: bool
) -> None:
    store: dict[str, str] = {}

    def pause_after_the_first_chunk(moved: int, total: int | None) -> None:
        if moved == 4:
            first.pause()

    first = upload_of(
        server, use_async, store=store, on_progress=pause_after_the_first_chunk
    )
    with pytest.raises(ResumableUploadPausedError):
        await run(first)
    assert first.offset == 4
    assert store == {first.fingerprint: f"{UPLOADS}/u0"}

    second = upload_of(server, use_async, store=store)
    await run(second)

    assert server.methods == ["POST", "PATCH", "HEAD", "PATCH", "PATCH"]
    assert server.uploads["u0"] == DATA
    assert store == {}


@use_async
async def test_run_continues_a_paused_upload(
    server: TusServer, use_async: bool
) -> None:
    pauses: list[int] = []

    def pause(moved: int, total: int | None) -> None:
        if moved == 4 and not pauses:
            pauses.append(moved)
            upload.pause()

    upload = upload_of(server, use_async, on_progress=pause)
    with pytest.raises(ResumableUploadPausedError):
        await run(upload)
    response = await run(upload)

    assert server.uploads["u0"] == DATA
    assert await run(upload) is response
    assert server.methods == ["POST", "PATCH", "HEAD", "PATCH", "PATCH"]


@use_async
async def test_cancel_deletes_the_upload(server: TusServer, use_async: bool) -> None:
    store: dict[str, str] = {}

    def pause(moved: int, total: int | None) -> None:
        if moved == 4:
            upload.pause()

    upload = upload_of(server, use_async, store=store, on_progress=pause)
    with pytest.raises(ResumableUploadPausedError):
        await run(upload)
    await cancel(upload)

    assert server.methods[-1] == "DELETE"
    assert server.uploads == {}
    assert store == {}
    with pytest.raises(ResumableUploadCancelledError):
        await run(upload)


@use_async
async def test_cancel_before_run_sends_nothing(
    server: TusServer, use_async: bool
) -> None:
    upload = upload_of(server, use_async)
    await cancel(upload)

    assert server.requests == []


@pytest.mark.parametrize(
    ("status", "text", "code"),
    [
        (409, "The resource already exists", "Duplicate"),
        (413, "Payload too large", "EntityTooLarge"),
        (404, "Bucket not found", "NotFound"),
    ],
)
@use_async
async def test_raises_the_error_of_the_server(
    server: TusServer, use_async: bool, status: int, text: str, code: str
) -> None:
    server.fail[0] = Response(status, text=text)

    with pytest.raises(StorageApiError) as caught:
        await run(upload_of(server, use_async))

    assert caught.value.status_code == status
    assert caught.value.code == code
    assert caught.value.message == text
    assert server.methods == ["POST"]


@use_async
async def test_parses_a_json_error(server: TusServer, use_async: bool) -> None:
    server.fail[0] = Response(
        400,
        json={
            "statusCode": "403",
            "code": "AccessDenied",
            "error": "x",
            "message": "no",
        },
    )

    with pytest.raises(StorageApiError) as caught:
        await run(upload_of(server, use_async))

    assert caught.value.code == "AccessDenied"


@use_async
async def test_keeps_an_upload_that_failed_with_an_error_it_can_recover_from(
    server: TusServer, use_async: bool
) -> None:
    server.fail[1] = Response(403, text="Forbidden")
    store: dict[str, str] = {}

    upload = upload_of(server, use_async, store=store)
    with pytest.raises(StorageApiError):
        await run(upload)
    await run(upload)

    assert server.methods == ["POST", "PATCH", "HEAD", "PATCH", "PATCH", "PATCH"]
    assert server.uploads["u0"] == DATA
    assert store == {}


@use_async
async def test_forgets_an_upload_that_cannot_complete(
    server: TusServer, use_async: bool
) -> None:
    server.fail[3] = Response(409, text="The resource already exists")
    store: dict[str, str] = {}

    with pytest.raises(StorageApiError) as caught:
        await run(upload_of(server, use_async, store=store))

    assert caught.value.code == "Duplicate"
    assert server.methods == ["POST", "PATCH", "PATCH", "PATCH"]
    assert store == {}


@use_async
async def test_completes_when_the_response_of_the_last_chunk_is_lost(
    use_async: bool,
) -> None:
    class LosingServer(TusServer):
        @override
        def __call__(self, request: Request) -> Response:
            response = super().__call__(request)
            if request.method == "PATCH" and "Tus-Complete" in response.headers:
                raise httpx.ReadError("connection dropped")
            return response

    losing = LosingServer()
    response = await run(upload_of(losing, use_async))

    assert response.id == "object-u0"
    assert losing.methods == ["POST", "PATCH", "PATCH", "PATCH", "HEAD"]


@use_async
async def test_keeps_the_upload_when_the_last_chunk_is_not_confirmed(
    server: TusServer, use_async: bool
) -> None:
    server.fail[3] = Response(204, headers={"Upload-Offset": "10"})
    store: dict[str, str] = {}

    upload = upload_of(server, use_async, store=store)
    with pytest.raises(StorageException, match="did not confirm"):
        await run(upload)

    assert upload.url == f"{UPLOADS}/u0"
    assert store == {upload.fingerprint: f"{UPLOADS}/u0"}


def test_cancel_while_creating_deletes_the_new_upload() -> None:
    store: dict[str, str] = {}

    class CancellingServer(TusServer):
        @override
        def __call__(self, request: Request) -> Response:
            if request.method == "POST":
                upload.cancel()
            return super().__call__(request)

    cancelling = CancellingServer()
    upload = (
        cancelling.sync_client()
        .from_("videos")
        .resumable_upload("clip.bin", DATA, chunk_size=4, store=store)
    )
    with pytest.raises(ResumableUploadCancelledError):
        upload.run()

    assert cancelling.methods == ["POST", "DELETE"]
    assert cancelling.uploads == {}
    assert store == {}


def test_keeps_the_new_upload_when_the_delete_after_a_cancel_fails() -> None:
    store: dict[str, str] = {}

    class CancellingServer(TusServer):
        @override
        def __call__(self, request: Request) -> Response:
            if request.method == "POST":
                upload.cancel()
            return super().__call__(request)

    cancelling = CancellingServer()
    cancelling.fail[1] = Response(503, text="Service Unavailable")
    upload = (
        cancelling.sync_client()
        .from_("videos")
        .resumable_upload("clip.bin", DATA, chunk_size=4, store=store)
    )
    with pytest.raises(StorageApiError):
        upload.run()
    assert upload.url == f"{UPLOADS}/u0"

    upload.cancel()

    assert cancelling.methods == ["POST", "DELETE", "DELETE"]
    assert cancelling.uploads == {}
    assert store == {}


@use_async
async def test_does_not_resend_the_creating_post_after_a_network_error(
    server: TusServer, use_async: bool
) -> None:
    server.fail[0] = httpx.ConnectError("connection dropped")

    with pytest.raises(SupabaseTransportError):
        await run(upload_of(server, use_async))

    assert server.methods == ["POST"]


@use_async
async def test_pause_before_run_stops_it_before_sending(
    server: TusServer, use_async: bool
) -> None:
    upload = upload_of(server, use_async)
    upload.pause()

    with pytest.raises(ResumableUploadPausedError):
        await run(upload)
    await run(upload)

    assert server.methods == ["POST", "PATCH", "PATCH", "PATCH"]


@pytest.mark.parametrize("status", [522, 524])
@use_async
async def test_raises_an_api_error_for_a_status_python_does_not_name(
    server: TusServer, use_async: bool, status: int
) -> None:
    for index in range(10):
        server.fail[index] = Response(status)

    with pytest.raises(StorageApiError) as caught:
        await run(upload_of(server, use_async))

    assert caught.value.status_code == status
    assert caught.value.message == f"HTTP {status}"


def test_the_fingerprint_tells_files_and_objects_apart(
    server: TusServer, tmp_path: Path
) -> None:
    path = tmp_path / "clip.bin"
    path.write_bytes(DATA)
    bucket = server.sync_client().from_("videos")

    def fingerprint(
        file: ResumableUploadSource, object_path: str = "clip.bin"
    ) -> str | None:
        return bucket.resumable_upload(object_path, file).fingerprint

    assert fingerprint(DATA) == fingerprint(DATA)
    assert fingerprint(DATA) != fingerprint(DATA[::-1])
    assert fingerprint(DATA) != fingerprint(DATA, "other.bin")
    assert fingerprint(path) == fingerprint(str(path))
    with path.open("rb") as file:
        assert fingerprint(file) == fingerprint(path)


def test_rejects_a_source_that_cannot_seek(server: TusServer) -> None:
    bucket = server.sync_client().from_("videos")
    with pytest.raises(TypeError):
        bucket.resumable_upload("clip.bin", stdlib_io.BufferedReader(Unseekable()))


def test_rejects_a_chunk_size_that_is_not_positive(server: TusServer) -> None:
    bucket = server.sync_client().from_("videos")
    with pytest.raises(ValueError, match="chunk_size"):
        bucket.resumable_upload("clip.bin", DATA, chunk_size=0)


def test_rejects_a_path_with_dot_segments(server: TusServer) -> None:
    bucket = server.sync_client().from_("videos")
    with pytest.raises(ValueError, match="dot segments"):
        bucket.resumable_upload("../clip.bin", DATA)


@use_async
async def test_refuses_a_location_on_another_origin(
    server: TusServer, use_async: bool
) -> None:
    server.fail[0] = Response(
        201, headers={"Location": "https://attacker.example/upload/u0"}
    )

    with pytest.raises(StorageException, match="another origin"):
        await run(upload_of(server, use_async))

    assert server.methods == ["POST"]


@use_async
async def test_ignores_a_stored_url_on_another_origin(
    server: TusServer, use_async: bool
) -> None:
    fingerprint = upload_of(server, use_async).fingerprint
    assert fingerprint is not None
    store = {fingerprint: "https://attacker.example/upload/u0"}

    await run(upload_of(server, use_async, store=store))

    assert server.methods[0] == "POST"
    assert all(request.url.host == "example.supabase.co" for request in server.requests)


def test_the_fingerprint_tells_options_apart(server: TusServer) -> None:
    bucket = server.sync_client().from_("videos")

    def fingerprint(**options: Any) -> str | None:
        return bucket.resumable_upload("clip.bin", DATA, **options).fingerprint

    assert fingerprint() != fingerprint(content_type="video/mp4")
    assert fingerprint() != fingerprint(cache_control="60")
    assert fingerprint() != fingerprint(upsert=True)
    assert fingerprint() != fingerprint(metadata={"source": "test"})


def test_the_fingerprint_follows_the_open_file_when_its_path_is_replaced(
    server: TusServer, tmp_path: Path
) -> None:
    path = tmp_path / "clip.bin"
    path.write_bytes(DATA)
    bucket = server.sync_client().from_("videos")
    with path.open("rb") as old:
        replacement = tmp_path / "replacement.bin"
        replacement.write_bytes(DATA[::-1])
        replacement.replace(path)

        assert (
            bucket.resumable_upload("clip.bin", old).fingerprint
            != bucket.resumable_upload("clip.bin", path).fingerprint
        )


@use_async
async def test_does_not_resend_the_creating_post_after_an_error_status(
    server: TusServer, use_async: bool
) -> None:
    server.fail[0] = Response(503, text="Service Unavailable")

    with pytest.raises(StorageApiError):
        await run(upload_of(server, use_async))

    assert server.methods == ["POST"]


@use_async
async def test_refuses_to_continue_with_a_file_that_was_replaced(
    server: TusServer, use_async: bool, tmp_path: Path
) -> None:
    path = tmp_path / "clip.bin"
    path.write_bytes(DATA)

    def pause(moved: int, total: int | None) -> None:
        if moved == 4:
            upload.pause()

    upload = upload_of(server, use_async, path, on_progress=pause)
    with pytest.raises(ResumableUploadPausedError):
        await run(upload)
    replacement = tmp_path / "replacement.bin"
    replacement.write_bytes(DATA[::-1])
    replacement.replace(path)

    with pytest.raises(StorageException, match="changed"):
        await run(upload)

    assert server.methods == ["POST", "PATCH"]
    assert server.uploads["u0"] == DATA[:4]


@use_async
async def test_refuses_a_file_that_changed_before_the_first_run(
    server: TusServer, use_async: bool, tmp_path: Path
) -> None:
    path = tmp_path / "clip.bin"
    path.write_bytes(DATA[:4])
    upload = upload_of(server, use_async, path)
    replacement = tmp_path / "replacement.bin"
    replacement.write_bytes(DATA)
    replacement.replace(path)

    with pytest.raises(StorageException, match="changed"):
        await run(upload)

    assert server.requests == []


@use_async
async def test_a_paused_upload_continues_with_the_headers_the_client_has_now(
    server: TusServer, use_async: bool
) -> None:
    def pause(moved: int, total: int | None) -> None:
        if moved == 4 and len(server.requests) == 2:
            upload.pause()

    client = server.async_client() if use_async else server.sync_client()
    bucket = client.from_("videos")
    upload = bucket.resumable_upload("clip.bin", DATA, chunk_size=4, on_progress=pause)
    with pytest.raises(ResumableUploadPausedError):
        await run(upload)
    client.default_headers = client.default_headers.override(
        "Authorization", "Bearer refreshed"
    )

    await run(upload)

    assert [request.headers["Authorization"] for request in server.requests] == [
        "Bearer key",
        "Bearer key",
        "Bearer refreshed",
        "Bearer refreshed",
        "Bearer refreshed",
    ]
