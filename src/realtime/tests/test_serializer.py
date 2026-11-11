import json
from collections.abc import AsyncIterator

import pytest
from pydantic import ValidationError
from websockets.asyncio.server import Server, ServerConnection, serve
from websockets.exceptions import ConnectionClosed

from realtime._serializer import decode, encode
from realtime.channel import RealtimeChannelOptions
from realtime.client import connect_once
from realtime.message import BroadcastMessage, Message
from realtime.types import ChannelEvents

HOST = "127.0.0.1"


def user_broadcast_frame(
    topic: bytes,
    event: bytes,
    body: bytes,
    encoding: int,
    metadata: bytes = b"",
) -> bytes:
    header = bytes([4, len(topic), len(event), len(metadata), encoding])
    return header + topic + event + metadata + body


def test_encode_writes_a_json_array() -> None:
    message = Message(
        topic="realtime:room",
        event=ChannelEvents.join,
        payload={"config": {"private": False}},
        ref="1",
        join_ref="1",
    )

    frame = encode(message)

    assert isinstance(frame, str)
    assert json.loads(frame) == [
        "1",
        "1",
        "realtime:room",
        "phx_join",
        {"config": {"private": False}},
    ]


def test_encode_keeps_a_json_broadcast_as_text() -> None:
    message = Message(
        topic="realtime:room",
        event=ChannelEvents.broadcast,
        payload={"type": "broadcast", "event": "cursor", "payload": {"x": 1}},
        ref="2",
        join_ref="1",
    )

    frame = encode(message)

    assert isinstance(frame, str)
    assert json.loads(frame)[4] == message.payload


def test_encode_writes_a_binary_broadcast_as_user_broadcast_push() -> None:
    message = Message(
        topic="realtime:röom",
        event=ChannelEvents.broadcast,
        payload={"type": "broadcast", "event": "ëvent", "payload": b"\x00\xff"},
        ref="12",
        join_ref="1",
    )

    frame = encode(message)

    topic = "realtime:röom".encode()
    event = "ëvent".encode()
    assert frame == (
        bytes([3, 1, 2, len(topic), len(event), 0, 0])
        + b"1"
        + b"12"
        + topic
        + event
        + b"\x00\xff"
    )


def test_encode_writes_empty_refs_of_an_unjoined_binary_broadcast() -> None:
    message = Message(
        topic="t",
        event=ChannelEvents.broadcast,
        payload={"type": "broadcast", "event": "e", "payload": b""},
    )

    assert encode(message) == bytes([3, 0, 0, 1, 1, 0, 0]) + b"t" + b"e"


def test_encode_rejects_a_binary_broadcast_field_over_255_bytes() -> None:
    message = Message(
        topic="realtime:room",
        event=ChannelEvents.broadcast,
        payload={"type": "broadcast", "event": "é" * 128, "payload": b"data"},
    )

    with pytest.raises(ValueError, match="user_event is 256 bytes long"):
        encode(message)


def test_decode_reads_a_json_array() -> None:
    message = decode('[null,"3","phoenix","phx_reply",{"status":"ok","response":{}}]')

    assert message == Message(
        join_ref=None,
        ref="3",
        topic="phoenix",
        event="phx_reply",
        payload={"status": "ok", "response": {}},
    )


@pytest.mark.parametrize(
    "frame",
    [
        '{"topic":"phoenix","event":"phx_reply","payload":{},"ref":"1"}',
        '[null,"1","phoenix","phx_reply"]',
        "not json",
    ],
)
def test_decode_rejects_a_text_frame_that_is_not_a_message_array(frame: str) -> None:
    with pytest.raises(ValidationError):
        decode(frame)


def test_decode_reads_a_user_broadcast_with_a_json_payload() -> None:
    frame = user_broadcast_frame(
        "realtime:röom".encode(), b"cursor", b'{"x":1}', encoding=1
    )

    message = decode(frame)

    assert message == Message(
        topic="realtime:röom",
        event="broadcast",
        payload={"type": "broadcast", "event": "cursor", "payload": {"x": 1}},
    )


def test_decode_reads_a_user_broadcast_with_a_binary_payload_and_metadata() -> None:
    frame = user_broadcast_frame(
        b"realtime:room",
        b"blob",
        b"\x00\xff",
        encoding=0,
        metadata=b'{"id":"abc"}',
    )

    message = decode(frame)

    assert message.payload == {
        "type": "broadcast",
        "event": "blob",
        "payload": b"\x00\xff",
        "meta": {"id": "abc"},
    }


@pytest.mark.parametrize(
    ("frame", "error"),
    [
        (b"", "empty binary frame"),
        (bytes([2, 0, 0]), "unknown binary frame kind 2"),
        (bytes([4, 5, 0, 0]), "truncated user broadcast frame"),
        (bytes([4, 5, 0, 0, 0]) + b"top", "truncated user broadcast frame"),
        (user_broadcast_frame(b"t", b"e", b"", encoding=7), "unknown user broadcast"),
    ],
)
def test_decode_rejects_a_malformed_binary_frame(frame: bytes, error: str) -> None:
    with pytest.raises(ValueError, match=error):
        decode(frame)


class BroadcastServer:
    """Acks every ref'd message, records binary frames and echoes binary broadcasts."""

    def __init__(self) -> None:
        self.ws_server: Server | None = None
        self.url = ""
        self.binary_frames: list[bytes] = []

    async def __aenter__(self) -> "BroadcastServer":
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
        try:
            async for frame in connection:
                if isinstance(frame, bytes):
                    self.binary_frames.append(frame)
                    ref, topic, event, body = read_user_broadcast_push(frame)
                    await connection.send(b"\x09unknown kind")
                    await connection.send(
                        user_broadcast_frame(topic, event, body, encoding=0)
                    )
                else:
                    message = decode(frame)
                    ref, topic = message.ref or "", message.topic.encode()
                if ref:
                    reply = Message(
                        event=ChannelEvents.reply,
                        topic=topic.decode(),
                        ref=ref,
                        payload={"status": "ok", "response": {}},
                    )
                    await connection.send(encode(reply))
        except ConnectionClosed:
            pass


def read_user_broadcast_push(frame: bytes) -> tuple[str, bytes, bytes, bytes]:
    join_ref_size, ref_size, topic_size, event_size = frame[1:5]
    offset = 7 + join_ref_size
    ref = frame[offset : offset + ref_size].decode()
    offset += ref_size
    topic = frame[offset : offset + topic_size]
    offset += topic_size
    event = frame[offset : offset + event_size]
    return ref, topic, event, frame[offset + event_size :]


@pytest.fixture
async def server() -> AsyncIterator[BroadcastServer]:
    async with BroadcastServer() as server:
        yield server


@pytest.mark.parametrize("ack", [False, True])
async def test_binary_broadcast_round_trip(server: BroadcastServer, ack: bool) -> None:
    options = RealtimeChannelOptions().broadcast(ack=ack)
    async with (
        connect_once(server.url) as client,
        client.channel("room", options) as channel,
    ):
        reply = await channel.send_broadcast("blob", b"\x00\x01\xff")

        message = await channel.messages.__anext__()

        assert (reply is not None) == ack
        assert isinstance(message, BroadcastMessage)
        assert message.payload.event == "blob"
        assert message.payload.payload == b"\x00\x01\xff"
        assert not client._connection_failure.done()

    [frame] = server.binary_frames
    assert frame[0] == 3
    assert frame.endswith(b"realtime:roomblob\x00\x01\xff")
