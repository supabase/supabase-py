from typing import AsyncIterator

import pytest
from pydantic import TypeAdapter
from websockets.asyncio.server import ServerConnection, serve

from realtime.channel import RealtimeChannelOptions
from realtime.client import connect_once
from realtime.message import (
    ClientMessage,
    Message,
    ReplyMessage,
    ReplyPostgresChanges,
    SuccessReplyMessage,
)
from realtime.types import ChannelEvents

# SDK-1526: the Realtime protocol requires every client-sent event (join, leave,
# broadcast, presence track/untrack) to carry the channel's current `join_ref` so
# the server can detect stale messages after a rejoin.
# See: https://supabase.com/docs/guides/realtime/protocol#client-sent-events

PORT = 55565
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


class RecordingServer:
    """A local websocket server that acks every ref'd message and records what it received."""

    def __init__(self, url: str, port: int):
        self.url = url
        self.port = port
        self.received: list[Message] = []

    async def start(self) -> None:
        self.ws_server = await serve(self.handler, self.url, self.port)
        await self.ws_server.start_serving()

    async def __aenter__(self) -> "RecordingServer":
        await self.start()
        return self

    async def __aexit__(self, *exc) -> None:
        self.ws_server.close()
        await self.ws_server.wait_closed()

    async def handler(self, connection: ServerConnection) -> None:
        while True:
            raw = await connection.recv(decode=False)
            message = Message.model_validate_json(raw)
            self.received.append(message)
            if message.ref is not None:
                await connection.send(reply_ack(message.topic, message.ref))

    def events(self, event: str) -> list[Message]:
        return [m for m in self.received if m.event == event]


@pytest.fixture
async def server() -> AsyncIterator[RecordingServer]:
    async with RecordingServer(URL, PORT) as server:
        yield server


@pytest.mark.asyncio
async def test_join_carries_join_ref_equal_to_its_own_ref(server: RecordingServer):
    async with connect_once(f"http://{URL}:{PORT}", get_token) as client:
        async with client.channel("test-join-ref") as channel:
            [join_message] = server.events("phx_join")
            assert join_message.join_ref == join_message.ref
            assert join_message.join_ref == channel.join_ref


@pytest.mark.asyncio
async def test_broadcast_push_carries_channel_join_ref(server: RecordingServer):
    options = RealtimeChannelOptions().broadcast(ack=True)
    async with connect_once(f"http://{URL}:{PORT}", get_token) as client:
        async with client.channel("test-join-ref-broadcast", params=options) as channel:
            await channel.send_broadcast("cursor", {"x": 1})

            [join_message] = server.events("phx_join")
            [broadcast_message] = server.events("broadcast")
            assert broadcast_message.join_ref == join_message.ref
            assert broadcast_message.join_ref is not None


@pytest.mark.asyncio
async def test_presence_track_and_untrack_carry_channel_join_ref(
    server: RecordingServer,
):
    options = RealtimeChannelOptions().presence(enabled=True)
    async with connect_once(f"http://{URL}:{PORT}", get_token) as client:
        async with client.channel("test-join-ref-presence", params=options) as channel:
            await channel.track({"id": 123})
            await channel.untrack()

            [join_message] = server.events("phx_join")
            track_message, untrack_message = server.events("presence")
            assert track_message.payload["event"] == "track"
            assert track_message.join_ref == join_message.ref

            assert untrack_message.payload["event"] == "untrack"
            assert untrack_message.join_ref == join_message.ref


@pytest.mark.asyncio
async def test_leave_push_carries_channel_join_ref(server: RecordingServer):
    async with connect_once(f"http://{URL}:{PORT}", get_token) as client:
        async with client.channel("test-join-ref-leave"):
            pass

        [join_message] = server.events("phx_join")
        [leave_message] = server.events("phx_leave")
        assert leave_message.join_ref == join_message.ref
