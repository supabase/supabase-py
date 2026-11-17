import asyncio
import json
from types import TracebackType
from typing import Self

import pytest
from supabase_utils.http.errors import SupabaseTransportError
from supabase_utils.http.headers import Headers
from supabase_utils.http.request import Request, Response
from yarl import URL

from realtime import (
    ConnectionState,
    RealtimeAPIError,
    RealtimeChannelOptions,
    RealtimeClient,
    RealtimeError,
    RealtimeTimeoutError,
)

REALTIME_URL = "ws://127.0.0.1:54321/realtime/v1"


class FakeSession:
    def __init__(
        self,
        status: int = 202,
        content: bytes = b"",
        delay: float = 0,
        error: Exception | None = None,
    ) -> None:
        self.status = status
        self.content = content
        self.delay = delay
        self.error = error
        self.requests: list[Request] = []

    async def send(self, request: Request) -> Response:
        self.requests.append(request)
        await asyncio.sleep(self.delay)
        if self.error is not None:
            raise self.error
        return Response(
            headers=Headers.empty(),
            content=self.content,
            status=self.status,
            request=request,
        )

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        pass


async def get_token() -> str:
    return "user-token"


async def no_token() -> str | None:
    return None


async def test_posts_the_payload_without_subscribing() -> None:
    session = FakeSession()
    client = RealtimeClient(
        REALTIME_URL,
        get_token,
        http_session=session,
        headers={"apikey": "publishable-key"},
    )
    channel = client.channel("room/1")

    await channel.http_send("new message", {"text": "hi"})

    [request] = session.requests
    assert request.method == "POST"
    assert str(request.url) == (
        "http://127.0.0.1:54321/realtime/v1/api/broadcast/room%2F1/events/new%20message"
    )
    assert request.headers["apikey"] == "publishable-key"
    assert request.headers["Authorization"] == "Bearer user-token"
    assert request.headers["Content-Type"] == "application/json"
    assert "supabase-py/realtime" in request.headers["X-Client-Info"]
    assert request.content is not None
    assert json.loads(request.content) == {"text": "hi"}
    assert client.connection_state == ConnectionState.CLOSED
    assert not channel.joined


async def test_sends_bytes_as_octet_stream() -> None:
    session = FakeSession()
    client = RealtimeClient(REALTIME_URL, get_token, http_session=session)

    await client.channel("room").http_send("binary", bytearray(b"\x00\x01"))

    [request] = session.requests
    assert request.headers["Content-Type"] == "application/octet-stream"
    assert request.content == b"\x00\x01"


async def test_marks_a_private_channel_in_the_query() -> None:
    session = FakeSession()
    client = RealtimeClient(REALTIME_URL, get_token, http_session=session)
    channel = client.channel("room", RealtimeChannelOptions().private(True))

    await channel.http_send("event", {})

    [request] = session.requests
    assert request.url.query["private"] == "true"


async def test_sends_no_authorization_without_a_token() -> None:
    session = FakeSession()
    client = RealtimeClient(
        REALTIME_URL,
        no_token,
        http_session=session,
        headers={"apikey": "publishable-key"},
    )

    await client.channel("room").http_send("event", {})

    [request] = session.requests
    assert "Authorization" not in request.headers
    assert request.headers["apikey"] == "publishable-key"


async def test_sends_the_token_set_with_set_auth() -> None:
    session = FakeSession()
    client = RealtimeClient(REALTIME_URL, get_token, http_session=session)
    await client.set_auth("manual-token")

    await client.channel("room").http_send("event", {})

    [request] = session.requests
    assert request.headers["Authorization"] == "Bearer manual-token"


async def test_the_token_replaces_a_configured_authorization_header() -> None:
    session = FakeSession()
    client = RealtimeClient(
        REALTIME_URL,
        get_token,
        http_session=session,
        headers={"Authorization": "Bearer stale", "Content-Type": "text/plain"},
    )

    await client.channel("room").http_send("event", {})

    [request] = session.requests
    assert request.headers.get_list("Authorization") == ["Bearer user-token"]
    assert request.headers.get_list("Content-Type") == ["application/json"]


@pytest.mark.parametrize(
    ("content", "message"),
    [
        (b'{"error": "rate limited", "message": "other"}', "rate limited"),
        (b'{"message": "invalid payload"}', "invalid payload"),
        (b"not json", "the server answered the broadcast with status 429"),
    ],
)
async def test_raises_on_a_status_other_than_202(content: bytes, message: str) -> None:
    session = FakeSession(status=429, content=content)
    client = RealtimeClient(REALTIME_URL, get_token, http_session=session)

    with pytest.raises(RealtimeAPIError) as error:
        await client.channel("room").http_send("event", {})

    assert error.value.message == message
    assert error.value.status_code == 429
    assert error.value.response is not None


async def test_raises_a_timeout_error_after_the_timeout() -> None:
    session = FakeSession(delay=1)
    client = RealtimeClient(REALTIME_URL, get_token, http_session=session)

    with pytest.raises(RealtimeTimeoutError):
        await client.channel("room").http_send("event", {}, request_timeout=0.01)


async def test_uses_the_timeout_of_the_client_by_default() -> None:
    session = FakeSession(delay=1)
    client = RealtimeClient(REALTIME_URL, get_token, timeout=0.01, http_session=session)

    with pytest.raises(RealtimeTimeoutError) as error:
        await client.channel("room").http_send("event", {})

    assert error.value.timeout == 0.01


async def test_rejects_a_non_positive_timeout() -> None:
    client = RealtimeClient(REALTIME_URL, get_token, http_session=FakeSession())

    with pytest.raises(ValueError, match="positive"):
        await client.channel("room").http_send("event", {}, request_timeout=0)


async def test_does_not_retry_a_transport_error() -> None:
    session = FakeSession(error=SupabaseTransportError(_request()))
    client = RealtimeClient(REALTIME_URL, get_token, http_session=session)

    with pytest.raises(SupabaseTransportError):
        await client.channel("room").http_send("event", {})

    assert len(session.requests) == 1


async def test_raises_without_an_http_session() -> None:
    client = RealtimeClient(REALTIME_URL, get_token)

    with pytest.raises(RealtimeError, match="http_session"):
        await client.channel("room").http_send("event", {})


def _request() -> Request:
    return Request(
        url=URL("http://127.0.0.1"),
        method="POST",
        headers=Headers.empty(),
        content=None,
        delay=None,
    )
