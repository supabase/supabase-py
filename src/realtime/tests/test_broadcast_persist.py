import json
from collections.abc import AsyncIterator
from typing import Self

import pytest
from supabase_utils.types import JSON
from websockets.asyncio.server import Server, ServerConnection, serve

from realtime import BroadcastPersistence, PushRejectedError, RealtimeChannelOptions
from realtime._serializer import decode, encode
from realtime.client import connect_once
from realtime.message import Message
from realtime.types import ChannelEvents

HOST = "127.0.0.1"


async def get_token() -> str:
    return "my-publishable-key"


JOIN_REPLY: dict[str, JSON] = {"status": "ok", "response": {"postgres_changes": []}}


class RecordingServer:
    def __init__(self, broadcast_reply: dict[str, JSON] | None = None) -> None:
        self.broadcast_reply = broadcast_reply or {"status": "ok", "response": {}}
        self.broadcasts: list[str | bytes] = []
        self.ws_server: Server | None = None
        self.url = ""

    async def __aenter__(self) -> Self:
        self.ws_server = await serve(self.handler, HOST, 0)
        port = next(iter(self.ws_server.sockets)).getsockname()[1]
        self.url = f"http://{HOST}:{port}"
        return self

    async def __aexit__(self, *exc: object) -> None:
        assert self.ws_server is not None
        self.ws_server.close()
        await self.ws_server.wait_closed()

    async def handler(self, connection: ServerConnection) -> None:
        async for raw in connection:
            if isinstance(raw, bytes):
                self.broadcasts.append(raw)
                topic, ref = _topic_and_ref(raw)
                payload = self.broadcast_reply
            else:
                message = decode(raw)
                topic, ref = message.topic, message.ref
                if message.event == ChannelEvents.broadcast:
                    self.broadcasts.append(raw)
                    payload = self.broadcast_reply
                else:
                    payload = JOIN_REPLY
            if not ref:
                continue
            reply = Message(
                event=ChannelEvents.reply, topic=topic, ref=ref, payload=payload
            )
            await connection.send(encode(reply))


def _fields(frame: bytes) -> list[bytes]:
    fields: list[bytes] = []
    offset = 7
    for size in frame[1:6]:
        fields.append(frame[offset : offset + size])
        offset += size
    fields.append(frame[offset:])
    return fields


def _topic_and_ref(frame: bytes) -> tuple[str, str]:
    _, ref, topic, *_ = _fields(frame)
    return topic.decode(), ref.decode()


def _metadata_and_body(frame: bytes) -> tuple[JSON, int, bytes]:
    *_, metadata, body = _fields(frame)
    return json.loads(metadata), frame[6], body


@pytest.fixture
async def server() -> AsyncIterator[RecordingServer]:
    async with RecordingServer() as server:
        yield server


PRIVATE = RealtimeChannelOptions().private(True)


@pytest.mark.parametrize(
    ("persist", "metadata"),
    [
        (BroadcastPersistence(), {"persist": True}),
        (BroadcastPersistence(ttl=3600), {"persist": {"ttl": 3600}}),
        (BroadcastPersistence(ttl=0), {"persist": {"ttl": 0}}),
    ],
)
async def test_send_broadcast_sends_persist_as_frame_metadata(
    server: RecordingServer, persist: BroadcastPersistence, metadata: JSON
) -> None:
    async with connect_once(server.url, get_token) as client:
        channel = client.channel("room", PRIVATE)
        await channel.subscribe()

        await channel.send_broadcast("event", {"a": 1}, persist=persist)

    [frame] = server.broadcasts
    assert isinstance(frame, bytes)
    sent_metadata, encoding, body = _metadata_and_body(frame)
    assert sent_metadata == metadata
    assert encoding == 1
    assert json.loads(body) == {"a": 1}


async def test_send_broadcast_sends_persist_with_a_binary_payload(
    server: RecordingServer,
) -> None:
    async with connect_once(server.url, get_token) as client:
        channel = client.channel("room", PRIVATE)
        await channel.subscribe()

        await channel.send_broadcast(
            "event", b"\x00\xff", persist=BroadcastPersistence(ttl=60)
        )

    [frame] = server.broadcasts
    assert isinstance(frame, bytes)
    assert _metadata_and_body(frame) == ({"persist": {"ttl": 60}}, 0, b"\x00\xff")


async def test_send_broadcast_without_persist_keeps_json_as_text(
    server: RecordingServer,
) -> None:
    async with connect_once(server.url, get_token) as client:
        channel = client.channel("room", PRIVATE)
        await channel.subscribe()

        await channel.send_broadcast("event", {"persist": True})

    [frame] = server.broadcasts
    assert isinstance(frame, str)
    assert json.loads(frame)[4] == {
        "type": "broadcast",
        "event": "event",
        "payload": {"persist": True},
    }


async def test_send_broadcast_refuses_persist_on_a_public_channel(
    server: RecordingServer,
) -> None:
    async with connect_once(server.url, get_token) as client:
        channel = client.channel("room")
        await channel.subscribe()

        with pytest.raises(ValueError, match="private channel"):
            await channel.send_broadcast(
                "event", {"a": 1}, persist=BroadcastPersistence()
            )

    assert server.broadcasts == []


@pytest.mark.parametrize(
    "code",
    ["persistence_unauthorized", "persistence_failed", "persistence_invalid_ttl"],
)
async def test_acknowledged_send_broadcast_raises_the_persistence_error_code(
    code: str,
) -> None:
    reply: dict[str, JSON] = {"status": "error", "response": {"error": code}}
    async with (
        RecordingServer(broadcast_reply=reply) as server,
        connect_once(server.url, get_token) as client,
    ):
        channel = client.channel("room", PRIVATE.broadcast(ack=True))
        await channel.subscribe()

        with pytest.raises(PushRejectedError, match=code) as error:
            await channel.send_broadcast(
                "event", {"a": 1}, persist=BroadcastPersistence()
            )

    assert error.value.code == code
    assert error.value.reason is None


async def test_acknowledged_send_broadcast_returns_the_reply_when_stored() -> None:
    reply: dict[str, JSON] = {"status": "ok", "response": {"id": "message-id"}}
    async with (
        RecordingServer(broadcast_reply=reply) as server,
        connect_once(server.url, get_token) as client,
    ):
        channel = client.channel("room", PRIVATE.broadcast(ack=True))
        await channel.subscribe()

        result = await channel.send_broadcast(
            "event", {"a": 1}, persist=BroadcastPersistence()
        )

    assert result is not None
    assert result.payload.status == "ok"
