from __future__ import annotations

import asyncio
import os
import secrets
import stat
from contextlib import asynccontextmanager, contextmanager, suppress
from pathlib import Path
from typing import TYPE_CHECKING, BinaryIO

from .exceptions import (
    StorageDownloadTooLargeError,
    StorageException,
    StorageRangeIgnoredError,
    parse_api_error,
)
from .progress import _async_downloaded, _downloaded

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, AsyncIterator, Generator, Iterator

    from supabase_utils.http.headers import Headers
    from supabase_utils.http.io import AsyncHttpIO, HttpMethod, SyncHttpIO
    from supabase_utils.http.request import (
        AsyncStreamedResponse,
        EmptyRequest,
        Response,
        StreamedResponse,
    )
    from yarl import URL

    from .progress import ProgressCallback

__all__ = ["AsyncStorageDownload", "StorageDownload"]


def _content_length(headers: Headers) -> int | None:
    value = headers.get("Content-Length")
    return int(value) if value is not None and value.isdecimal() else None


def _download_total(headers: Headers) -> int | None:
    """The `Content-Length` of a download, unless the HTTP stack decodes a
    `Content-Encoding`, which makes it count other bytes than the body."""
    encoding = headers.get("Content-Encoding")
    if encoding is not None and encoding.strip().lower() != "identity":
        return None
    return _content_length(headers)


class _DownloadHead:
    def __init__(self, status: int, headers: Headers) -> None:
        self.status = status
        """The HTTP status: 200, or 206 for a byte range."""
        self.headers = headers
        """The response headers."""

    @property
    def content_length(self) -> int | None:
        """The `Content-Length` of the body, or None when the server did not
        send one, as for a transformed image. For a body sent with a
        `Content-Encoding` it counts the encoded bytes, not the decoded bytes
        the download yields."""
        return _content_length(self.headers)

    @property
    def content_type(self) -> str | None:
        """The `Content-Type` of the body."""
        return self.headers.get("Content-Type")

    @property
    def etag(self) -> str | None:
        """The `ETag` of the file, quotes included, to pass as `if_match`
        when the download is resumed."""
        return self.headers.get("ETag")

    @property
    def _total(self) -> int | None:
        return _download_total(self.headers)


def _byte_range(offset: int, length: int | None) -> str | None:
    """The `Range` header for `length` bytes from `offset`, or None for the
    whole object."""
    if offset < 0:
        raise ValueError(f"offset must not be negative, got {offset}")
    if length is not None and length < 1:
        raise ValueError(f"length must be at least 1, got {length}")
    if length is not None:
        return f"bytes={offset}-{offset + length - 1}"
    return f"bytes={offset}-" if offset else None


def _range_start(headers: Headers) -> int:
    """The first byte of a partial body, from its `Content-Range` header.
    Rejects an encoded body, whose byte offsets are not those of the file."""
    encoding = headers.get("Content-Encoding")
    if encoding is not None and encoding.strip().lower() != "identity":
        raise StorageException(
            f"The partial download is encoded with {encoding}, so its byte"
            " offsets are not those of the file"
        )
    value = headers.get("Content-Range") or ""
    unit, _, positions = value.partition(" ")
    span, _, total = positions.partition("/")
    first, _, last = span.partition("-")
    if (
        unit.lower() == "bytes"
        and first.isdecimal()
        and last.isdecimal()
        and int(first) <= int(last)
        and (total == "*" or (total.isdecimal() and int(last) < int(total)))
    ):
        return int(first)
    raise StorageException(
        f"The partial download has an invalid Content-Range header: {value!r}"
    )


def _open_to_resume(destination: Path, start: int) -> BinaryIO:
    """Opens `destination` to append a body that starts at byte `start`."""
    size = destination.stat().st_size if destination.exists() else 0
    if start != size:
        raise StorageException(
            f"The download starts at byte {start}, but {destination} has {size} bytes"
        )
    return destination.open("ab")


def _check_size(size: int, max_bytes: int | None) -> None:
    if max_bytes is not None and size > max_bytes:
        raise StorageDownloadTooLargeError(max_bytes)


def _destination(path: str | os.PathLike[str]) -> Path:
    """The file `path` names, following a symlink so that the file it points
    to is replaced rather than the link."""
    return Path(path).resolve()


def _temporary_path(destination: Path) -> Path:
    return destination.with_name(f".{destination.name}.{secrets.token_hex(8)}.part")


