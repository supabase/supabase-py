import os
from unittest.mock import AsyncMock, patch

import httpx
import pytest
from dotenv import load_dotenv

from realtime import AsyncRealtimeChannel, AsyncRealtimeClient

load_dotenv()

URL = os.getenv("SUPABASE_URL") or "http://127.0.0.1:54321"
ANON_KEY = (
    os.getenv("SUPABASE_ANON_KEY")
    or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0"
)


@pytest.fixture
def socket() -> AsyncRealtimeClient:
    url = f"{URL}/realtime/v1"
    key = ANON_KEY
    return AsyncRealtimeClient(url, key)


def create_mock_response(status_code: int, reason_phrase: str = "OK", body: dict = None):
    """Create a mock HTTP response."""
    from unittest.mock import Mock

    mock_response = Mock()
    mock_response.status_code = status_code
    mock_response.reason_phrase = reason_phrase
    if body:
        mock_response.json = Mock(return_value=body)
    else:
        mock_response.json = Mock(side_effect=Exception("No JSON body"))
    return mock_response


@pytest.mark.asyncio
async def test_http_send_without_access_token():
    """Test http_send with no access token."""
    # Create a client without setting access_token
    url = f"{URL}/realtime/v1"
    socket_no_token = AsyncRealtimeClient(url, None)
    channel: AsyncRealtimeChannel = socket_no_token.channel("test-topic")

    mock_response = create_mock_response(202, "Accepted")

    with patch("httpx.AsyncClient.post", return_value=mock_response) as mock_post:
        result = await channel.http_send("test-event", {"data": "test"})

        assert result == {"success": True}
        assert mock_post.called
        call_args = mock_post.call_args

        # Verify headers
        headers = call_args.kwargs["headers"]
        assert headers["Authorization"] == ""
        assert headers["apikey"] == ""
        assert headers["Content-Type"] == "application/json"

        # Verify body
        body = call_args.kwargs["json"]
        assert body["messages"][0]["topic"] == "realtime:test-topic"
        assert body["messages"][0]["event"] == "test-event"
        assert body["messages"][0]["payload"] == {"data": "test"}
        assert body["messages"][0]["private"] is False


@pytest.mark.asyncio
async def test_http_send_with_access_token(socket: AsyncRealtimeClient):
    """Test http_send with access token."""
    await socket.set_auth("token123")
    channel: AsyncRealtimeChannel = socket.channel("test-topic")

    mock_response = create_mock_response(202, "Accepted")

    with patch("httpx.AsyncClient.post", return_value=mock_response) as mock_post:
        result = await channel.http_send("test-event", {"data": "test"})

        assert result == {"success": True}
        assert mock_post.called
        call_args = mock_post.call_args

        # Verify Authorization header includes token
        headers = call_args.kwargs["headers"]
        assert headers["Authorization"] == "Bearer token123"
        assert headers["apikey"] == ANON_KEY


@pytest.mark.asyncio
async def test_http_send_rejects_when_payload_is_none(socket: AsyncRealtimeClient):
    """Test http_send raises ValueError when payload is None."""
    channel: AsyncRealtimeChannel = socket.channel("test-topic")

    with pytest.raises(ValueError, match="Payload is required for http_send"):
        await channel.http_send("test-event", None)


@pytest.mark.asyncio
async def test_http_send_handles_timeout_error(socket: AsyncRealtimeClient):
    """Test http_send handles timeout errors."""
    channel: AsyncRealtimeChannel = socket.channel("test-topic")

    with patch(
        "httpx.AsyncClient.post", side_effect=httpx.TimeoutException("Request timeout")
    ):
        with pytest.raises(Exception, match="Request timeout"):
            await channel.http_send("test-event", {"data": "test"})


@pytest.mark.asyncio
async def test_http_send_handles_non_202_status(socket: AsyncRealtimeClient):
    """Test http_send handles non-202 status codes."""
    channel: AsyncRealtimeChannel = socket.channel("test-topic")

    mock_response = create_mock_response(
        500, "Internal Server Error", {"error": "Server error"}
    )

    with patch("httpx.AsyncClient.post", return_value=mock_response):
        with pytest.raises(Exception, match="Server error"):
            await channel.http_send("test-event", {"data": "test"})


@pytest.mark.asyncio
async def test_http_send_uses_error_message_from_body(socket: AsyncRealtimeClient):
    """Test http_send uses error message from response body."""
    channel: AsyncRealtimeChannel = socket.channel("test-topic")

    mock_response = create_mock_response(
        400, "Bad Request", {"message": "Invalid request"}
    )

    with patch("httpx.AsyncClient.post", return_value=mock_response):
        with pytest.raises(Exception, match="Invalid request"):
            await channel.http_send("test-event", {"data": "test"})


