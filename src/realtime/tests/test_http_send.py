from typing import Any, Optional
from unittest.mock import patch

import httpx
import pytest

from realtime import AsyncRealtimeClient

URL = "http://127.0.0.1:54321/realtime/v1"
KEY = "anon-key"


def make_client(token: Optional[str] = KEY, **kwargs: Any) -> AsyncRealtimeClient:
    return AsyncRealtimeClient(URL, token, **kwargs)


def response(
    status: int, body: Any = None, reason: Optional[str] = None
) -> httpx.Response:
    return httpx.Response(
        status, json=body, extensions={"reason_phrase": (reason or "").encode()}
    )


def mock_post(resp: httpx.Response) -> Any:
    async def _post(self: Any, url: str, **kwargs: Any) -> httpx.Response:
        resp.request = httpx.Request("POST", url)
        return resp

    return patch("httpx.AsyncClient.post", autospec=True, side_effect=_post)


@pytest.mark.asyncio
async def test_posts_to_per_event_endpoint_with_headers() -> None:
    channel = make_client().channel("room:1")
    with mock_post(response(202)) as post:
        result = await channel.http_send("my event", {"a": 1})

    assert result == {"success": True}
    args, kwargs = post.call_args
    assert args[1] == f"{URL}/api/broadcast/room%3A1/events/my%20event"
    assert kwargs["params"] is None
    assert kwargs["headers"] == {
        "apikey": KEY,
        "Authorization": f"Bearer {KEY}",
        "Content-Type": "application/json",
    }
    assert kwargs["content"] == '{"a": 1}'


@pytest.mark.asyncio
async def test_uses_updated_access_token_and_omits_missing_one() -> None:
    client = make_client()
    await client.set_auth("jwt")
    with mock_post(response(202)) as post:
        await client.channel("t").http_send("e", {})
    assert post.call_args.kwargs["headers"]["Authorization"] == "Bearer jwt"

    anonymous = make_client(token=None)
    with mock_post(response(202)) as post:
        await anonymous.channel("t").http_send("e", {})
    headers = post.call_args.kwargs["headers"]
    assert headers["apikey"] == ""
    assert "Authorization" not in headers


@pytest.mark.asyncio
async def test_private_channel_sets_query_param() -> None:
    channel = make_client().channel(
        "t", {"config": {"broadcast": None, "presence": None, "private": True}}
    )
    with mock_post(response(202)) as post:
        await channel.http_send("e", {})
    assert post.call_args.kwargs["params"] == {"private": "true"}


@pytest.mark.asyncio
async def test_binary_payload_sent_as_octet_stream() -> None:
    channel = make_client().channel("t")
    with mock_post(response(202)) as post:
        await channel.http_send("e", b"\x00\x01")
    kwargs = post.call_args.kwargs
    assert kwargs["content"] == b"\x00\x01"
    assert kwargs["headers"]["Content-Type"] == "application/octet-stream"


@pytest.mark.asyncio
async def test_does_not_require_subscription_or_connection() -> None:
    channel = make_client().channel("t")
    assert not channel._joined_once
    with mock_post(response(202)):
        assert await channel.http_send("e", {"x": 1}) == {"success": True}


@pytest.mark.asyncio
async def test_rejects_none_payload() -> None:
    with pytest.raises(ValueError, match="Payload is required for http_send"):
        await make_client().channel("t").http_send("e", None)


@pytest.mark.asyncio
@pytest.mark.parametrize("payload", [0, "", [], {}, False])
async def test_accepts_falsy_payloads(payload) -> None:
    with mock_post(response(202)):
        assert await make_client().channel("t").http_send("e", payload) == {
            "success": True
        }


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "body,expected",
    [({"error": "boom"}, "boom"), ({"message": "bad"}, "bad"), (None, "Teapot")],
)
async def test_error_message_from_body_or_reason(body, expected) -> None:
    channel = make_client().channel("t")
    with mock_post(response(418, body, "Teapot")):
        with pytest.raises(Exception, match=expected):
            await channel.http_send("e", {})


@pytest.mark.asyncio
async def test_404_mentions_server_version() -> None:
    channel = make_client().channel("t")
    with mock_post(response(404, {"message": "Not Found"})):
        with pytest.raises(Exception, match=r"v2\.97\.0"):
            await channel.http_send("e", {})


@pytest.mark.asyncio
async def test_timeout_error() -> None:
    channel = make_client().channel("t")
    with patch("httpx.AsyncClient.post", side_effect=httpx.ReadTimeout("slow")):
        with pytest.raises(Exception, match="Request timeout"):
            await channel.http_send("e", {})


@pytest.mark.asyncio
async def test_timeout_defaults_to_client_timeout_and_can_be_overridden() -> None:
    channel = make_client(timeout=5).channel("t")
    timeouts = []
    real_init = httpx.AsyncClient.__init__

    def spy_init(self, *args, **kwargs) -> None:
        timeouts.append(kwargs["timeout"])
        real_init(self, *args, **kwargs)

    with mock_post(response(202)):
        with patch.object(httpx.AsyncClient, "__init__", spy_init):
            await channel.http_send("e", {})
            await channel.http_send("e", {}, timeout=3)
    assert timeouts == [5, 3]
