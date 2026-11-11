import asyncio
from collections.abc import AsyncIterator

import pytest
from websockets.asyncio.server import Server, ServerConnection, serve

from realtime._serializer import decode, encode
from realtime.client import RealtimeClient, connect_once
from realtime.message import Message
from realtime.types import ChannelEvents

HOST = "127.0.0.1"


def connection_failure(client: RealtimeClient) -> asyncio.Future[Message]:
    assert client._connection_failure is not None
    return client._connection_failure


async def get_token() -> str:
    return "my-publishable-key"


def reply_ack(topic: str, ref: str) -> str | bytes:
    return encode(
        Message(
            event=ChannelEvents.reply,
            topic=topic,
            ref=ref,
            payload={"status": "ok", "response": {"postgres_changes": []}},
        )
    )


class FakeServer:
    """Acks every ref'd message, closes channels on leave and can delay join replies."""

    def __init__(self) -> None:
        self.ws_server: Server | None = None
        self.url = ""
        self.join_reply_delay = 0.0

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
        while True:
            message = decode(await connection.recv())
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
                await connection.send(encode(close))
                await connection.send(reply_ack(message.topic, "unknown-ref"))


@pytest.fixture
async def server() -> AsyncIterator[FakeServer]:
    async with FakeServer() as server:
        yield server


@pytest.mark.asyncio
async def test_close_with_join_ref_after_leave_keeps_client_alive(
    server: FakeServer,
) -> None:
    async with connect_once(server.url, get_token) as client, client.channel("held"):
        async with client.channel("first"):
            pass
        async with client.channel("second") as channel:
            assert channel.joined
        assert not connection_failure(client).done()
        assert client.message_refs == {}


@pytest.mark.asyncio
async def test_orphan_reply_is_not_forwarded_to_the_channel(server: FakeServer) -> None:
    async with connect_once(server.url, get_token) as client:
        channel = client.channel("room")
        await channel.subscribe()
        await channel.socket._send_no_wait(
            Message(topic=channel.topic, event=ChannelEvents.leave, payload={}, ref="x")
        )
        await asyncio.sleep(0.1)
        queued = []
        while not channel.message_stream.empty():
            queued.append(channel.message_stream.get_nowait())
        assert all(message.event != ChannelEvents.reply for message in queued)
        assert any(message.event == ChannelEvents.close for message in queued)
        assert not connection_failure(client).done()


@pytest.mark.asyncio
async def test_late_reply_for_timed_out_send_keeps_client_alive(
    server: FakeServer,
) -> None:
    server.join_reply_delay = 0.2
    async with connect_once(server.url, get_token) as client:
        with pytest.raises(asyncio.TimeoutError):
            await asyncio.wait_for(client.channel("slow").subscribe(), timeout=0.05)

        server.join_reply_delay = 0
        await asyncio.sleep(0.3)
        async with client.channel("fast") as channel:
            assert channel.joined
        assert not connection_failure(client).done()


@pytest.mark.asyncio
async def test_unsubscribe_delivers_a_single_close(server: FakeServer) -> None:
    async with connect_once(server.url, get_token) as client:
        channel = client.channel("room")
        await channel.subscribe()
        await channel.unsubscribe()
        await asyncio.sleep(0.1)

        closes = []
        while not channel.message_stream.empty():
            message = channel.message_stream.get_nowait()
            if message.event == ChannelEvents.close:
                closes.append(message)
        assert len(closes) == 1
