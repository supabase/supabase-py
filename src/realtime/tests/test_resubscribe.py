import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any
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
        self.sent: list[dict[str, Any]] = []
        self.hold_leave = False
        self.leave_status = "ok"
        self.held: list[Any] = []

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
                "payload": {
                    "status": self.leave_status
                    if message["event"] == "phx_leave"
                    else "ok",
                    "response": {},
                },
            }
        )
        if self.hold_leave and message["event"] == "phx_leave":
            self.held.append(reply)
            return
        channel = self.socket.channels.get(message["topic"])
        if channel is not None:
            asyncio.get_running_loop().call_soon(channel._handle_message, reply)


@pytest_asyncio.fixture
async def socket() -> AsyncIterator[AsyncRealtimeClient]:
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
        if channel.is_joined and not channel._resubscribing:
            return


def events(socket: AsyncRealtimeClient) -> list[str]:
    return [m["event"] for m in socket.server.sent]  # type: ignore[attr-defined]


@pytest.mark.asyncio
async def test_presence_callback_on_joined_channel_rejoins_with_presence(
    socket: AsyncRealtimeClient,
) -> None:
    channel = socket.channel("room")
    states: list[RealtimeSubscribeStates] = []
    await channel.subscribe(lambda state, error: states.append(state))
    await settle(channel)
    assert channel.is_joined

    channel.on_presence_sync(lambda: None)
    await settle(channel)

    assert events(socket) == ["phx_join", "phx_leave", "phx_join"]
    assert channel.is_joined
    assert socket.channels["realtime:room"] is channel
    last_join = socket.server.sent[-1]  # type: ignore[attr-defined]
    assert last_join["payload"]["config"]["presence"]["enabled"] is True
    assert states == [
        RealtimeSubscribeStates.SUBSCRIBED,
        RealtimeSubscribeStates.CLOSED,
        RealtimeSubscribeStates.SUBSCRIBED,
    ]


@pytest.mark.asyncio
async def test_several_presence_callbacks_resubscribe_once(
    socket: AsyncRealtimeClient,
) -> None:
    channel = socket.channel("room")
    await channel.subscribe(lambda state, error: None)
    await settle(channel)

    channel.on_presence_sync(lambda: None)
    channel.on_presence_join(lambda key, current, new: None)
    channel.on_presence_leave(lambda key, current, left: None)
    await settle(channel)

    assert events(socket) == ["phx_join", "phx_leave", "phx_join"]
    assert channel.state == ChannelStates.JOINED


@pytest.mark.asyncio
async def test_presence_callback_on_presence_enabled_channel_does_not_rejoin(
    socket: AsyncRealtimeClient,
) -> None:
    channel = socket.channel("room")
    channel.on_presence_sync(lambda: None)
    await channel.subscribe(lambda state, error: None)
    await settle(channel)

    channel.on_presence_join(lambda key, current, new: None)
    await settle(channel)

    assert events(socket) == ["phx_join"]
    assert channel.is_joined


@pytest.mark.asyncio
async def test_unsubscribe_during_resubscribe_does_not_rejoin(
    socket: AsyncRealtimeClient,
) -> None:
    channel = socket.channel("room")
    await channel.subscribe(lambda state, error: None)
    await settle(channel)

    channel.on_presence_sync(lambda: None)
    await asyncio.sleep(0)
    await channel.unsubscribe()
    for _ in range(20):
        await asyncio.sleep(0.01)

    assert events(socket) == ["phx_join", "phx_leave", "phx_leave"]
    assert channel.is_closed
    assert "realtime:room" not in socket.channels


@pytest.mark.asyncio
async def test_unsubscribe_before_resubscribe_starts_does_not_rejoin(
    socket: AsyncRealtimeClient,
) -> None:
    channel = socket.channel("room")
    await channel.subscribe(lambda state, error: None)
    await settle(channel)

    channel.on_presence_sync(lambda: None)
    await channel.unsubscribe()
    for _ in range(20):
        await asyncio.sleep(0.01)

    assert events(socket) == ["phx_join", "phx_leave"]
    assert channel.is_closed
    assert "realtime:room" not in socket.channels


@pytest.mark.asyncio
async def test_disconnect_during_resubscribe_rejoins_on_reconnect(
    socket: AsyncRealtimeClient,
) -> None:
    channel = socket.channel("room")
    await channel.subscribe(lambda state, error: None)
    await settle(channel)

    ws = socket._ws_connection
    socket.server.hold_leave = True  # type: ignore[attr-defined]
    channel.on_presence_sync(lambda: None)
    for _ in range(5):
        await asyncio.sleep(0.01)
    await socket.close()
    for reply in socket.server.held:  # type: ignore[attr-defined]
        channel._handle_message(reply)
    for _ in range(20):
        await asyncio.sleep(0.01)

    assert events(socket) == ["phx_join", "phx_leave"]
    assert not socket.is_connected
    assert channel.is_errored
    assert socket.channels["realtime:room"] is channel

    socket._ws_connection = ws
    await socket._rejoin_errored_channels()
    await settle(channel)

    assert events(socket) == ["phx_join", "phx_leave", "phx_join"]
    assert channel.is_joined
    last_join = socket.server.sent[-1]  # type: ignore[attr-defined]
    assert last_join["payload"]["config"]["presence"]["enabled"] is True


@pytest.mark.asyncio
@pytest.mark.parametrize("outcome", ["error", "timeout"])
async def test_resubscribe_rejoins_after_failed_leave(
    socket: AsyncRealtimeClient, outcome: str
) -> None:
    channel = socket.channel("room")
    await channel.subscribe(lambda state, error: None)
    await settle(channel)

    channel.timeout = 0.05  # type: ignore[assignment]
    if outcome == "error":
        socket.server.leave_status = "error"  # type: ignore[attr-defined]
    else:
        socket.server.hold_leave = True  # type: ignore[attr-defined]
    channel.on_presence_sync(lambda: None)
    await settle(channel)

    assert events(socket) == ["phx_join", "phx_leave", "phx_join"]
    assert channel.is_joined
    assert socket.channels["realtime:room"] is channel


@pytest.mark.asyncio
async def test_server_close_during_resubscribe_keeps_channel_closed(
    socket: AsyncRealtimeClient,
) -> None:
    channel = socket.channel("room")
    await channel.subscribe(lambda state, error: None)
    await settle(channel)

    socket.server.hold_leave = True  # type: ignore[attr-defined]
    channel.on_presence_sync(lambda: None)
    for _ in range(5):
        await asyncio.sleep(0.01)
    channel._handle_message(
        ServerMessageAdapter.validate_python(
            {
                "topic": "realtime:room",
                "event": "phx_close",
                "ref": None,
                "payload": {},
            }
        )
    )
    for reply in socket.server.held:  # type: ignore[attr-defined]
        channel._handle_message(reply)
    for _ in range(20):
        await asyncio.sleep(0.01)

    assert events(socket) == ["phx_join", "phx_leave"]
    assert channel.is_closed
    assert "realtime:room" not in socket.channels