@pytest.mark.asyncio
async def test_http_send_falls_back_to_reason_phrase(socket: AsyncRealtimeClient):
    """Test http_send falls back to reason phrase when JSON parsing fails."""
    channel: AsyncRealtimeChannel = socket.channel("test-topic")

    mock_response = create_mock_response(503, "Service Unavailable")

    with patch("httpx.AsyncClient.post", return_value=mock_response):
        with pytest.raises(Exception, match="Service Unavailable"):
            await channel.http_send("test-event", {"data": "test"})


@pytest.mark.asyncio
async def test_http_send_respects_custom_timeout(socket: AsyncRealtimeClient):
    """Test http_send respects custom timeout option."""
    channel: AsyncRealtimeChannel = socket.channel("test-topic")

    mock_response = create_mock_response(202, "Accepted")

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        await channel.http_send("test-event", {"data": "test"}, timeout=3000)

        # Verify timeout was passed correctly (3000ms = 3.0s)
        assert mock_client_class.called
        call_args = mock_client_class.call_args
        assert call_args.kwargs["timeout"] == 3.0


@pytest.mark.asyncio
async def test_http_send_with_private_channel(socket: AsyncRealtimeClient):
    """Test http_send with a private channel."""
    channel: AsyncRealtimeChannel = socket.channel(
        "test-topic", params={"config": {"private": True}}
    )

    mock_response = create_mock_response(202, "Accepted")

    with patch("httpx.AsyncClient.post", return_value=mock_response) as mock_post:
        result = await channel.http_send("test-event", {"data": "test"})

        assert result == {"success": True}
        assert mock_post.called

        # Verify private flag is set
        body = mock_post.call_args.kwargs["json"]
        assert body["messages"][0]["private"] is True


@pytest.mark.asyncio
async def test_http_send_uses_default_timeout(socket: AsyncRealtimeClient):
    """Test http_send uses default timeout when not specified."""
    socket_with_custom_timeout = AsyncRealtimeClient(
        f"{URL}/realtime/v1", ANON_KEY, timeout=5000
    )
    channel: AsyncRealtimeChannel = socket_with_custom_timeout.channel("test-topic")

    mock_response = create_mock_response(202, "Accepted")

    with patch("httpx.AsyncClient") as mock_client_class:
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value = mock_client
        mock_client.__aexit__.return_value = None
        mock_client.post.return_value = mock_response
        mock_client_class.return_value = mock_client

        await channel.http_send("test-event", {"data": "test"})

        # Verify default timeout was used (5000ms = 5.0s)
        assert mock_client_class.called
        call_args = mock_client_class.call_args
        assert call_args.kwargs["timeout"] == 5.0


@pytest.mark.asyncio
async def test_http_send_sends_correct_payload(socket: AsyncRealtimeClient):
    """Test http_send sends the correct payload structure."""
    channel: AsyncRealtimeChannel = socket.channel("test-topic")

    mock_response = create_mock_response(202, "Accepted")

    with patch("httpx.AsyncClient.post", return_value=mock_response) as mock_post:
        test_payload = {"key": "value", "nested": {"data": 123}}
        result = await channel.http_send("test-payload-event", test_payload)

        assert result == {"success": True}
        assert mock_post.called

        # Verify the exact payload structure
        body = mock_post.call_args.kwargs["json"]
        assert body["messages"][0]["topic"] == "realtime:test-topic"
        assert body["messages"][0]["event"] == "test-payload-event"
        assert body["messages"][0]["payload"] == test_payload


@pytest.mark.asyncio
async def test_send_broadcast_shows_warning_when_not_connected(
    socket: AsyncRealtimeClient, caplog
):
    """Test send_broadcast shows deprecation warning when not connected."""
    channel: AsyncRealtimeChannel = socket.channel("test-topic")

    # Don't connect the socket, so _can_push() returns False
    # This will trigger the warning

    with pytest.raises(Exception):
        # send_broadcast will fail because we're not subscribed, but we want to check the warning
        await channel.send_broadcast("test-event", {"data": "test"})

    # Check that the warning was logged
    warning_found = any(
        "falling back to REST API" in record.message
        for record in caplog.records
        if record.levelname == "WARNING"
    )
    assert warning_found, "Expected deprecation warning was not logged"
