from __future__ import annotations

import asyncio
import hashlib
import os
import stat
import threading
from base64 import b64encode
from collections.abc import Iterator
from contextlib import contextmanager
from dataclasses import dataclass, replace
from functools import cached_property
from http import HTTPStatus
from io import SEEK_END, BytesIO
from typing import TYPE_CHECKING, Any, BinaryIO, cast

from supabase_utils.http.body import CHUNK_SIZE
from supabase_utils.http.errors import SupabaseTransportError
from supabase_utils.http.headers import Headers
from supabase_utils.http.io import AsyncHttpIO, SyncHttpIO
from supabase_utils.http.request import Request
from supabase_utils.types import HTTPRequestMethod, JSONParser
from yarl import URL

from .exceptions import (
    ResumableUploadCancelledError,
    ResumableUploadPausedError,
    StorageApiError,
    StorageException,
    parse_api_error,
)
from .types import UploadResponse

if TYPE_CHECKING:
    from collections.abc import Generator, MutableMapping

    from supabase_utils.http.io import HttpMethod
    from supabase_utils.http.request import Response
    from supabase_utils.http.retry import RetryPolicy

    from .progress import ProgressCallback

__all__ = [
    "DEFAULT_CHUNK_SIZE",
    "AsyncResumableUpload",
    "BaseResumableUpload",
    "ResumableUpload",
    "ResumableUploadSource",
]

DEFAULT_CHUNK_SIZE = 6 * 1024 * 1024
"""The bytes a resumable upload sends per request, 6 MiB. Hosted Supabase
only accepts this size."""

type ResumableUploadSource = bytes | str | os.PathLike[str] | BinaryIO
"""What a resumable upload sends: the bytes themselves, the path of a file,
or a binary file opened for reading that can seek. A file is read from disk
one chunk at a time."""

_TUS_VERSION = "1.0.0"


@dataclass(frozen=True)
class _TusRequest:
    """A request to the tus endpoint. The upload URL is absolute, as the
    server returned it, so it is not joined to the base URL."""

    url: URL
    method: HTTPRequestMethod
    headers: Headers
    body: bytes | Iterator[bytes] | None = None
    delay: float | None = None

    def finalize(self, base_url: URL, default_headers: Headers) -> Request:
        return Request(
            url=self.url,
            method=self.method,
            headers=default_headers.update(self.headers).override(
                "Tus-Resumable", _TUS_VERSION
            ),
            content=self.body,
            delay=self.delay,
            retry=False,
        )


def _once(request: _TusRequest) -> HttpMethod[Response]:
    return (yield request)


def _encode(value: str) -> str:
    return b64encode(value.encode("utf-8")).decode("ascii")


_FINAL_CODES = frozenset({"Duplicate", "EntityTooLarge"})
"""The codes of errors after which the upload can never complete."""


def _status_phrase(status: int) -> str | None:
    try:
        return HTTPStatus(status).phrase
    except ValueError:
        return None


def _error_code(response: Response, message: str) -> str:
    if response.status == HTTPStatus.CONFLICT and "already exists" in message:
        return "Duplicate"
    if response.status == HTTPStatus.REQUEST_ENTITY_TOO_LARGE:
        return "EntityTooLarge"
    phrase = _status_phrase(response.status)
    return "InternalError" if phrase is None else "".join(phrase.split())


def _tus_error(response: Response) -> StorageApiError:
    """The error of a tus response. The tus routes answer in plain text, so
    the code is derived from the status when the body is not JSON."""
    content_type = response.headers.get("Content-Type") or ""
    if content_type.startswith("application/json"):
        return parse_api_error(response)
    message = response.content.decode("utf-8", errors="replace").strip()
    message = message or _status_phrase(response.status) or f"HTTP {response.status}"
    return StorageApiError(
        message,
        status_code=response.status,
        code=_error_code(response, message),
        response=response,
    )


def _upload_offset(response: Response) -> int:
    value = response.headers.get("Upload-Offset")
    if value is None or not value.isdecimal():
        raise StorageException("Storage answered a resumable upload without an offset")
    return int(value)


def _open(source: ResumableUploadSource) -> tuple[BinaryIO, bool]:
    """The file to read `source` from, and whether the upload opened it and
    so closes it."""
    if isinstance(source, bytes):
        return BytesIO(source), False
    if isinstance(source, (str, os.PathLike)):
        return open(source, "rb"), True
    return source, False