def _umask() -> int:
    try:
        with open("/proc/self/status") as status:
            for line in status:
                if line.startswith("Umask:"):
                    return int(line.split()[1], 8)
    except OSError:
        pass
    umask = os.umask(0o077)
    os.umask(umask)
    return umask


def _open_new(path: Path, destination: Path) -> BinaryIO:
    """Creates `path` readable by its owner only, then gives it the mode of
    `destination`, or the default mode of a new file, before anything is
    written, so no one else can open it with more access than the result."""
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        if destination.exists():
            mode = stat.S_IMODE(destination.stat().st_mode)
        else:
            mode = 0o666 & ~_umask()
        if hasattr(os, "fchmod"):
            os.fchmod(descriptor, mode)
        else:
            os.chmod(path, mode)
    except BaseException:
        os.close(descriptor)
        raise
    return os.fdopen(descriptor, "wb")


class StorageDownload(_DownloadHead):
    """A download whose body is read as it arrives, from `download_stream` of
    the sync client.

    Iterate over it to read the body chunk by chunk, or use `read` or
    `write_to`. The body can be read once. A failure while it is read raises a
    `SupabaseTransportError`.
    """

    def __init__(
        self, response: StreamedResponse, on_progress: ProgressCallback | None = None
    ) -> None:
        super().__init__(response.status, response.headers)
        self._body = response.body
        if on_progress is not None:
            self._body = _downloaded(self._body, on_progress, self._total)

    def __iter__(self) -> Iterator[bytes]:
        return self._body

    def read(self, max_bytes: int | None = None) -> bytes:
        """Reads the whole body into memory.

        Raises `StorageDownloadTooLargeError` as soon as more than `max_bytes`
        bytes arrived, when it is given.
        """
        chunks: list[bytes] = []
        size = 0
        for chunk in self:
            size += len(chunk)
            _check_size(size, max_bytes)
            chunks.append(chunk)
        return b"".join(chunks)

    def write_to(self, path: str | os.PathLike[str], *, resume: bool = False) -> None:
        """Writes the body to the file at `path`, replacing it.

        The body goes to a temporary file in the same directory first, which
        replaces `path` once the whole body arrived. On a failure `path` is
        left as it was. The directory must exist. A file that existed keeps
        its permissions, and a symlink keeps pointing to the replaced file.

        With `resume`, a partial body (HTTP 206) is appended to `path`
        instead. `path` must hold exactly the bytes before the range, so start
        the download with the size of `path` as `offset`. A failure then
        leaves the bytes that arrived, and the next resume continues after
        them. A whole body (HTTP 200), as a server or cache that ignores the
        range sends, replaces `path` as it does without `resume`.
        """
        destination = _destination(path)
        if resume and self.status == 206:
            with _open_to_resume(destination, _range_start(self.headers)) as file:
                for chunk in self:
                    file.write(chunk)
            return
        temporary = _temporary_path(destination)
        try:
            with _open_new(temporary, destination) as file:
                for chunk in self:
                    file.write(chunk)
            temporary.replace(destination)
        except BaseException:
            with suppress(OSError):
                temporary.unlink(missing_ok=True)
            raise


class AsyncStorageDownload(_DownloadHead):
    """A download whose body is read as it arrives, from `download_stream` of
    the async client.

    Iterate over it with `async for` to read the body chunk by chunk, or use
    `read` or `write_to`. The body can be read once. A failure while it is
    read raises a `SupabaseTransportError`.
    """

    def __init__(
        self,
        response: AsyncStreamedResponse,
        on_progress: ProgressCallback | None = None,
    ) -> None:
        super().__init__(response.status, response.headers)
        self._body = response.body
        if on_progress is not None:
            self._body = _async_downloaded(self._body, on_progress, self._total)

    def __aiter__(self) -> AsyncIterator[bytes]:
        return self._body

    async def read(self, max_bytes: int | None = None) -> bytes:
        """Reads the whole body into memory.

        Raises `StorageDownloadTooLargeError` as soon as more than `max_bytes`
        bytes arrived, when it is given.
        """
        chunks: list[bytes] = []
        size = 0
        async for chunk in self:
            size += len(chunk)
            _check_size(size, max_bytes)
            chunks.append(chunk)
        return b"".join(chunks)

    async def write_to(
        self, path: str | os.PathLike[str], *, resume: bool = False
    ) -> None:
        """Writes the body to the file at `path`, replacing it.

        The body goes to a temporary file in the same directory first, which
        replaces `path` once the whole body arrived. On a failure or a
        cancellation `path` is left as it was. The directory must exist. A
        file that existed keeps its permissions, and a symlink keeps pointing
        to the replaced file. The body is written in worker threads, so it
        does not block the event loop.

        With `resume`, a partial body (HTTP 206) is appended to `path`
        instead. `path` must hold exactly the bytes before the range, so start
        the download with the size of `path` as `offset`. A failure or a
        cancellation then leaves the bytes that arrived, and the next resume
        continues after them. A whole body (HTTP 200), as a server or cache
        that ignores the range sends, replaces `path` as it does without
        `resume`.
        """
        destination = _destination(path)
        if resume and self.status == 206:
            file = await asyncio.to_thread(
                _open_to_resume, destination, _range_start(self.headers)
            )
            try:
                async for chunk in self:
                    await asyncio.to_thread(file.write, chunk)
            finally:
                await asyncio.to_thread(file.close)
            return
        temporary = _temporary_path(destination)
        try:
            file = _open_new(temporary, destination)
            try:
                async for chunk in self:
                    await asyncio.to_thread(file.write, chunk)
            finally:
                file.close()
            temporary.replace(destination)
        except BaseException:
            with suppress(OSError):
                temporary.unlink(missing_ok=True)
            raise


