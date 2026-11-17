from collections.abc import AsyncIterator

from supabase_utils.http.headers import Headers
from supabase_utils.http.request import (
    AsyncStreamedResponse,
    Request,
    StreamedResponse,
)
from supabase_utils.http.sse import ServerSentEvent
from yarl import URL

from supabase_functions import AsyncFunctionResponseStream, FunctionResponseStream

REQUEST = Request(
    url=URL("https://example.com/functions/v1/chat"),
    method="POST",
    headers=Headers.empty(),
    content=None,
    delay=None,
)


def headers(content_type: str | None) -> Headers:
    if content_type is None:
        return Headers.empty()
    return Headers.empty().set("Content-Type", content_type)


def sync_stream(
    chunks: list[bytes], content_type: str | None = None
) -> FunctionResponseStream:
    return FunctionResponseStream(
        StreamedResponse(
            headers=headers(content_type),
            status=200,
            request=REQUEST,
            body=iter(chunks),
        )
    )


def async_stream(
    chunks: list[bytes], content_type: str | None = None
) -> AsyncFunctionResponseStream:
    async def body() -> AsyncIterator[bytes]:
        for chunk in chunks:
            yield chunk

    return AsyncFunctionResponseStream(
        AsyncStreamedResponse(
            headers=headers(content_type),
            status=200,
            request=REQUEST,
            body=body(),
        )
    )


def test_iterating_gives_the_chunks() -> None:
    assert list(sync_stream([b"a", b"b"])) == [b"a", b"b"]


async def test_async_iterating_gives_the_chunks() -> None:
    assert [chunk async for chunk in async_stream([b"a", b"b"])] == [b"a", b"b"]


def test_read_gives_the_rest_of_the_body() -> None:
    stream = sync_stream([b"a", b"b", b"c"])
    assert next(iter(stream)) == b"a"
    assert stream.read() == b"bc"


async def test_async_read() -> None:
    assert await async_stream([b"a", b"b"]).read() == b"ab"


def test_iter_text_decodes_characters_split_across_chunks() -> None:
    encoded = "héllo".encode()
    assert "".join(sync_stream([encoded[:2], encoded[2:]]).iter_text()) == "héllo"


def test_iter_text_uses_the_charset_of_the_content_type() -> None:
    stream = sync_stream(["é".encode("latin-1")], "text/plain; charset=latin-1")
    assert list(stream.iter_text()) == ["é"]


def test_iter_text_falls_back_to_utf8_for_an_unknown_charset() -> None:
    stream = sync_stream(["é".encode()], "text/plain; charset=nope")
    assert list(stream.iter_text()) == ["é"]


async def test_async_iter_text_decodes_characters_split_across_chunks() -> None:
    encoded = "héllo".encode()
    stream = async_stream([encoded[:2], encoded[2:]])
    assert "".join([text async for text in stream.iter_text()]) == "héllo"


def test_iter_events_strips_the_byte_order_mark() -> None:
    encoded = "﻿data: é\n\n".encode()
    stream = sync_stream([encoded[:2], encoded[2:6], encoded[6:]])
    assert list(stream.iter_events()) == [ServerSentEvent(data="é")]


async def test_async_iter_events() -> None:
    stream = async_stream([b"data: a\n", b"\ndata: b\n\n"])
    assert [event async for event in stream.iter_events()] == [
        ServerSentEvent(data="a"),
        ServerSentEvent(data="b"),
    ]
