import asyncio
from collections.abc import AsyncIterator, Awaitable, Callable
from unittest.mock import AsyncMock

import pytest
from websockets.asyncio.server import Server, ServerConnection, serve
from websockets.exceptions import ConnectionClosed

from realtime._serializer import decode, encode
from realtime.channel import RealtimeChannel, RealtimeChannelOptions
from realtime.client import connect_once
from realtime.message import Message
from realtime.types import ChannelEvents

HOST = "127.0.0.1"


async def get_token() -> str:
    return "my-publishable-key"


class FakeServer:
    def __init__(self) -> None:
        self.ws_server: Server | None = None
        self.url = ""
        self.connections: list[ServerConnection] = []

    async def __aenter__(self) -> "FakeServer":
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
        self.connections.append(connection)
        async for raw in connection:
            message = decode(raw)
            if message.ref is None:
                continue
            reply = Message(
                event=ChannelEvents.reply,
                topic=message.topic,
                ref=message.ref,
                payload={"status": "ok", "response": {"postgres_changes": []}},
            )
            try:
                await connection.send(encode(reply))
            except ConnectionClosed:
                return

    async def drop_connections(self) -> None:
        for connection in self.connections:
            await connection.close()


@pytest.fixture
async def server() -> AsyncIterator[FakeServer]:
    async with FakeServer() as server:
        yield server


SENDS: dict[str, Callable[[RealtimeChannel], Awaitable[object]]] = {
    "send_broadcast": lambda channel: channel.send_broadcast("event", {"a": 1}),
    "track": lambda channel: channel.track({"user": "a"}),
    "untrack": lambda channel: channel.untrack(),
    "unsubscribe": lambda channel: channel.unsubscribe(),
}


@pytest.mark.asyncio
@pytest.mark.parametrize("send", SENDS.values(), ids=SENDS.keys())
async def test_send_raises_when_the_connection_is_closed(
    server: FakeServer, send: Callable[[RealtimeChannel], Awaitable[object]]
) -> None:
    async with connect_once(server.url, get_token) as client:
        channel = client.channel("room")
        await channel.subscribe()

        await server.drop_connections()
        with pytest.raises(ConnectionClosed):
            await asyncio.wait_for(client._connection_failure, timeout=1)

        with pytest.raises(ConnectionClosed):
            await send(channel)


@pytest.mark.asyncio
@pytest.mark.parametrize("send", SENDS.values(), ids=SENDS.keys())
async def test_send_raises_when_the_connection_already_failed(
    server: FakeServer,
    send: Callable[[RealtimeChannel], Awaitable[object]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async with connect_once(server.url, get_token) as client:
        channel = client.channel("room")
        await channel.subscribe()
        ws_send = AsyncMock()
        monkeypatch.setattr(client._ws_connection, "send", ws_send)

        client._connection_failure.set_exception(TimeoutError())
        with pytest.raises(TimeoutError):
            await send(channel)

        ws_send.assert_not_awaited()


@pytest.mark.asyncio
async def test_acknowledged_broadcast_raises_when_the_connection_is_closed(
    server: FakeServer,
) -> None:
    async with connect_once(server.url, get_token) as client:
        channel = client.channel("room", RealtimeChannelOptions().broadcast(ack=True))
        await channel.subscribe()

        await server.drop_connections()
        with pytest.raises(ConnectionClosed):
            await asyncio.wait_for(client._connection_failure, timeout=1)

        with pytest.raises(ConnectionClosed):
            await channel.send_broadcast("event", {"a": 1})


@pytest.mark.asyncio
async def test_set_auth_raises_and_keeps_the_previous_token_when_the_send_fails(
    server: FakeServer,
) -> None:
    async with connect_once(server.url) as client:
        await client.channel("room").subscribe()
        await client.set_auth("first-token")
        assert client.last_token == "first-token"

        await server.drop_connections()
        with pytest.raises(ConnectionClosed):
            await asyncio.wait_for(client._connection_failure, timeout=1)

        with pytest.raises(ConnectionClosed):
            await client.set_auth("second-token")
        assert client.last_token == "first-token"