@contextmanager
def _sync_download(
    executor: SyncHttpIO,
    base_url: URL,
    headers: Headers,
    request: EmptyRequest,
    on_progress: ProgressCallback | None,
) -> Generator[StorageDownload]:
    with executor.stream(base_url, headers, request) as response:
        if not response.is_success:
            raise parse_api_error(response.read())
        yield StorageDownload(response, on_progress)


@asynccontextmanager
async def _async_download(
    executor: AsyncHttpIO,
    base_url: URL,
    headers: Headers,
    request: EmptyRequest,
    on_progress: ProgressCallback | None,
) -> AsyncGenerator[AsyncStorageDownload]:
    async with executor.stream(base_url, headers, request) as response:
        if not response.is_success:
            raise parse_api_error(await response.read())
        yield AsyncStorageDownload(response, on_progress)


def _content_of(response: Response) -> bytes:
    if not response.is_success:
        raise parse_api_error(response)
    return response.content


def _body_of(request: EmptyRequest) -> HttpMethod[bytes]:
    return _content_of((yield request))


def _check_range(status: int, headers: Headers, byte_range: str) -> None:
    if status != 206:
        raise StorageRangeIgnoredError(byte_range, status)
    requested = int(byte_range.removeprefix("bytes=").partition("-")[0])
    start = _range_start(headers)
    if start != requested:
        raise StorageException(
            f"The server answered the request for {byte_range} with a range"
            f" that starts at byte {start}"
        )


def _sync_read(
    executor: SyncHttpIO,
    base_url: URL,
    headers: Headers,
    request: EmptyRequest,
    byte_range: str | None,
    on_progress: ProgressCallback | None,
) -> bytes:
    """The body of a download, with every chunk of every attempt reported to
    `on_progress` when it is given. A download of `byte_range` that is
    answered with anything but the range raises once the head arrives,
    without reading the body."""
    if byte_range is None and on_progress is None:
        return executor.communicate(base_url, headers, _body_of(request))

    def observe(response: StreamedResponse) -> Iterator[bytes]:
        if byte_range is not None:
            _check_range(response.status, response.headers, byte_range)
        if on_progress is None:
            return response.body
        return _downloaded(
            response.body, on_progress, _download_total(response.headers)
        )

    return _content_of(executor.receive(base_url, headers, request, observe))


async def _async_read(
    executor: AsyncHttpIO,
    base_url: URL,
    headers: Headers,
    request: EmptyRequest,
    byte_range: str | None,
    on_progress: ProgressCallback | None,
) -> bytes:
    """The body of a download, with every chunk of every attempt reported to
    `on_progress` when it is given. A download of `byte_range` that is
    answered with anything but the range raises once the head arrives,
    without reading the body."""
    if byte_range is None and on_progress is None:
        return await executor.communicate(base_url, headers, _body_of(request))

    def observe(response: AsyncStreamedResponse) -> AsyncIterator[bytes]:
        if byte_range is not None:
            _check_range(response.status, response.headers, byte_range)
        if on_progress is None:
            return response.body
        return _async_downloaded(
            response.body, on_progress, _download_total(response.headers)
        )

    return _content_of(await executor.receive(base_url, headers, request, observe))
