from __future__ import annotations

import codecs
from email.message import Message
from typing import TYPE_CHECKING

from supabase_utils.http.sse import ServerSentEvent, ServerSentEventDecoder

if TYPE_CHECKING:
    from collections.abc import AsyncGenerator, AsyncIterator, Generator, Iterator

    from supabase_utils.http.headers import Headers
    from supabase_utils.http.request import AsyncStreamedResponse, StreamedResponse

__all__ = ["AsyncFunctionResponseStream", "FunctionResponseStream"]


def _charset(headers: Headers) -> str:
    message = Message()
    message["Content-Type"] = headers.get("Content-Type") or ""
    charset = message.get_content_charset()
    if charset is None:
        return "utf-8"
    try:
        return codecs.lookup(charset).name
    except LookupError:
        return "utf-8"


class FunctionResponseStream:
    """The response of a function whose body is read as it arrives, from
    `invoke_stream` of the sync client.

    Iterate over it to read the body chunk by chunk, or use `iter_text`,
    `iter_events` or `read`. The body can be read once. A failure while it is
    read raises a `SupabaseTransportError`.
    """

    def __init__(self, response: StreamedResponse) -> None:
        self.status = response.status
        """The HTTP status."""
        self.headers = response.headers
        """The response headers."""
        self._body = response.body

    def __iter__(self) -> Iterator[bytes]:
        return self._body

    def iter_text(self) -> Generator[str]:
        """The body as text, decoded with the charset of its `Content-Type`
        or UTF-8."""
        decoder = codecs.getincrementaldecoder(_charset(self.headers))("replace")
        for chunk in self:
            if text := decoder.decode(chunk):
                yield text
        if text := decoder.decode(b"", final=True):
            yield text

    def iter_events(self) -> Generator[ServerSentEvent]:
        """The server-sent events of a `text/event-stream` body."""
        decoder = codecs.getincrementaldecoder("utf-8-sig")("replace")
        events = ServerSentEventDecoder()
        for chunk in self:
            yield from events.feed(decoder.decode(chunk))
        yield from events.feed(decoder.decode(b"", final=True))

    def read(self) -> bytes:
        """Reads the rest of the body into memory."""
        return b"".join(self)


class AsyncFunctionResponseStream:
    """The response of a function whose body is read as it arrives, from
    `invoke_stream` of the async client.

    Iterate over it with `async for` to read the body chunk by chunk, or use
    `iter_text`, `iter_events` or `read`. The body can be read once. A failure
    while it is read raises a `SupabaseTransportError`.
    """

    def __init__(self, response: AsyncStreamedResponse) -> None:
        self.status = response.status
        """The HTTP status."""
        self.headers = response.headers
        """The response headers."""
        self._body = response.body

    def __aiter__(self) -> AsyncIterator[bytes]:
        return self._body

    async def iter_text(self) -> AsyncGenerator[str]:
        """The body as text, decoded with the charset of its `Content-Type`
        or UTF-8."""
        decoder = codecs.getincrementaldecoder(_charset(self.headers))("replace")
        async for chunk in self:
            if text := decoder.decode(chunk):
                yield text
        if text := decoder.decode(b"", final=True):
            yield text

    async def iter_events(self) -> AsyncGenerator[ServerSentEvent]:
        """The server-sent events of a `text/event-stream` body."""
        decoder = codecs.getincrementaldecoder("utf-8-sig")("replace")
        events = ServerSentEventDecoder()
        async for chunk in self:
            for event in events.feed(decoder.decode(chunk)):
                yield event
        for event in events.feed(decoder.decode(b"", final=True)):
            yield event

    async def read(self) -> bytes:
        """Reads the rest of the body into memory."""
        return b"".join([chunk async for chunk in self])
