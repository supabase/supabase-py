import asyncio
import socket
from collections.abc import AsyncIterator
from types import TracebackType

import pytest
from pydantic import TypeAdapter
from websockets.asyncio.server import ServerConnection, serve
from websockets.exceptions import ConnectionClosedOK

from realtime import (
    RealtimeClient,
)
from realtime.client import MaxRetriesExceeded, automatically_reconnect, connect_once
from realtime.message import (
    ChannelLeaveMessage,
    ClientMessage,
    HeartbeatMessage,
    JoinMessage,
    ReplyMessage,
    ReplyPostgresChanges,
    SuccessReplyMessage,
)
from realtime.types import ChannelEvents

HOST = "127.0.0.1"
PUBLISHABLE_KEY = "my-publishable-key"
MessageParser: TypeAdapter[ClientMessage] = TypeAdapter(ClientMessage)


async def get_token() -> str:
    return PUBLISHABLE_KEY


def reply_ack(topic: str, ref: str) -> str:
    reply_msg = ReplyMessage(
        event=ChannelEvents.reply,
        topic=topic,
        ref=ref,
        payload=SuccessReplyMessage(
            status="ok", response=ReplyPostgresChanges(postgres_changes=[])
        ),
    )
    return reply_msg.model_dump_json()


class RealtimeServer:
    def __init__(self) -> None:
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
        await self.ws_server.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.ws_server.__aexit__(exc_type, exc_value, traceback)

    async def close(self) -> None:
        self.ws_server.close()
        await self.ws_server.wait_closed()

    async def handler(self, connection: ServerConnection) -> None:
        while True:
            try:
                message = await connection.recv(decode=False)
            except ConnectionClosedOK:
                break
            msg = MessageParser.validate_json(message)
            match msg:
                case HeartbeatMessage(topic=topic, ref=ref):
                    await connection.send(reply_ack(topic, ref))
                case JoinMessage(topic=topic, ref=ref):
                    await connection.send(reply_ack(topic, ref))
                case ChannelLeaveMessage(topic=topic, ref=ref):
                    await connection.send(reply_ack(topic, ref))
                case _:
                    pass


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
            async for msg in channel.messages:
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
    asyncio.create_task(restart_server_after_2_seconds())
    await automatically_reconnect(server.url, get_token, client_callback, max_retries=3)


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

    async def restart_server_after_1_second() -> None:
        await asyncio.sleep(1)
        await server.start()

    async def client_callback(client: RealtimeClient) -> None:
        nonlocal called_twice
        if called_twice:
            return
        called_twice = True
        await server.close()
        # reschedule server to re-start 1 second later
        asyncio.create_task(restart_server_after_1_second())
        # this should raise when the server is offline
        async with client.channel("test-channel"):
            pass

    await automatically_reconnect(server.url, get_token, client_callback, max_retries=3)
    assert called_twice
