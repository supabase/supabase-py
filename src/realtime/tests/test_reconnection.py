import asyncio
import datetime
import os
from typing import AsyncIterator

import aiohttp
import pytest
from dotenv import load_dotenv
from pydantic import BaseModel, TypeAdapter
from websockets import broadcast
from websockets.asyncio.server import ServerConnection, serve
from websockets.exceptions import ConnectionClosedOK

from realtime import (
    RealtimeChannel,
    RealtimeClient,
    RealtimePostgresChangesListenEvent,
    RealtimeSubscribeStates,
)
from realtime.channel import RealtimeChannelOptions
from realtime.client import MaxRetriesExceeded, automatically_reconnect, connect_once
from realtime.message import (
    BroadcastMessage,
    ChannelLeaveMessage,
    ClientMessage,
    HeartbeatMessage,
    JoinMessage,
    Message,
    PostgresChangesMessage,
    ReplyMessage,
    ReplyPostgresChanges,
    SuccessReplyMessage,
    SystemMessage,
)
from realtime.types import DEFAULT_HEARTBEAT_INTERVAL, DEFAULT_TIMEOUT, ChannelEvents

PORT = 55555
URL = "localhost"
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
    def __init__(self, url: str, port: int):
        self.url = url
        self.port = port

    async def start(self) -> None:
        self.ws_server = await serve(self.handler, self.url, self.port)
        await self.ws_server.start_serving()

    async def __aenter__(self) -> "RealtimeServer":
        await self.start()
        await self.ws_server.__aenter__()
        return self

    async def __aexit__(self, type, exc_value, traceback):
        await self.ws_server.__aexit__(type, exc_value, traceback)

    async def close(self):
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


@pytest.fixture
async def server() -> AsyncIterator[RealtimeServer]:
    async with RealtimeServer(URL, PORT) as server:
        yield server


async def test_raises_on_send_broadcast(server: RealtimeServer) -> None:
    async with (
        connect_once(f"http://{URL}:{PORT}", get_token) as client,
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
        connect_once(f"http://{URL}:{PORT}", get_token) as client,
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
        connect_once(f"http://{URL}:{PORT}", get_token) as client,
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
    async def restart_server_after_2_seconds():
        await asyncio.sleep(2)
        await server.start()

    async def client_callback(client: RealtimeClient) -> None:
        return

    await server.close()
    asyncio.create_task(restart_server_after_2_seconds())
    await automatically_reconnect(
        f"http://{URL}:{PORT}", get_token, client_callback, max_retries=3
    )


async def test_automatic_reconnection_fails_after_max_retries() -> None:
    # no server running.
    async def client_callback(client: RealtimeClient) -> None:
        return

    try:
        await automatically_reconnect(
            f"http://{URL}:{PORT}", get_token, client_callback, max_retries=3
        )
    except MaxRetriesExceeded as exc:
        return
    raise Exception("expected max retries exceeded exception but got nothing")


async def test_automatic_reconnection_calls_callback_when_connected(
    server: RealtimeServer,
) -> None:
    called_twice = False

    async def restart_server_after_1_second():
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
        async with client.channel("test-channel") as channel:
            pass

    await automatically_reconnect(
        f"http://{URL}:{PORT}", get_token, client_callback, max_retries=3
    )
    assert called_twice
