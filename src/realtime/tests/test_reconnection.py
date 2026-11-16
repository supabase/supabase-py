from collections.abc import AsyncIterator
from types import TracebackType

import pytest
from pydantic import TypeAdapter
from websockets.asyncio.server import Server, ServerConnection, serve
from websockets.exceptions import ConnectionClosed, ConnectionClosedOK

from realtime import ChannelNotJoinedError, ChannelStateChange, ChannelStates
from realtime._serializer import decode, encode
from realtime.client import connect_once
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
        with pytest.raises((ConnectionClosedOK, ChannelNotJoinedError)):
            await channel.send_presence("track", {})


async def test_yields_the_errored_state_when_the_connection_drops(
    server: RealtimeServer,
) -> None:
    async with (
        connect_once(server.url, get_token) as client,
        client.channel("test-channel") as channel,
    ):
        await server.close()
        message = await anext(aiter(channel.messages))

        assert isinstance(message, ChannelStateChange)
        assert message.state == ChannelStates.ERRORED
        assert isinstance(message.error, ConnectionClosed)
        assert channel.state == ChannelStates.ERRORED
