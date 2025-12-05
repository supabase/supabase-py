"""
Tests for Realtime V2 serializer.

Based on supabase-js PRs #1829 and #1894.
"""
import json
import pytest

from realtime.serializer import Serializer
from realtime.types import ChannelEvents


def test_json_encode():
    """Test JSON encoding (V1 format)."""
    serializer = Serializer()
    msg = {
        "join_ref": "0",
        "ref": "1",
        "topic": "t",
        "event": "e",
        "payload": {"foo": 1},
    }
    result = serializer.encode(msg)
    assert result == '["0","1","t","e",{"foo":1}]'


def test_json_decode():
    """Test JSON decoding (V1 format)."""
    serializer = Serializer()
    result = serializer.decode('["0","1","t","e",{"foo":1}]')
    assert result == {
        "join_ref": "0",
        "ref": "1",
        "topic": "t",
        "event": "e",
        "payload": {"foo": 1},
    }


def test_binary_encode_push():
    """Test binary encoding of push message with binary payload."""
    serializer = Serializer()
    buffer = bytes([1, 4])
    msg = {
        "join_ref": "0",
        "ref": "1",
        "topic": "t",
        "event": "e",
        "payload": buffer,
    }
    result = serializer.encode(msg)
    assert isinstance(result, bytes)
    # Verify structure: kind (0), join_ref_len (1), ref_len (1), topic_len (1), event_len (1)
    assert result[0] == 0  # push kind
    assert result[1] == 1  # join_ref length
    assert result[2] == 1  # ref length
    assert result[3] == 1  # topic length
    assert result[4] == 1  # event length
    # Verify payload is at the end
    assert result[-2:] == buffer


def test_binary_encode_push_variable_length():
    """Test binary encoding with variable length segments."""
    serializer = Serializer()
    buffer = bytes([1, 4])
    msg = {
        "join_ref": "10",
        "ref": "1",
        "topic": "top",
        "event": "ev",
        "payload": buffer,
    }
    result = serializer.encode(msg)
    assert isinstance(result, bytes)
    assert result[0] == 0  # push kind
    assert result[1] == 2  # join_ref length
    assert result[2] == 1  # ref length
    assert result[3] == 3  # topic length
    assert result[4] == 2  # event length


def test_encode_user_broadcast_push_json():
    """Test encoding user broadcast push with JSON payload."""
    serializer = Serializer()
    msg = {
        "join_ref": "10",
        "ref": "1",
        "topic": "top",
        "event": "broadcast",
        "payload": {
            "type": "broadcast",
            "event": "user-event",
            "payload": {"a": "b"},
        },
    }
    result = serializer.encode(msg)
    assert isinstance(result, bytes)
    # Verify structure: kind (3), join_ref_len, ref_len, topic_len, user_event_len, metadata_len, encoding
    assert result[0] == 3  # userBroadcastPush kind
    assert result[1] == 2  # join_ref length
    assert result[2] == 1  # ref length
    assert result[3] == 3  # topic length
    assert result[4] == 10  # user_event length
    assert result[5] == 0  # metadata length (no metadata)
    assert result[6] == 1  # JSON encoding


def test_encode_user_broadcast_push_json_with_metadata():
    """Test encoding user broadcast push with JSON payload and metadata."""
    serializer = Serializer(allowed_metadata_keys=["extra"])
    msg = {
        "join_ref": "10",
        "ref": "1",
        "topic": "top",
        "event": "broadcast",
        "payload": {
            "type": "broadcast",
            "event": "user-event",
            "extra": "bit",
            "store": True,  # Not in allowed keys, should be filtered
            "payload": {"a": "b"},
        },
    }
    result = serializer.encode(msg)
    assert isinstance(result, bytes)
    assert result[0] == 3  # userBroadcastPush kind
    assert result[5] > 0  # metadata length (should have metadata)
    # Verify metadata contains "extra" but not "store"
    # Format: kind(1) + join_ref_len(1) + ref_len(1) + topic_len(1) + user_event_len(1) + metadata_len(1) + encoding(1) = 7 bytes header
    # Then: join_ref(2) + ref(1) + topic(3) + user_event(10) = 16 bytes
    # So metadata starts at: 7 + 16 = 23
    header_len = 7
    join_ref_len = result[1]
    ref_len = result[2]
    topic_len = result[3]
    user_event_len = result[4]
    metadata_start = header_len + join_ref_len + ref_len + topic_len + user_event_len
    metadata_len = result[5]
    metadata_bytes = result[metadata_start:metadata_start + metadata_len]
    metadata = json.loads(metadata_bytes.decode("utf-8"))
    assert "extra" in metadata
    assert metadata["extra"] == "bit"
    assert "store" not in metadata


