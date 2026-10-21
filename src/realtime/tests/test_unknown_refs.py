import asyncio
from typing import AsyncIterator

import pytest
from websockets.asyncio.server import ServerConnection, serve

from realtime.client import connect_once
from realtime.message import (
    Message,
    ReplyMessage,
    ReplyPostgresChanges,
    SuccessReplyMessage,
)
from realtime.types import ChannelEvents

PORT = 55566
URL = "localhost"


async def get_token() -> str:
    return "my-publishable-key"


def reply_ack(topic: str, ref: str) -> str:
    return ReplyMessage(
        event=ChannelEvents.reply,
        topic=topic,
        ref=ref,
        payload=SuccessReplyMessage(
            status="ok", response=ReplyPostgresChanges(postgres_changes=[])
        ),
    ).model_dump_json()


class FakeServer:
    """Acks every ref'd message, closes channels on leave and can delay join replies."""

    def __init__(self) -> None:
        self.join_reply_delay = 0.0

    async def __aenter__(self) -> "FakeServer":
        self.ws_server = await serve(self.handler, URL, PORT)
        await self.ws_server.start_serving()
        return self

    async def __aexit__(self, *exc) -> None:
        self.ws_server.close()
        await self.ws_server.wait_closed()

    async def handler(self, connection: ServerConnection) -> None:
        while True:
            message = Message.model_validate_json(await connection.recv(decode=False))
            if message.ref is None:
                continue
            if message.event == ChannelEvents.join and self.join_reply_delay:
                await asyncio.sleep(self.join_reply_delay)
            await connection.send(reply_ack(message.topic, message.ref))
            if message.event == ChannelEvents.leave:
                close = Message(
                    topic=message.topic,
                    event=ChannelEvents.close,
                    payload={},
                    ref=message.join_ref,
                    join_ref=message.join_ref,
                )
                await connection.send(close.model_dump_json())
                await connection.send(reply_ack(message.topic, "unknown-ref"))


@pytest.fixture
async def server() -> AsyncIterator[FakeServer]:
    async with FakeServer() as server:
        yield server


@pytest.mark.asyncio
async def test_close_with_join_ref_after_leave_keeps_client_alive(server: FakeServer):
    async with connect_once(f"http://{URL}:{PORT}", get_token) as client:
        async with client.channel("first"):
            pass
        async with client.channel("second") as channel:
            assert channel.joined
        assert not client._connection_failure.done()
        assert client.message_refs == {}


@pytest.mark.asyncio
async def test_orphan_reply_is_not_forwarded_to_the_channel(server: FakeServer):
    async with connect_once(f"http://{URL}:{PORT}", get_token) as client:
        channel = client.channel("room")
        await channel.subscribe()
        await channel.socket.send_no_wait(
            Message(topic=channel.topic, event=ChannelEvents.leave, payload={}, ref="x")
        )
        await asyncio.sleep(0.1)
        queued = []
        while not channel.message_stream.empty():
            queued.append(channel.message_stream.get_nowait())
        assert all(message.event != ChannelEvents.reply for message in queued)


@pytest.mark.asyncio
async def test_late_reply_for_timed_out_send_keeps_client_alive(server: FakeServer):
    server.join_reply_delay = 0.2
    async with connect_once(f"http://{URL}:{PORT}", get_token) as client:
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(client.channel("slow").subscribe(), timeout=0.05)

        server.join_reply_delay = 0
        await asyncio.sleep(0.3)
        async with client.channel("fast") as channel:
            assert channel.joined
        assert not client._connection_failure.done()
