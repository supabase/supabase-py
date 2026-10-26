from unittest.mock import AsyncMock, patch

import pytest

from realtime import AsyncRealtimeClient


@pytest.mark.asyncio
@pytest.mark.parametrize("timeout", [1, 30])
async def test_connect_applies_configured_opening_timeout(timeout: int) -> None:
    client = AsyncRealtimeClient("ws://localhost/realtime/v1", timeout=timeout)

    with (
        patch("realtime._async.client.connect", new_callable=AsyncMock) as connect,
        patch.object(client, "_on_connect", new_callable=AsyncMock),
    ):
        await client.connect()

    connect.assert_awaited_once_with(client.endpoint_url(), open_timeout=timeout)


@pytest.mark.asyncio
async def test_connect_applies_default_opening_timeout() -> None:
    client = AsyncRealtimeClient("ws://localhost/realtime/v1")

    with (
        patch("realtime._async.client.connect", new_callable=AsyncMock) as connect,
        patch.object(client, "_on_connect", new_callable=AsyncMock),
    ):
        await client.connect()

    connect.assert_awaited_once_with(client.endpoint_url(), open_timeout=10)