def test_encode_user_broadcast_push_binary():
    """Test encoding user broadcast push with binary payload."""
    serializer = Serializer()
    buffer = bytes([1, 4])
    msg = {
        "join_ref": "10",
        "ref": "1",
        "topic": "top",
        "event": "broadcast",
        "payload": {
            "type": "broadcast",
            "event": "user-event",
            "payload": buffer,
        },
    }
    result = serializer.encode(msg)
    assert isinstance(result, bytes)
    assert result[0] == 3  # userBroadcastPush kind
    assert result[6] == 0  # binary encoding
    # Verify binary payload is at the end
    assert result[-2:] == buffer


def test_decode_push():
    """Test decoding push message."""
    serializer = Serializer()
    # Create binary message: kind=0, join_ref_len=3, topic_len=3, event_len=10, then strings, then JSON payload
    bin_data = b'\x00\x03\x03\n123topsome-event{"a":"b"}'
    result = serializer.decode(bin_data)
    assert result["join_ref"] == "123"
    assert result["ref"] is None
    assert result["topic"] == "top"
    assert result["event"] == "some-event"
    assert result["payload"] == {"a": "b"}


def test_decode_reply():
    """Test decoding reply message."""
    serializer = Serializer()
    # Create binary message: kind=1, join_ref_len=3, ref_len=2, topic_len=3, event_len=2, then strings, then JSON
    bin_data = b'\x01\x03\x02\x03\x0210012topok{"a":"b"}'
    result = serializer.decode(bin_data)
    assert result["join_ref"] == "100"
    assert result["ref"] == "12"
    assert result["topic"] == "top"
    assert result["event"] == ChannelEvents.reply
    assert result["payload"]["status"] == "ok"
    assert result["payload"]["response"] == {"a": "b"}


def test_decode_broadcast():
    """Test decoding broadcast message."""
    serializer = Serializer()
    # Create binary message: kind=2, topic_len=3, event_len=10, then strings, then JSON
    bin_data = b'\x02\x03\ntopsome-event{"a":"b"}'
    result = serializer.decode(bin_data)
    assert result["join_ref"] is None
    assert result["ref"] is None
    assert result["topic"] == "top"
    assert result["event"] == "some-event"
    assert result["payload"] == {"a": "b"}


def test_decode_user_broadcast_json_no_metadata():
    """Test decoding user broadcast with JSON payload and no metadata."""
    serializer = Serializer()
    # kind=4, topic_len=3, user_event_len=10, metadata_len=0, encoding=1, then strings, then JSON payload
    bin_data = b'\x04\x03\n\x00\x01topuser-event{"a":"b"}'
    result = serializer.decode(bin_data)
    assert result["join_ref"] is None
    assert result["ref"] is None
    assert result["topic"] == "top"
    assert result["event"] == "broadcast"
    assert result["payload"]["type"] == "broadcast"
    assert result["payload"]["event"] == "user-event"
    assert result["payload"]["payload"] == {"a": "b"}
    assert "meta" not in result["payload"]


def test_decode_user_broadcast_json_with_metadata():
    """Test decoding user broadcast with JSON payload and metadata."""
    serializer = Serializer()
    # kind=4, topic_len=3, user_event_len=10, metadata_len=17, encoding=1, then strings, metadata, JSON payload
    bin_data = b'\x04\x03\n\x11\x01topuser-event{"replayed":true}{"a":"b"}'
    result = serializer.decode(bin_data)
    assert result["join_ref"] is None
    assert result["ref"] is None
    assert result["topic"] == "top"
    assert result["event"] == "broadcast"
    assert result["payload"]["type"] == "broadcast"
    assert result["payload"]["event"] == "user-event"
    assert result["payload"]["payload"] == {"a": "b"}
    assert result["payload"]["meta"] == {"replayed": True}


