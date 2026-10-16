import asyncio
from unittest.mock import AsyncMock

import pytest

from realtime import AsyncRealtimeClient
from realtime.types import ChannelStates, RealtimeSubscribeStates

URL = "http://127.0.0.1:54321/realtime/v1"


async def connected_socket(timeout: float) -> AsyncRealtimeClient:
    socket = AsyncRealtimeClient(URL, "token", timeout=timeout)  # type: ignore[arg-type]
    socket._ws_connection = AsyncMock()
    await socket.connect()
    return socket


@pytest.mark.asyncio
async def test_join_push_uses_client_timeout():
    socket = await connected_socket(timeout=0.1)
    channel = socket.channel("join-timeout")
    states: list[RealtimeSubscribeStates] = []

    await channel.subscribe(lambda state, error: states.append(state))
    await asyncio.sleep(0.3)

    assert states == [RealtimeSubscribeStates.TIMED_OUT]
    assert channel.state == ChannelStates.ERRORED

    channel.rejoin_timer.reset()
    await socket.close()


@pytest.mark.asyncio
async def test_unsubscribe_closes_channel_when_leave_times_out():
    socket = await connected_socket(timeout=0.1)
    channel = socket.channel("leave-timeout")
    await channel.subscribe(lambda state, error: None)
    channel.join_push.destroy()

    await channel.unsubscribe()
    assert channel.state == ChannelStates.LEAVING
    await asyncio.sleep(0.3)

    assert channel.state == ChannelStates.CLOSED
    assert channel.topic not in socket.channels

    await socket.close()