def _measure(source: ResumableUploadSource) -> tuple[int, int]:
    """The position the upload starts at in `source` and the bytes it sends."""
    if isinstance(source, bytes):
        return 0, len(source)
    if isinstance(source, (str, os.PathLike)):
        return 0, os.stat(source).st_size
    if not (hasattr(source, "seekable") and source.seekable()):
        raise TypeError(
            "A resumable upload needs bytes, a path or a binary file that can seek"
        )
    start = source.tell()
    end = source.seek(0, SEEK_END)
    source.seek(start)
    return start, end - start


def _identity(source: ResumableUploadSource) -> str | None:
    """What tells `source` apart from another one of the same size, or None
    when nothing does without reading it."""
    if isinstance(source, bytes):
        return hashlib.sha256(source).hexdigest()
    if isinstance(source, (str, os.PathLike)):
        status = os.stat(source)
    else:
        try:
            status = os.fstat(source.fileno())
        except (AttributeError, OSError, ValueError):
            return None
    if not stat.S_ISREG(status.st_mode):
        return None
    return f"{status.st_dev}:{status.st_ino}:{status.st_mtime_ns}"


class BaseResumableUpload[HttpIO: (SyncHttpIO, AsyncHttpIO)]:
    """What `ResumableUpload` and `AsyncResumableUpload` share."""

    def __init__(
        self,
        *,
        executor: HttpIO,
        base_url: URL,
        default_headers: Headers,
        bucket_id: str,
        path: str,
        source: ResumableUploadSource,
        content_type: str,
        cache_control: str,
        upsert: bool,
        metadata: dict[str, Any] | None,
        headers: dict[str, str] | None,
        chunk_size: int,
        store: MutableMapping[str, str] | None,
        on_progress: ProgressCallback | None,
    ) -> None:
        if chunk_size <= 0:
            raise ValueError(f"chunk_size must be positive, not {chunk_size!r}")
        self.bucket_id = bucket_id
        """The bucket the object goes to."""
        self.path = path
        """The path of the object in the bucket."""
        self._start, self.size = _measure(source)
        """The bytes the upload sends."""
        self._source = source
        self._file_identity = None if isinstance(source, bytes) else _identity(source)
        self._executor = executor
        self._base_url = base_url
        self._default_headers = default_headers
        self._content_type = content_type
        self._cache_control = cache_control
        self._upsert = upsert
        self._metadata = None if metadata is None else JSONParser.dump_json(metadata)
        self._headers = Headers.from_mapping(headers or {})
        self._chunk_size = chunk_size
        self._store = store
        self._on_progress = on_progress
        self._url: str | None = None
        self._offset = 0
        self._response: UploadResponse | None = None
        self._paused = False
        self._cancelled = False
        self._lock = threading.Lock()
        self._read_lock = threading.Lock()
        self._running = False
        self._attempt = 0

    @cached_property
    def fingerprint(self) -> str | None:
        """The key the upload URL is kept under in the store: the same file
        uploaded to the same object with the same options has the same
        fingerprint. None when the
        file cannot be told apart from another one, like a file object
        without a path, which the store then does not keep."""
        identity = (
            hashlib.sha256(self._source).hexdigest()
            if isinstance(self._source, bytes)
            else self._file_identity
        )
        if identity is None:
            return None
        parts = (
            str(self._base_url),
            self.bucket_id,
            self.path,
            str(self.size),
            identity,
            self._content_type,
            self._cache_control,
            str(self._upsert),
            (self._metadata or b"").decode(),
        )
        return hashlib.sha256("\0".join(parts).encode()).hexdigest()

    @property
    def url(self) -> str | None:
        """The URL of the upload on the server, or None until it is created."""
        return self._url

    @property
    def offset(self) -> int:
        """The bytes the server confirmed it holds."""
        return self._offset

    def pause(self) -> None:
        """Stops `run` once the chunk in flight is sent, making it raise
        `ResumableUploadPausedError`, or makes the next `run` raise it before
        sending anything. Calling `run` again continues from the offset the
        server confirmed.

        It can be called from the `on_progress` callback or from another
        thread or task than the one running the upload."""
        self._paused = True

    @contextmanager
    def _running_state(self) -> Generator[None]:
        with self._lock:
            if self._running:
                raise RuntimeError("The resumable upload is already running")
            self._running = True
        try:
            yield
        finally:
            with self._lock:
                self._attempt += 1
                self._running = False

    def _retire(self) -> None:
        """Ends the reads of the current run before its file is closed."""
        with self._lock:
            self._attempt += 1

    def _open(self) -> tuple[BinaryIO, bool]:
        """Opens the source, refusing a file that changed since the upload
        was prepared, since its bytes would be appended to those of the old
        one on the server."""
        file, owned = _open(self._source)
        if self._file_identity is not None and _identity(file) != self._file_identity:
            if owned:
                file.close()
            raise StorageException(
                "The file of the resumable upload changed since the upload was "
                "prepared. Cancel it and start a new one."
            )
        return file, owned

    def _stored_url(self) -> str | None:
        if self._url is None and self._store is not None and self.fingerprint:
            url = self._store.get(self.fingerprint)
            if url is not None and self._is_trusted(URL(url)):
                self._url = url
        return self._url

    def _is_trusted(self, url: URL) -> bool:
        """Whether `url` is on the storage server, so the credentials of the
        client can be sent to it."""
        return url.is_absolute() and url.origin() == self._base_url.origin()

    def _forget(self) -> None:
        self._url = None
        if self._store is not None and self.fingerprint:
            self._store.pop(self.fingerprint, None)

    def _report(self, moved: int) -> None:
        if self._on_progress is not None:
            self._on_progress(moved, self.size)

    def _raise_if_stopped(self) -> None:
        if self._cancelled:
            raise ResumableUploadCancelledError("The resumable upload was cancelled")
        if self._paused:
            self._paused = False
            raise ResumableUploadPausedError("The resumable upload was paused")

    def _request_headers(self) -> Headers:
        headers = self._headers
        if self._upsert:
            headers = headers.override("x-upsert", "true")
        return headers

    def _create_request(self) -> _TusRequest:
        metadata = [
            f"bucketName {_encode(self.bucket_id)}",
            f"objectName {_encode(self.path)}",
            f"contentType {_encode(self._content_type)}",
            f"cacheControl {_encode(self._cache_control)}",
        ]
        if self._metadata is not None:
            metadata.append(f"metadata {b64encode(self._metadata).decode('ascii')}")
        return _TusRequest(
            url=self._base_url.joinpath("upload", "resumable"),
            method="POST",
            headers=self._request_headers()
            .override("Upload-Length", str(self.size))
            .override("Upload-Metadata", ",".join(metadata)),
        )

    def _chunk(
        self, file: BinaryIO, start: int, end: int, attempt: int
    ) -> Iterator[bytes]:
        """Reads the bytes from `start` to `end` for the run `attempt`. The
        async client reads it in a worker thread, which can outlive that run,
        so a read of a run that ended reads and reports nothing. The read lock
        is never taken by the event loop, so a slow read cannot block it."""
        position = start
        while position < end:
            with self._read_lock:
                if attempt != self._attempt:
                    return
                try:
                    file.seek(self._start + position)
                    data = file.read(min(CHUNK_SIZE, end - position))
                except ValueError:
                    if attempt != self._attempt:
                        return
                    raise
            if not data:
                raise StorageException("The file of the resumable upload got shorter")
            yield data
            position += len(data)
            if attempt == self._attempt:
                self._report(position)

    def _patch_request(self, url: str, file: BinaryIO, offset: int) -> _TusRequest:
        end = min(offset + self._chunk_size, self.size)
        return _TusRequest(
            url=URL(url),
            method="PATCH",
            headers=self._request_headers()
            .override("Upload-Offset", str(offset))
            .override("Content-Type", "application/offset+octet-stream")
            .override("Content-Length", str(end - offset)),
            body=self._chunk(file, offset, end, self._attempt),
        )

    def _delete_request(self, url: str) -> _TusRequest:
        return _TusRequest(url=URL(url), method="DELETE", headers=self._headers)

    def _complete(self, response: Response) -> UploadResponse:
        self._forget()
        self._offset = self.size
        self._report(self.size)
        self._response = UploadResponse(
            id=response.headers.get("supabase-object-id"),
            path=self.path,
            full_path=f"{self.bucket_id}/{self.path}",
            version=response.headers.get("supabase-object-version-id"),
        )
        return self._response

    def _retry_delay(
        self,
        outcome: Response | SupabaseTransportError,
        retries: int,
        method: HTTPRequestMethod,
    ) -> float | None:
        """Seconds to wait before trying again after `outcome`, or None when
        the upload fails with it. The creating POST is retried only when
        the `RetryPolicy` retries a POST, since a failed one may still have
        created an upload. A PATCH or a HEAD is safe to repeat, as
        the offset is read again before the next PATCH."""
        policy: RetryPolicy = self._executor.retry_policy
        if method == "POST" and "POST" not in policy.retryable_methods:
            return None
        if isinstance(outcome, SupabaseTransportError):
            return policy.delay(outcome, retries)
        if outcome.status == HTTPStatus.CONFLICT and method == "PATCH":
            if (
                retries >= policy.max_retries
                or _tus_error(outcome).code in _FINAL_CODES
            ):
                return None
            return policy.backoff(retries + 1)
        return policy.delay(outcome, retries)

    def _created(self, request: _TusRequest, response: Response) -> str:
        location = response.headers.get("Location")
        if location is None:
            raise StorageException(
                "Storage created the resumable upload without a location"
            )
        resolved = request.url.join(URL(location))
        if not self._is_trusted(resolved):
            raise StorageException(
                "Storage returned the location of the resumable upload on "
                "another origin"
            )
        url = str(resolved)
        self._url = url
        if self._store is not None and self.fingerprint:
            self._store[self.fingerprint] = url
        return url

    def _steps(
        self, file: BinaryIO
    ) -> Generator[_TusRequest, Response, UploadResponse]:
        """The requests of the upload, from where the server is to the end.
        A transport error of a request is thrown into the generator."""
        offset: int | None = None
        retries = 0
        restarted = False
        delay: float | None = None
        self._stored_url()
        while True:
            self._raise_if_stopped()
            if self._url is None:
                request = self._create_request()
            elif offset is None:
                request = _TusRequest(
                    url=URL(self._url), method="HEAD", headers=self._headers
                )
            else:
                request = self._patch_request(self._url, file, offset)
            try:
                response = yield replace(request, delay=delay)
            except SupabaseTransportError as error:
                delay = self._retry_delay(error, retries, request.method)
                if delay is None:
                    raise
                retries += 1
                offset = None
                continue
            delay = None
            if not response.is_success:
                if (
                    request.method != "POST"
                    and response.status in (HTTPStatus.NOT_FOUND, HTTPStatus.GONE)
                    and not restarted
                ):
                    restarted = True
                    self._forget()
                    offset = None
                    continue
                delay = self._retry_delay(response, retries, request.method)
                if delay is None:
                    error = _tus_error(response)
                    if error.code in _FINAL_CODES:
                        self._forget()
                    raise error
                retries += 1
                offset = None
                continue
            if response.headers.get("Tus-Complete") == "1":
                return self._complete(response)
            if request.method == "POST":
                url = self._created(request, response)
                if self._cancelled:
                    deleted = yield self._delete_request(url)
                    if not deleted.is_success and deleted.status not in (404, 410):
                        raise _tus_error(deleted)
                    self._forget()
                offset = 0
            else:
                offset = _upload_offset(response)
                if request.method == "PATCH":
                    retries = 0
                if offset >= self.size:
                    if response.headers.get("supabase-object-id") is not None:
                        return self._complete(response)
                    raise StorageException(
                        "Storage received every byte of the resumable upload "
                        "but did not confirm that it stored the object, which "
                        "it cannot when the policies let the user insert but "
                        "not select objects. Check whether the object exists."
                    )
            self._offset = offset
            self._report(offset)