def test_decode_user_broadcast_binary_no_metadata():
    """Test decoding user broadcast with binary payload and no metadata."""
    serializer = Serializer()
    # kind=4, topic_len=3, user_event_len=10, metadata_len=0, encoding=0, then strings, then binary payload
    bin_data = b'\x04\x03\n\x00\x00topuser-event\x01\x04'
    result = serializer.decode(bin_data)
    assert result["join_ref"] is None
    assert result["ref"] is None
    assert result["topic"] == "top"
    assert result["event"] == "broadcast"
    assert result["payload"]["type"] == "broadcast"
    assert result["payload"]["event"] == "user-event"
    assert isinstance(result["payload"]["payload"], bytes)
    assert result["payload"]["payload"] == b'\x01\x04'
    assert "meta" not in result["payload"]


def test_decode_user_broadcast_binary_with_metadata():
    """Test decoding user broadcast with binary payload and metadata."""
    serializer = Serializer()
    # kind=4, topic_len=3, user_event_len=10, metadata_len=17, encoding=0, then strings, metadata, binary payload
    bin_data = b'\x04\x03\n\x11\x00topuser-event{"replayed":true}\x01\x04'
    result = serializer.decode(bin_data)
    assert result["join_ref"] is None
    assert result["ref"] is None
    assert result["topic"] == "top"
    assert result["event"] == "broadcast"
    assert result["payload"]["type"] == "broadcast"
    assert result["payload"]["event"] == "user-event"
    assert isinstance(result["payload"]["payload"], bytes)
    assert result["payload"]["payload"] == b'\x01\x04'
    assert result["payload"]["meta"] == {"replayed": True}


def test_encode_validation_errors():
    """Test that encoding validates field lengths."""
    serializer = Serializer()
    
    # Test join_ref too long
    with pytest.raises(ValueError, match="joinRef length"):
        serializer._encode_user_broadcast_push_internal(
            {
                "join_ref": "a" * 256,
                "ref": "1",
                "topic": "top",
                "payload": {"event": "user-event", "payload": {}},
            },
            1,
            b"",
        )
    
    # Test ref too long
    with pytest.raises(ValueError, match="ref length"):
        serializer._encode_user_broadcast_push_internal(
            {
                "join_ref": "10",
                "ref": "a" * 256,
                "topic": "top",
                "payload": {"event": "user-event", "payload": {}},
            },
            1,
            b"",
        )
    
    # Test topic too long
    with pytest.raises(ValueError, match="topic length"):
        serializer._encode_user_broadcast_push_internal(
            {
                "join_ref": "10",
                "ref": "1",
                "topic": "a" * 256,
                "payload": {"event": "user-event", "payload": {}},
            },
            1,
            b"",
        )
    
    # Test user_event too long
    with pytest.raises(ValueError, match="userEvent length"):
        serializer._encode_user_broadcast_push_internal(
            {
                "join_ref": "10",
                "ref": "1",
                "topic": "top",
                "payload": {"event": "a" * 256, "payload": {}},
            },
            1,
            b"",
        )
    
    # Test metadata too long
    serializer_with_meta = Serializer(allowed_metadata_keys=["extra"])
    # Create metadata that will exceed 255 chars when JSON stringified
    # JSON format: {"extra":"aaa..."} = 2 + 9 + 1 + 1 + N + 1 = 14 + N
    # So we need N > 241 to exceed 255 total
    with pytest.raises(ValueError, match="metadata length"):
        serializer_with_meta._encode_user_broadcast_push_internal(
            {
                "join_ref": "10",
                "ref": "1",
                "topic": "top",
                "payload": {
                    "event": "user-event",
                    "payload": {},
                    "extra": "a" * 260,  # Will exceed 255 when JSON stringified
                },
            },
            1,
            b"",
        )


def test_pick_helper():
    """Test the _pick helper method."""
    serializer = Serializer()
    obj = {"a": 1, "b": 2, "c": 3}
    result = serializer._pick(obj, ["a", "c"])
    assert result == {"a": 1, "c": 3}
    assert "b" not in result
    
    # Test with None
    assert serializer._pick(None, ["a"]) == {}
    
    # Test with empty dict
    assert serializer._pick({}, ["a"]) == {}
