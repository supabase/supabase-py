from contextlib import aclosing
from unittest.mock import AsyncMock

from yarl import URL

from realtime import RealtimeClient

REALTIME_URL = URL("ws://127.0.0.1/realtime/v1")


async def test_aclose_closes_the_websocket() -> None:
    close = AsyncMock()
    client = RealtimeClient(REALTIME_URL, AsyncMock(close=close))

    await client.aclose()

    close.assert_awaited_once()


async def test_aclosing_closes_the_websocket() -> None:
    close = AsyncMock()

    async with aclosing(RealtimeClient(REALTIME_URL, AsyncMock(close=close))):
        close.assert_not_awaited()

    close.assert_awaited_once()
