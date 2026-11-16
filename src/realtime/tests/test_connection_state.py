import asyncio
import contextlib
import socket
from collections.abc import AsyncIterator
from typing import Literal

import pytest
from websockets.asyncio.server import Server, ServerConnection, serve

from realtime import ConnectionState, HeartbeatStatus, RealtimeClient
from realtime._serializer import decode, encode
from realtime.message import Message
from realtime.types import ChannelEvents

HOST = "127.0.0.1"

HeartbeatReply = Literal["ok", "error", "none"]


class HeartbeatServer:
    def __init__(self, reply: HeartbeatReply) -> None:
        self.reply = reply
        self.ws_server: Server | None = None
        self.url = ""

    async def __aenter__(self) -> "HeartbeatServer":
        self.ws_server = await serve(self.handler, HOST, 0)
        port = next(iter(self.ws_server.sockets)).getsockname()[1]
        self.url = f"http://{HOST}:{port}"
        await self.ws_server.start_serving()
        return self

    async def __aexit__(self, *exc: object) -> None:
        assert self.ws_server is not None
        self.ws_server.close()
        await self.ws_server.wait_closed()

    async def handler(self, connection: ServerConnection) -> None:
        async for raw in connection:
            message = decode(raw)
            if message.event != ChannelEvents.heartbeat or self.reply == "none":
                continue
            reply = Message(
                event=ChannelEvents.reply,
                topic=message.topic,
                ref=message.ref,
                payload={"status": self.reply, "response": {}},
            )
            await connection.send(encode(reply))


@pytest.fixture
async def ok_server() -> AsyncIterator[HeartbeatServer]:
    async with HeartbeatServer("ok") as server:
        yield server


async def take[T](iterator: AsyncIterator[T], count: int) -> list[T]:
    async def collect() -> list[T]:
        return [await anext(iterator) for _ in range(count)]

    return await asyncio.wait_for(collect(), timeout=5)


async def test_connection_state_follows_connect_and_close(
    ok_server: HeartbeatServer,
) -> None:
    client = RealtimeClient(ok_server.url)
    states = client.connection_states()

    assert client.connection_state == ConnectionState.CLOSED
    assert await anext(states) == ConnectionState.CLOSED

    await client.connect()
    assert client.connection_state == ConnectionState.CONNECTED
    await client.aclose()
    assert client.connection_state == ConnectionState.CLOSED

    assert await take(states, 3) == [
        ConnectionState.CONNECTING,
        ConnectionState.CONNECTED,
        ConnectionState.CLOSED,
    ]
    await states.aclose()


async def test_connection_states_yields_the_current_state_first(
    ok_server: HeartbeatServer,
) -> None:
    client = RealtimeClient(ok_server.url)
    await client.connect()
    try:
        assert await take(client.connection_states(), 1) == [ConnectionState.CONNECTED]
    finally:
        await client.aclose()


async def test_unread_states_are_bounded(ok_server: HeartbeatServer) -> None:
    client = RealtimeClient(ok_server.url, max_queued_messages=2)
    states = client.connection_states()
    await anext(states)

    await client.connect()
    await client.aclose()

    assert await take(states, 2) == [
        ConnectionState.CONNECTED,
        ConnectionState.CLOSED,
    ]
    await states.aclose()


async def test_failed_connect_moves_back_to_closed() -> None:
    with socket.socket() as unused:
        unused.bind((HOST, 0))
        port = unused.getsockname()[1]
    client = RealtimeClient(f"http://{HOST}:{port}")
    states = client.connection_states()
    await anext(states)

    with pytest.raises(ConnectionRefusedError):
        await client.connect()

    assert client.connection_state == ConnectionState.CLOSED
    assert await take(states, 2) == [
        ConnectionState.CONNECTING,
        ConnectionState.CLOSED,
    ]
    await states.aclose()


async def test_acknowledged_heartbeats_are_reported(
    ok_server: HeartbeatServer,
) -> None:
    client = RealtimeClient(ok_server.url, heartbeat_interval=0.01)
    heartbeats = client.heartbeats()
    first = asyncio.ensure_future(anext(heartbeats))
    await asyncio.sleep(0)
    await client.connect()
    try:
        assert [await first, *await take(heartbeats, 3)] == [
            HeartbeatStatus.SENT,
            HeartbeatStatus.OK,
            HeartbeatStatus.SENT,
            HeartbeatStatus.OK,
        ]
        assert client.connection_state == ConnectionState.CONNECTED
    finally:
        await heartbeats.aclose()
        await client.aclose()


@pytest.mark.parametrize(
    ("reply", "status"),
    [("error", HeartbeatStatus.ERROR), ("none", HeartbeatStatus.TIMEOUT)],
)
async def test_failed_heartbeat_closes_the_connection(
    reply: HeartbeatReply, status: HeartbeatStatus
) -> None:
    async with HeartbeatServer(reply) as server:
        client = RealtimeClient(server.url, heartbeat_timeout=0.05)
        heartbeats = client.heartbeats()
        first = asyncio.ensure_future(anext(heartbeats))
        await asyncio.sleep(0)
        states = client.connection_states()
        await anext(states)
        await client.connect()
        try:
            assert [await first, *await take(heartbeats, 1)] == [
                HeartbeatStatus.SENT,
                status,
            ]
            assert await take(states, 3) == [
                ConnectionState.CONNECTING,
                ConnectionState.CONNECTED,
                ConnectionState.CLOSED,
            ]
            assert client.connection_state == ConnectionState.CLOSED
        finally:
            await heartbeats.aclose()
            await states.aclose()
            await client.aclose()


async def test_stopped_iterators_stop_listening(ok_server: HeartbeatServer) -> None:
    client = RealtimeClient(ok_server.url)
    states = client.connection_states()
    heartbeats = client.heartbeats()
    await anext(states)
    pending = asyncio.ensure_future(anext(heartbeats))
    await asyncio.sleep(0)

    pending.cancel()
    with contextlib.suppress(asyncio.CancelledError):
        await pending
    await states.aclose()

    assert not client._connection_state_listeners
    assert not client._heartbeat_listeners