def _drive_sync(
    executor: SyncHttpIO,
    base_url: URL,
    headers: Headers,
    steps: Generator[_TusRequest, Response, UploadResponse],
) -> UploadResponse:
    try:
        request = next(steps)
        while True:
            try:
                response = executor.communicate(base_url, headers, _once(request))
            except SupabaseTransportError as error:
                request = steps.throw(error)
            else:
                request = steps.send(response)
    except StopIteration as stop:
        return cast("UploadResponse", stop.value)
    finally:
        steps.close()


async def _drive_async(
    executor: AsyncHttpIO,
    base_url: URL,
    headers: Headers,
    steps: Generator[_TusRequest, Response, UploadResponse],
) -> UploadResponse:
    try:
        request = next(steps)
        while True:
            try:
                response = await executor.communicate(base_url, headers, _once(request))
            except SupabaseTransportError as error:
                request = steps.throw(error)
            else:
                request = steps.send(response)
    except StopIteration as stop:
        return cast("UploadResponse", stop.value)
    finally:
        steps.close()


class ResumableUpload(BaseResumableUpload[SyncHttpIO]):
    """An upload sent in chunks with the tus protocol, from
    `resumable_upload` of the sync client. It can be paused, continued, and
    cancelled, and continued by another process that uses the same store.

    ```python
    upload = client.from_("videos").resumable_upload("holiday.mp4", "holiday.mp4")
    response = upload.run()
    ```
    """

    def run(self) -> UploadResponse:
        """Sends the bytes the server does not hold yet and returns the stored
        object. Call it again after it was paused or failed to continue from
        the offset the server confirmed. After the upload completed it returns
        the same object without sending anything.

        A request that fails is retried as the `RetryPolicy` of the client
        retries a failed request, after reading the offset the server holds
        again. An upload the server no longer knows, because it expired,
        starts over.
        """
        if self._response is not None:
            return self._response
        with self._running_state():
            file, owned = self._open()
            try:
                return _drive_sync(
                    self._executor,
                    self._base_url,
                    self._default_headers,
                    self._steps(file),
                )
            finally:
                self._retire()
                if owned:
                    file.close()

    def cancel(self) -> None:
        """Stops the upload, deletes what the server holds of it, and removes
        it from the store. A `run` in progress raises
        `ResumableUploadCancelledError` once the chunk in flight is sent.
        Does nothing once the upload completed. A cancel that comes while the
        last chunk is in flight can be too late: the server then stores the
        object, and `run` returns it."""
        if self._response is not None:
            return
        self._cancelled = True
        url = self._stored_url()
        if url is not None:
            response = self._executor.communicate(
                self._base_url, self._default_headers, _once(self._delete_request(url))
            )
            if not response.is_success and response.status not in (404, 410):
                raise _tus_error(response)
        self._forget()


