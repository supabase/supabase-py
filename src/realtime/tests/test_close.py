from contextlib import aclosing
from unittest.mock import AsyncMock

from realtime import RealtimeClient

REALTIME_URL = "ws://127.0.0.1/realtime/v1"


def connected_client(close: AsyncMock) -> RealtimeClient:
    client = RealtimeClient(REALTIME_URL)
    client._ws_connection = AsyncMock(close=close)
    return client


async def test_aclose_closes_the_websocket() -> None:
    close = AsyncMock()
    client = connected_client(close)

    await client.aclose()

    close.assert_awaited_once()


async def test_aclosing_closes_the_websocket() -> None:
    close = AsyncMock()

    async with aclosing(connected_client(close)):
        close.assert_not_awaited()

    close.assert_awaited_once()
