"""Tests for AsyncRealtimeClient access_token pull approach (issue #1210)."""

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from realtime._async.client import AsyncRealtimeClient


@pytest.fixture
def client():
    return AsyncRealtimeClient("https://example.com", token="initial-token")


@pytest.mark.asyncio
async def test_get_token_returns_static_token_when_no_getter(client):
    """Without an access_token getter, _get_token returns the static token."""
    result = await client._get_token()
    assert result == "initial-token"


@pytest.mark.asyncio
async def test_get_token_calls_sync_getter():
    """A sync callable getter is called and its value stored in access_token."""
    getter = MagicMock(return_value="fresh-token")
    client = AsyncRealtimeClient(
        "https://example.com", token="old-token", access_token=getter
    )

    result = await client._get_token()

    getter.assert_called_once()
    assert result == "fresh-token"
    assert client.access_token == "fresh-token"


@pytest.mark.asyncio
async def test_get_token_calls_async_getter():
    """An async callable getter is awaited and its value stored in access_token."""

    async def async_getter():
        return "async-fresh-token"

    client = AsyncRealtimeClient(
        "https://example.com", token="old-token", access_token=async_getter
    )

    result = await client._get_token()

    assert result == "async-fresh-token"
    assert client.access_token == "async-fresh-token"


@pytest.mark.asyncio
async def test_connect_pulls_fresh_token_before_connecting():
    """connect() calls _get_token() to refresh the token before opening the socket."""
    call_order = []

    async def async_getter():
        call_order.append("getter")
        return "refreshed-token"

    client = AsyncRealtimeClient(
        "https://example.com", token="stale-token", access_token=async_getter
    )

    mock_ws = AsyncMock()

    async def fake_connect(url):
        call_order.append("connect")
        return mock_ws

    mock_connect = AsyncMock(side_effect=fake_connect)

    with patch("realtime._async.client.connect", mock_connect):
        with patch.object(client, "_on_connect", new_callable=AsyncMock):
            await client.connect()

    assert call_order[0] == "getter", "Token getter must be called before connecting"
    assert client.access_token == "refreshed-token"


@pytest.mark.asyncio
async def test_reconnect_pulls_fresh_token_before_reconnecting():
    """_reconnect() calls _get_token() so stale tokens are never reused."""
    call_count = 0

    def sync_getter():
        nonlocal call_count
        call_count += 1
        return f"refreshed-token-{call_count}"

    client = AsyncRealtimeClient(
        "https://example.com", token="old-token", access_token=sync_getter
    )

    mock_ws = AsyncMock()
    mock_connect = AsyncMock(return_value=mock_ws)

    with patch("realtime._async.client.connect", mock_connect):
        with patch.object(client, "_on_connect", new_callable=AsyncMock):
            with patch.object(client, "connect", new_callable=AsyncMock):
                await client._reconnect()

    # getter called once in _reconnect before connect
    assert call_count >= 1
    assert client.access_token == "refreshed-token-1"


@pytest.mark.asyncio
async def test_no_getter_static_token_unchanged():
    """Without a getter, connect() leaves access_token unchanged."""
    client = AsyncRealtimeClient("https://example.com", token="static-token")

    mock_ws = AsyncMock()
    mock_connect = AsyncMock(return_value=mock_ws)

    with patch("realtime._async.client.connect", mock_connect):
        with patch.object(client, "_on_connect", new_callable=AsyncMock):
            await client.connect()

    assert client.access_token == "static-token"