class AsyncResumableUpload(BaseResumableUpload[AsyncHttpIO]):
    """An upload sent in chunks with the tus protocol, from
    `resumable_upload` of the async client. It can be paused, continued, and
    cancelled, and continued by another process that uses the same store.

    ```python
    upload = client.from_("videos").resumable_upload("holiday.mp4", "holiday.mp4")
    response = await upload.run()
    ```

    Cancelling the task that runs it pauses it too.
    """

    async def run(self) -> UploadResponse:
        """Sends the bytes the server does not hold yet and returns the stored
        object. Call it again after it was paused or failed to continue from
        the offset the server confirmed. After the upload completed it returns
        the same object without sending anything.

        A request that fails is retried as the `RetryPolicy` of the client
        retries a failed request, after reading the offset the server holds
        again. An upload the server no longer knows, because it expired,
        starts over.
        """
        if self._response is not None:
            return self._response
        with self._running_state():
            file, owned = await asyncio.to_thread(self._open)
            try:
                return await _drive_async(
                    self._executor,
                    self._base_url,
                    self._default_headers,
                    self._steps(file),
                )
            finally:
                self._retire()
                if owned:
                    await asyncio.to_thread(file.close)

    async def cancel(self) -> None:
        """Stops the upload, deletes what the server holds of it, and removes
        it from the store. A `run` in progress raises
        `ResumableUploadCancelledError` once the chunk in flight is sent.
        Does nothing once the upload completed. A cancel that comes while the
        last chunk is in flight can be too late: the server then stores the
        object, and `run` returns it."""
        if self._response is not None:
            return
        self._cancelled = True
        url = self._stored_url()
        if url is not None:
            response = await self._executor.communicate(
                self._base_url, self._default_headers, _once(self._delete_request(url))
            )
            if not response.is_success and response.status not in (404, 410):
                raise _tus_error(response)
        self._forget()
