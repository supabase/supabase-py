import asyncio
import threading
from collections.abc import AsyncIterable, AsyncIterator, Iterable, Iterator
from io import SEEK_END
from typing import BinaryIO

CHUNK_SIZE = 64 * 1024
"""The number of bytes read from a file at a time when it is streamed."""


class FileContent:
    """A request body read from a binary file in chunks, from the position the
    file is at when this is created.

    Every iteration starts again from that position when the file is seekable,
    so a retry sends the whole body again. A file that is not seekable is read
    once.
    """

    def __init__(self, file: BinaryIO) -> None:
        self.file = file
        self.start: int | None = file.tell() if file.seekable() else None
        self._lock = threading.Lock()

    @property
    def replayable(self) -> bool:
        return self.start is not None

    @property
    def length(self) -> int | None:
        """The number of bytes left to send, or None when it is not known."""
        if self.start is None:
            return None
        with self._lock:
            end = self.file.seek(0, SEEK_END)
            self.file.seek(self.start)
        return end - self.start

    def __iter__(self) -> Iterator[bytes]:
        if self.start is None:
            while chunk := self.file.read(CHUNK_SIZE):
                yield chunk
            return
        position = self.start
        while True:
            # A retry can iterate while a worker thread of the abandoned
            # attempt still reads, so every read seeks to its own position.
            with self._lock:
                self.file.seek(position)
                chunk = self.file.read(CHUNK_SIZE)
            if not chunk:
                return
            position += len(chunk)
            yield chunk


type RequestContent = bytes | Iterable[bytes] | AsyncIterable[bytes]
"""A request body: the bytes to send, or an iterator over them that is sent
as it is read. The sync executor sends only `bytes` and sync iterables."""


async def async_chunks(
    content: Iterable[bytes] | AsyncIterable[bytes],
) -> AsyncIterator[bytes]:
    """Iterates over `content` without blocking the event loop: a sync
    iterable, such as a `FileContent`, is read in a worker thread."""
    if isinstance(content, AsyncIterable):
        async for chunk in content:
            yield chunk
        return
    iterator = iter(content)
    while (chunk := await asyncio.to_thread(next, iterator, None)) is not None:
        yield chunk
