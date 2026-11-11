import asyncio
import socket
from collections.abc import AsyncIterator
from types import TracebackType

import pytest
from pydantic import TypeAdapter
from websockets.asyncio.server import Server, ServerConnection, serve
from websockets.exceptions import ConnectionClosedOK

from realtime import (
    MaxRetriesExceeded,
    RealtimeClient,
)
from realtime._serializer import decode, encode
from realtime.client import automatically_reconnect, connect_once
from realtime.message import (
    AccessTokenMessage,
    ChannelLeaveMessage,
    ClientMessage,
    HeartbeatMessage,
    JoinMessage,
    Message,
)
from realtime.types import ChannelEvents

HOST = "127.0.0.1"
PUBLISHABLE_KEY = "my-publishable-key"
MessageParser: TypeAdapter[ClientMessage] = TypeAdapter(ClientMessage)


async def get_token() -> str:
    return PUBLISHABLE_KEY


def reply_ack(topic: str, ref: str) -> str | bytes:
    return encode(
        Message(
            event=ChannelEvents.reply,
            topic=topic,
            ref=ref,
            payload={"status": "ok", "response": {"postgres_changes": []}},
        )
    )


class RealtimeServer:
    def __init__(self) -> None:
        self.ws_server: Server | None = None
        self.port = 0

    @property
    def url(self) -> str:
        return f"http://{HOST}:{self.port}"

    async def start(self) -> None:
        self.ws_server = await serve(self.handler, HOST, self.port)
        self.port = next(iter(self.ws_server.sockets)).getsockname()[1]
        await self.ws_server.start_serving()

    async def __aenter__(self) -> "RealtimeServer":
        await self.start()
        assert self.ws_server is not None
        await self.ws_server.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        assert self.ws_server is not None
        await self.ws_server.__aexit__(exc_type, exc_value, traceback)

    async def close(self) -> None:
        assert self.ws_server is not None
        self.ws_server.close()
        await self.ws_server.wait_closed()

    async def handler(self, connection: ServerConnection) -> None:
        while True:
            try:
                frame = await connection.recv()
            except ConnectionClosedOK:
                break
            msg = MessageParser.validate_python(decode(frame).model_dump())
            match msg:
                case HeartbeatMessage(topic=topic, ref=ref):
                    await connection.send(reply_ack(topic, ref))
                case JoinMessage(topic=topic, ref=ref):
                    await connection.send(reply_ack(topic, ref))
                case ChannelLeaveMessage(topic=topic, ref=ref):
                    await connection.send(reply_ack(topic, ref))
                case _:
                    pass


def test_parses_the_access_token_message_the_client_sends() -> None:
    message = Message(
        topic="realtime:test-channel",
        event=ChannelEvents.access_token,
        payload={"access_token": "token"},
        ref="3",
    )

    parsed = MessageParser.validate_python(decode(encode(message)).model_dump())

    assert isinstance(parsed, AccessTokenMessage)
    assert parsed.ref == "3"


@pytest.fixture
async def server() -> AsyncIterator[RealtimeServer]:
    async with RealtimeServer() as server:
        yield server


async def test_raises_on_send_broadcast(server: RealtimeServer) -> None:
    async with (
        connect_once(server.url, get_token) as client,
        client.channel("test-channel") as channel,
    ):
        await server.close()
        try:
            await channel.send_broadcast("test", {})
        except ConnectionClosedOK:
            return
        raise Exception("should have raised a connection error, but got nothing")


async def test_raises_on_send_presence(server: RealtimeServer) -> None:
    async with (
        connect_once(server.url, get_token) as client,
        client.channel("test-channel") as channel,
    ):
        await server.close()
        try:
            await channel.send_presence("presence", {})
        except ConnectionClosedOK:
            return
        raise Exception("should have raised a connection error, but got nothing")


async def test_raises_on_listen_message(server: RealtimeServer) -> None:
    async with (
        connect_once(server.url, get_token) as client,
        client.channel("test-channel") as channel,
    ):
        await server.close()
        try:
            async for _msg in channel.messages:
                pass
        except ConnectionClosedOK:
            return
        raise Exception("should have raised a connection error, but got nothing")


async def test_automatic_reconnection(server: RealtimeServer) -> None:
    async def restart_server_after_2_seconds() -> None:
        await asyncio.sleep(2)
        await server.start()

    async def client_callback(client: RealtimeClient) -> None:
        return

    await server.close()
    restart = asyncio.create_task(restart_server_after_2_seconds())
    await automatically_reconnect(server.url, get_token, client_callback, max_retries=3)
    await restart


async def test_automatic_reconnection_fails_after_max_retries() -> None:
    async def client_callback(client: RealtimeClient) -> None:
        return

    with socket.socket() as unused:
        unused.bind((HOST, 0))
        port = unused.getsockname()[1]
        try:
            await automatically_reconnect(
                f"http://{HOST}:{port}", get_token, client_callback, max_retries=3
            )
        except MaxRetriesExceeded:
            return
    raise Exception("expected max retries exceeded exception but got nothing")


async def test_automatic_reconnection_calls_callback_when_connected(
    server: RealtimeServer,
) -> None:
    called_twice = False
    restart: asyncio.Task[None] | None = None

    async def restart_server_after_1_second() -> None:
        await asyncio.sleep(1)
        await server.start()

    async def client_callback(client: RealtimeClient) -> None:
        nonlocal called_twice, restart
        if called_twice:
            return
        called_twice = True
        await server.close()
        # reschedule server to re-start 1 second later
        restart = asyncio.create_task(restart_server_after_1_second())
        # this should raise when the server is offline
        async with client.channel("test-channel"):
            pass

    await automatically_reconnect(server.url, get_token, client_callback, max_retries=3)
    assert called_twice
    assert restart is not None
    await restart
