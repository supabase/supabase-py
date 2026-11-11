"""Encode and decode the frames of the Realtime protocol 2.0.0.

Text frames hold the JSON array ``[join_ref, ref, topic, event, payload]``.
A broadcast whose payload is ``bytes`` is sent as a binary ``user broadcast
push`` frame, and the server sends broadcasts to the client as binary
``user broadcast`` frames, with either a JSON or a binary payload.
"""

import json
from typing import TYPE_CHECKING, Any

from pydantic import TypeAdapter

from .message import Message
from .types import ChannelEvents

if TYPE_CHECKING:
    from supabase_utils.types import JSON

_USER_BROADCAST_PUSH = 3
_USER_BROADCAST = 4
_BINARY_ENCODING = 0
_JSON_ENCODING = 1
_USER_BROADCAST_HEADER_LENGTH = 5
_MAX_FIELD_LENGTH = 255

type _TextFrame = tuple[str | None, str | None, str, str, Any]
_TextFrameAdapter: TypeAdapter[_TextFrame] = TypeAdapter(_TextFrame)


def encode(message: Message) -> str | bytes:
    payload = message.payload
    user_event = payload.get("event")
    user_payload = payload.get("payload")
    if (
        message.event == ChannelEvents.broadcast
        and isinstance(user_event, str)
        and isinstance(user_payload, bytes)
    ):
        return _encode_user_broadcast_push(message, user_event, user_payload)
    frame = (message.join_ref, message.ref, message.topic, message.event, payload)
    return _TextFrameAdapter.dump_json(frame).decode()


def decode(frame: str | bytes) -> Message:
    """Decode a frame, raising `ValueError` when it is malformed."""
    if isinstance(frame, str):
        join_ref, ref, topic, event, payload = _TextFrameAdapter.validate_json(frame)
        return Message(
            join_ref=join_ref, ref=ref, topic=topic, event=event, payload=payload
        )
    if not frame:
        raise ValueError("empty binary frame")
    if frame[0] != _USER_BROADCAST:
        raise ValueError(f"unknown binary frame kind {frame[0]}")
    return _decode_user_broadcast(frame)


def _encode_user_broadcast_push(
    message: Message, user_event: str, user_payload: bytes
) -> bytes:
    fields = {
        "join_ref": (message.join_ref or "").encode(),
        "ref": (message.ref or "").encode(),
        "topic": message.topic.encode(),
        "user_event": user_event.encode(),
    }
    for name, value in fields.items():
        if len(value) > _MAX_FIELD_LENGTH:
            raise ValueError(
                f"{name} is {len(value)} bytes long, the maximum is {_MAX_FIELD_LENGTH}"
            )
    header = bytes(
        [
            _USER_BROADCAST_PUSH,
            *(len(value) for value in fields.values()),
            0,
            _BINARY_ENCODING,
        ]
    )
    return b"".join([header, *fields.values(), user_payload])


def _decode_user_broadcast(frame: bytes) -> Message:
    if len(frame) < _USER_BROADCAST_HEADER_LENGTH:
        raise ValueError("truncated user broadcast frame")
    topic_size, user_event_size, metadata_size, encoding = frame[1:5]
    offset = _USER_BROADCAST_HEADER_LENGTH
    topic, offset = _read(frame, offset, topic_size)
    user_event, offset = _read(frame, offset, user_event_size)
    metadata, offset = _read(frame, offset, metadata_size)
    body = frame[offset:]

    user_payload: JSON | bytes
    if encoding == _JSON_ENCODING:
        user_payload = json.loads(body)
    elif encoding == _BINARY_ENCODING:
        user_payload = body
    else:
        raise ValueError(f"unknown user broadcast payload encoding {encoding}")

    payload: dict[str, JSON | bytes] = {
        "type": ChannelEvents.broadcast.value,
        "event": user_event.decode(),
        "payload": user_payload,
    }
    if metadata:
        payload["meta"] = json.loads(metadata)
    return Message(
        topic=topic.decode(), event=ChannelEvents.broadcast.value, payload=payload
    )


def _read(frame: bytes, offset: int, size: int) -> tuple[bytes, int]:
    end = offset + size
    if end > len(frame):
        raise ValueError("truncated user broadcast frame")
    return frame[offset:end], end
