from __future__ import annotations

import threading
from collections.abc import AsyncIterable, Callable
from io import BytesIO
from typing import TYPE_CHECKING, BinaryIO, override

from supabase_utils.http.body import FileContent

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Iterable, Iterator

    from supabase_utils.http.body import RequestContent
    from supabase_utils.http.headers import Headers

__all__ = ["ProgressCallback"]

type ProgressCallback = Callable[[int, int | None], None]
"""Called while an upload or a download runs with the bytes moved so far and
the total bytes, or None when the total is not known.

It is called after every chunk, from any thread. The bytes moved restart from
0 when an upload is sent again, for a retry or a redirect. No call says that
the transfer is complete: the operation returning or the body ending does.
"""


class _Progress:
    """Reports the bytes one transfer moved to a callback.

    Every pass over the body is an attempt that counts from 0. A report of an
    attempt that a later one replaced, or that comes after `end`, is dropped,
    so a worker thread still reading an abandoned attempt reports nothing.
    """

    def __init__(self, callback: ProgressCallback, total: int | None) -> None:
        self.callback = callback
        self.total = total
        self._lock = threading.Lock()
        self._attempt = 0
        self._ended = False

    def start(self) -> int:
        with self._lock:
            self._attempt += 1
            attempt = self._attempt
        self.report(attempt, 0)
        return attempt

    def report(self, attempt: int, moved: int) -> None:
        with self._lock:
            if not self._ended and attempt == self._attempt:
                self.callback(moved, self.total)

    def end(self) -> None:
        with self._lock:
            self._ended = True


def _counted(chunks: Iterable[bytes], progress: _Progress) -> Iterator[bytes]:
    attempt = progress.start()
    moved = 0
    for chunk in chunks:
        yield chunk
        moved += len(chunk)
        progress.report(attempt, moved)


async def _async_counted(
    chunks: AsyncIterable[bytes], progress: _Progress
) -> AsyncIterator[bytes]:
    attempt = progress.start()
    moved = 0
    async for chunk in chunks:
        yield chunk
        moved += len(chunk)
        progress.report(attempt, moved)


class _CountedFileContent(FileContent):
    """A `FileContent` that reports every pass over the file to `progress`,
    so it keeps its `Content-Length` and can still be retried."""

    def __init__(self, file: BinaryIO, progress: _Progress) -> None:
        super().__init__(file)
        self.progress = progress

    @override
    def __iter__(self) -> Iterator[bytes]:
        return _counted(super().__iter__(), self.progress)


def _counted_upload(
    content: RequestContent, callback: ProgressCallback
) -> tuple[RequestContent, _Progress]:
    """`content` with every chunk handed to the HTTP stack reported to
    `callback`, and the progress to end once the upload returned."""
    if isinstance(content, bytes):
        content = FileContent(BytesIO(content))
    if isinstance(content, FileContent):
        progress = _Progress(callback, content.length)
        return _CountedFileContent(content.file, progress), progress
    progress = _Progress(callback, None)
    if isinstance(content, AsyncIterable):
        return _async_counted(content, progress), progress
    return _counted(content, progress), progress


def _download_total(headers: Headers, content_length: int | None) -> int | None:
    """The `Content-Length` of a download, unless the HTTP stack decodes a
    `Content-Encoding`, which makes it count other bytes than the body."""
    encoding = headers.get("Content-Encoding")
    if encoding is not None and encoding.strip().lower() != "identity":
        return None
    return content_length
