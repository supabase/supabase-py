from __future__ import annotations

import asyncio
import os
import secrets
from contextlib import asynccontextmanager, contextmanager, suppress
from pathlib import Path
from typing import TYPE_CHECKING, BinaryIO

from .exceptions import StorageDownloadTooLargeError, parse_api_error

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, AsyncIterator, Generator, Iterator

    from supabase_utils.http.headers import Headers
    from supabase_utils.http.io import AsyncHttpIO, SyncHttpIO
    from supabase_utils.http.request import (
        AsyncStreamedResponse,
        EmptyRequest,
        StreamedResponse,
    )
    from yarl import URL

__all__ = ["AsyncStorageDownload", "StorageDownload"]


class _DownloadHead:
    def __init__(self, status: int, headers: Headers) -> None:
        self.status = status
        """The HTTP status: 200, or 206 for a byte range."""
        self.headers = headers
        """The response headers."""

    @property
    def content_length(self) -> int | None:
        """The `Content-Length` of the body, or None when the server did not
        send one, as for a transformed image."""
        value = self.headers.get("Content-Length")
        return int(value) if value is not None and value.isdecimal() else None

    @property
    def content_type(self) -> str | None:
        """The `Content-Type` of the body."""
        return self.headers.get("Content-Type")


def _check_size(size: int, max_bytes: int | None) -> None:
    if max_bytes is not None and size > max_bytes:
        raise StorageDownloadTooLargeError(max_bytes)


def _temporary_path(destination: Path) -> Path:
    return destination.with_name(f".{destination.name}.{secrets.token_hex(8)}.part")


def _open_new(path: Path) -> BinaryIO:
    descriptor = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o666)
    return os.fdopen(descriptor, "wb")


class StorageDownload(_DownloadHead):
    """A download whose body is read as it arrives, from `download_stream` of
    the sync client.

    Iterate over it to read the body chunk by chunk, or use `read` or
    `write_to`. The body can be read once. A failure while it is read raises a
    `SupabaseTransportError`.
    """

    def __init__(self, response: StreamedResponse) -> None:
        super().__init__(response.status, response.headers)
        self._body = response.body

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

    def write_to(self, path: str | os.PathLike[str]) -> None:
        """Writes the body to the file at `path`, replacing it.

        The body goes to a temporary file in the same directory first, which
        replaces `path` once the whole body arrived. On a failure `path` is
        left as it was. The directory must exist.
        """
        destination = Path(path)
        temporary = _temporary_path(destination)
        try:
            with _open_new(temporary) as file:
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

    def __init__(self, response: AsyncStreamedResponse) -> None:
        super().__init__(response.status, response.headers)
        self._body = response.body

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

    async def write_to(self, path: str | os.PathLike[str]) -> None:
        """Writes the body to the file at `path`, replacing it.

        The body goes to a temporary file in the same directory first, which
        replaces `path` once the whole body arrived. On a failure or a
        cancellation `path` is left as it was. The directory must exist.
        Writing the file runs in worker threads, so it does not block the
        event loop.
        """
        destination = Path(path)
        temporary = _temporary_path(destination)
        try:
            file = await asyncio.to_thread(_open_new, temporary)
            try:
                async for chunk in self:
                    await asyncio.to_thread(file.write, chunk)
            finally:
                file.close()
            await asyncio.to_thread(temporary.replace, destination)
        except BaseException:
            with suppress(OSError):
                temporary.unlink(missing_ok=True)
            raise


@contextmanager
def _sync_download(
    executor: SyncHttpIO, base_url: URL, headers: Headers, request: EmptyRequest
) -> Generator[StorageDownload]:
    with executor.stream(base_url, headers, request) as response:
        if not response.is_success:
            raise parse_api_error(response.read())
        yield StorageDownload(response)


@asynccontextmanager
async def _async_download(
    executor: AsyncHttpIO, base_url: URL, headers: Headers, request: EmptyRequest
) -> AsyncGenerator[AsyncStorageDownload]:
    async with executor.stream(base_url, headers, request) as response:
        if not response.is_success:
            raise parse_api_error(await response.read())
        yield AsyncStorageDownload(response)
