"""
Serializer for Realtime V2 protocol.

This module implements binary encoding/decoding for Realtime V2 serializer,
supporting binary payloads and user broadcast messages with metadata.

Based on supabase-js PRs #1829 and #1894.
"""
from __future__ import annotations

import json
from typing import Any, Dict, List, Optional, Union

from .types import ChannelEvents


class Serializer:
    """
    Serializer for Realtime messages supporting both V1 (JSON) and V2 (binary) formats.
    
    V2 features:
    - Binary payload support for user messages
    - Two new message types: user broadcast and user broadcast push
    - Optional metadata support for user broadcast push messages
    - Reduced JSON encoding overhead on the server side
    """

    HEADER_LENGTH = 1
    META_LENGTH = 4
    USER_BROADCAST_PUSH_META_LENGTH = 6
    
    # Message kinds
    KINDS = {
        "push": 0,
        "reply": 1,
        "broadcast": 2,
        "userBroadcastPush": 3,
        "userBroadcast": 4,
    }
    
    # Encoding types
    BINARY_ENCODING = 0
    JSON_ENCODING = 1
    
    BROADCAST_EVENT = "broadcast"

    def __init__(self, allowed_metadata_keys: Optional[List[str]] = None) -> None:
        """
        Initialize the serializer.
        
        Args:
            allowed_metadata_keys: List of metadata keys allowed in user broadcast push messages.
                                  If None or empty, no metadata will be included.
        """
        self.allowed_metadata_keys = allowed_metadata_keys or []

    def encode(
        self,
        msg: Dict[str, Any],
    ) -> Union[bytes, str]:
        """
        Encode a message to either JSON string (V1) or binary (V2).
        
        Args:
            msg: Message dictionary with keys: join_ref, ref, topic, event, payload
            
        Returns:
            JSON string for V1 or bytes for V2 binary encoding
        """
        payload = msg.get("payload")
        
        # Check if payload is bytes/bytearray (binary)
        if isinstance(payload, (bytes, bytearray)):
            return self._binary_encode_push(msg)
        
        # Check if this is a user broadcast push message
        if (
            msg.get("event") == self.BROADCAST_EVENT
            and isinstance(payload, dict)
            and "event" in payload
        ):
            return self._encode_user_broadcast_push(msg)
        
        # Default: JSON encoding (V1)
        return json.dumps([
            msg.get("join_ref"),
            msg.get("ref"),
            msg.get("topic"),
            msg.get("event"),
            payload,
        ], separators=(',', ':'))

    def _binary_encode_push(self, message: Dict[str, Any]) -> bytes:
        """
        Encode a push message with binary payload.
        
        Format:
        - 1 byte: kind (push = 0)
        - 1 byte: join_ref length
        - 1 byte: ref length (0 for push)
        - 1 byte: topic length
        - 1 byte: event length
        - N bytes: join_ref (UTF-8)
        - N bytes: topic (UTF-8)
        - N bytes: event (UTF-8)
        - N bytes: binary payload
        """
        join_ref = message.get("join_ref", "") or ""
        ref = message.get("ref", "") or ""
        topic = message.get("topic", "")
        event = message.get("event", "")
        payload = message.get("payload", b"")
        
        if isinstance(payload, bytearray):
            payload = bytes(payload)
        elif not isinstance(payload, bytes):
            payload = bytes(payload)
        
        meta_length = (
            self.META_LENGTH
            + len(join_ref)
            + len(ref)
            + len(topic)
            + len(event)
        )
        
        header = bytearray(self.HEADER_LENGTH + meta_length)
        offset = 0
        
        header[offset] = self.KINDS["push"]
        offset += 1
        header[offset] = len(join_ref)
        offset += 1
        header[offset] = len(ref)
        offset += 1
        header[offset] = len(topic)
        offset += 1
        header[offset] = len(event)
        offset += 1
        
        # Write strings as UTF-8
        header[offset:offset + len(join_ref)] = join_ref.encode("utf-8")
        offset += len(join_ref)
        header[offset:offset + len(ref)] = ref.encode("utf-8")
        offset += len(ref)
        header[offset:offset + len(topic)] = topic.encode("utf-8")
        offset += len(topic)
        header[offset:offset + len(event)] = event.encode("utf-8")
        offset += len(event)
        
        # Combine header and payload
        return bytes(header) + payload

    def _encode_user_broadcast_push(self, message: Dict[str, Any]) -> bytes:
        """
        Encode a user broadcast push message.
        
        Supports both JSON and binary payloads, with optional metadata.
        """
        payload = message.get("payload", {})
        user_payload = payload.get("payload")
        
        if isinstance(user_payload, (bytes, bytearray)):
            return self._encode_binary_user_broadcast_push(message)
        else:
            return self._encode_json_user_broadcast_push(message)

    def _encode_binary_user_broadcast_push(self, message: Dict[str, Any]) -> bytes:
        """Encode user broadcast push with binary payload."""
        user_payload = message.get("payload", {}).get("payload", b"")
        if isinstance(user_payload, bytearray):
            user_payload = bytes(user_payload)
        elif not isinstance(user_payload, bytes):
            user_payload = bytes(user_payload)
        
        return self._encode_user_broadcast_push_internal(
            message, self.BINARY_ENCODING, user_payload
        )

    def _encode_json_user_broadcast_push(self, message: Dict[str, Any]) -> bytes:
        """Encode user broadcast push with JSON payload."""
        user_payload = message.get("payload", {}).get("payload", {})
        encoded_payload = json.dumps(user_payload).encode("utf-8")
        return self._encode_user_broadcast_push_internal(
            message, self.JSON_ENCODING, encoded_payload
        )

    def _encode_user_broadcast_push_internal(
        self,
        message: Dict[str, Any],
        encoding_type: int,
        encoded_payload: bytes,
    ) -> bytes:
        """
        Internal method to encode user broadcast push messages.
        
        Format:
        - 1 byte: kind (userBroadcastPush = 3)
        - 1 byte: join_ref length
        - 1 byte: ref length
        - 1 byte: topic length
        - 1 byte: user_event length
        - 1 byte: metadata length
        - 1 byte: encoding type (0 = binary, 1 = JSON)
        - N bytes: join_ref (UTF-8)
        - N bytes: ref (UTF-8)
        - N bytes: topic (UTF-8)
        - N bytes: user_event (UTF-8)
        - N bytes: metadata (UTF-8 JSON, if present)
        - N bytes: encoded payload
        """
        topic = message.get("topic", "")
        ref = message.get("ref", "") or ""
        join_ref = message.get("join_ref", "") or ""
        payload = message.get("payload", {})
        user_event = payload.get("event", "")
        
        # Filter metadata based on allowed keys (exclude special fields: type, event, payload)
        rest = self._pick(payload, self.allowed_metadata_keys)
        # Remove special fields that shouldn't be in metadata
        rest = {k: v for k, v in rest.items() if k not in ("type", "event", "payload")}
        metadata = json.dumps(rest) if rest else ""
        
        # Validate lengths don't exceed uint8 max value (255)
        if len(join_ref) > 255:
            raise ValueError(f"joinRef length {len(join_ref)} exceeds maximum of 255")
        if len(ref) > 255:
            raise ValueError(f"ref length {len(ref)} exceeds maximum of 255")
        if len(topic) > 255:
            raise ValueError(f"topic length {len(topic)} exceeds maximum of 255")
        if len(user_event) > 255:
            raise ValueError(f"userEvent length {len(user_event)} exceeds maximum of 255")
        if len(metadata) > 255:
            raise ValueError(f"metadata length {len(metadata)} exceeds maximum of 255")
        
        meta_length = (
            self.USER_BROADCAST_PUSH_META_LENGTH
            + len(join_ref)
            + len(ref)
            + len(topic)
            + len(user_event)
            + len(metadata)
        )
        
        header = bytearray(self.HEADER_LENGTH + meta_length)
        offset = 0
        
        header[offset] = self.KINDS["userBroadcastPush"]
        offset += 1
        header[offset] = len(join_ref)
        offset += 1
        header[offset] = len(ref)
        offset += 1
        header[offset] = len(topic)
        offset += 1
        header[offset] = len(user_event)
        offset += 1
        header[offset] = len(metadata)
        offset += 1
        header[offset] = encoding_type
        offset += 1
        
        # Write strings as UTF-8
        header[offset:offset + len(join_ref)] = join_ref.encode("utf-8")
        offset += len(join_ref)
        header[offset:offset + len(ref)] = ref.encode("utf-8")
        offset += len(ref)
        header[offset:offset + len(topic)] = topic.encode("utf-8")
        offset += len(topic)
        header[offset:offset + len(user_event)] = user_event.encode("utf-8")
        offset += len(user_event)
        header[offset:offset + len(metadata)] = metadata.encode("utf-8")
        offset += len(metadata)
        
        # Combine header and payload
        return bytes(header) + encoded_payload

    def decode(self, raw_payload: Union[bytes, str]) -> Dict[str, Any]:
        """
        Decode a message from either JSON string (V1) or binary (V2).
        
        Args:
            raw_payload: JSON string or bytes to decode
            
        Returns:
            Decoded message dictionary
        """
        if isinstance(raw_payload, bytes):
            return self._binary_decode(raw_payload)
        
        if isinstance(raw_payload, str):
            json_payload = json.loads(raw_payload)
            join_ref, ref, topic, event, payload = json_payload
            return {
                "join_ref": join_ref,
                "ref": ref,
                "topic": topic,
                "event": event,
                "payload": payload,
            }
        
        return {}

    def _binary_decode(self, buffer: bytes) -> Dict[str, Any]:
        """Decode a binary message based on its kind."""
        if len(buffer) == 0:
            return {}
        
        kind = buffer[0]
        
        if kind == self.KINDS["push"]:
            return self._decode_push(buffer)
        elif kind == self.KINDS["reply"]:
            return self._decode_reply(buffer)
        elif kind == self.KINDS["broadcast"]:
            return self._decode_broadcast(buffer)
        elif kind == self.KINDS["userBroadcast"]:
            return self._decode_user_broadcast(buffer)
        else:
            return {}

    def _decode_push(self, buffer: bytes) -> Dict[str, Any]:
        """Decode a push message."""
        if len(buffer) < self.HEADER_LENGTH + self.META_LENGTH - 1:
            return {}
        
        join_ref_size = buffer[1]
        topic_size = buffer[2]
        event_size = buffer[3]
        
        offset = self.HEADER_LENGTH + self.META_LENGTH - 1  # pushes have no ref
        
        join_ref = buffer[offset:offset + join_ref_size].decode("utf-8")
        offset += join_ref_size
        
        topic = buffer[offset:offset + topic_size].decode("utf-8")
        offset += topic_size
        
        event = buffer[offset:offset + event_size].decode("utf-8")
        offset += event_size
        
        data = json.loads(buffer[offset:].decode("utf-8"))
        
        return {
            "join_ref": join_ref,
            "ref": None,
            "topic": topic,
            "event": event,
            "payload": data,
        }

    def _decode_reply(self, buffer: bytes) -> Dict[str, Any]:
        """Decode a reply message."""
        if len(buffer) < self.HEADER_LENGTH + self.META_LENGTH:
            return {}
        
        join_ref_size = buffer[1]
        ref_size = buffer[2]
        topic_size = buffer[3]
        event_size = buffer[4]
        
        offset = self.HEADER_LENGTH + self.META_LENGTH
        
        join_ref = buffer[offset:offset + join_ref_size].decode("utf-8")
        offset += join_ref_size
        
        ref = buffer[offset:offset + ref_size].decode("utf-8")
        offset += ref_size
        
        topic = buffer[offset:offset + topic_size].decode("utf-8")
        offset += topic_size
        
        event = buffer[offset:offset + event_size].decode("utf-8")
        offset += event_size
        
        data = json.loads(buffer[offset:].decode("utf-8"))
        payload = {"status": event, "response": data}
        
        return {
            "join_ref": join_ref,
            "ref": ref,
            "topic": topic,
            "event": ChannelEvents.reply,
            "payload": payload,
        }

    def _decode_broadcast(self, buffer: bytes) -> Dict[str, Any]:
        """Decode a broadcast message."""
        if len(buffer) < self.HEADER_LENGTH + 2:
            return {}
        
        topic_size = buffer[1]
        event_size = buffer[2]
        
        offset = self.HEADER_LENGTH + 2  # kind(1) + topic_len(1) + event_len(1) = 3, but offset is after reading lengths
        
        topic = buffer[offset:offset + topic_size].decode("utf-8")
        offset += topic_size
        
        event = buffer[offset:offset + event_size].decode("utf-8")
        offset += event_size
        
        data = json.loads(buffer[offset:].decode("utf-8"))
        
        return {
            "join_ref": None,
            "ref": None,
            "topic": topic,
            "event": event,
            "payload": data,
        }

    def _decode_user_broadcast(self, buffer: bytes) -> Dict[str, Any]:
        """
        Decode a user broadcast message.
        
        Supports both JSON and binary payloads, with optional metadata.
        """
        if len(buffer) < self.HEADER_LENGTH + 4:
            return {}
        
        topic_size = buffer[1]
        user_event_size = buffer[2]
        metadata_size = buffer[3]
        payload_encoding = buffer[4]
        
        offset = self.HEADER_LENGTH + 4
        
        topic = buffer[offset:offset + topic_size].decode("utf-8")
        offset += topic_size
        
        user_event = buffer[offset:offset + user_event_size].decode("utf-8")
        offset += user_event_size
        
        metadata = buffer[offset:offset + metadata_size].decode("utf-8") if metadata_size > 0 else ""
        offset += metadata_size
        
        payload = buffer[offset:]
        
        if payload_encoding == self.JSON_ENCODING:
            parsed_payload = json.loads(payload.decode("utf-8"))
        else:
            parsed_payload = payload
        
        data: Dict[str, Any] = {
            "type": self.BROADCAST_EVENT,
            "event": user_event,
            "payload": parsed_payload,
        }
        
        # Metadata is optional and always JSON encoded
        if metadata_size > 0:
            data["meta"] = json.loads(metadata)
        
        return {
            "join_ref": None,
            "ref": None,
            "topic": topic,
            "event": self.BROADCAST_EVENT,
            "payload": data,
        }

    def _pick(self, obj: Optional[Dict[str, Any]], keys: List[str]) -> Dict[str, Any]:
        """
        Pick specific keys from a dictionary.
        
        Args:
            obj: Dictionary to pick from
            keys: List of keys to pick
            
        Returns:
            Dictionary containing only the specified keys
        """
        if not obj or not isinstance(obj, dict):
            return {}
        return {key: obj[key] for key in keys if key in obj}
