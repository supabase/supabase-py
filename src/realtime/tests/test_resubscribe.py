import asyncio
import json
from typing import Any, Dict, List
from unittest.mock import AsyncMock

import pytest
import pytest_asyncio

from realtime import AsyncRealtimeChannel, AsyncRealtimeClient
from realtime.message import ServerMessageAdapter
from realtime.types import ChannelStates, RealtimeSubscribeStates

URL = "http://127.0.0.1:54321/realtime/v1"


class FakeServer:
    """Acknowledges every join and leave the client sends."""

    def __init__(self, socket: AsyncRealtimeClient) -> None:
        self.socket = socket
        self.sent: List[Dict[str, Any]] = []

    async def send(self, raw: str) -> None:
        message = json.loads(raw)
        self.sent.append(message)
        if message["event"] not in ("phx_join", "phx_leave"):
            return
        reply = ServerMessageAdapter.validate_python(
            {
                "topic": message["topic"],
                "event": "phx_reply",
                "ref": message["ref"],
                "payload": {"status": "ok", "response": {}},
            }
        )
        channel = self.socket.channels.get(message["topic"])
        if channel is not None:
            asyncio.get_running_loop().call_soon(channel._handle_message, reply)


@pytest_asyncio.fixture
async def socket():
    socket = AsyncRealtimeClient(URL, "token")
    server = FakeServer(socket)
    ws = AsyncMock()
    ws.send.side_effect = server.send
    socket._ws_connection = ws
    socket.server = server  # type: ignore[attr-defined]
    await socket.connect()
    yield socket
    await socket.close()


async def settle(channel: AsyncRealtimeChannel) -> None:
    for _ in range(50):
        await asyncio.sleep(0.01)
        if channel.is_joined and not getattr(channel, "_resubscribing", False):
            return


def events(socket: AsyncRealtimeClient) -> List[str]:
    return [m["event"] for m in socket.server.sent]  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_presence_callback_on_joined_channel_rejoins_with_presence(socket):
    channel = socket.channel("room")
    states: List[RealtimeSubscribeStates] = []
    await channel.subscribe(lambda state, error: states.append(state))
    await settle(channel)
    assert channel.is_joined

    channel.on_presence_sync(lambda: None)
    await settle(channel)

    assert events(socket) == ["phx_join", "phx_leave", "phx_join"]
    assert channel.is_joined
    assert socket.channels["realtime:room"] is channel
    last_join = socket.server.sent[-1]
    assert last_join["payload"]["config"]["presence"]["enabled"] is True
    assert states == [RealtimeSubscribeStates.SUBSCRIBED] * 2


@pytest.mark.asyncio
async def test_several_presence_callbacks_resubscribe_once(socket):
    channel = socket.channel("room")
    await channel.subscribe(lambda state, error: None)
    await settle(channel)

    channel.on_presence_sync(lambda: None)
    channel.on_presence_join(lambda key, current, new: None)
    channel.on_presence_leave(lambda key, current, left: None)
    await settle(channel)

    assert events(socket) == ["phx_join", "phx_leave", "phx_join"]
    assert channel.state == ChannelStates.JOINED
