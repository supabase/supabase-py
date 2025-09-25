import asyncio
import datetime
import os
from typing import Dict, List, Tuple

import pytest
from dotenv import load_dotenv

from realtime import AsyncRealtimeChannel, AsyncRealtimeClient, AsyncRealtimePresence
from realtime.types import RawPresenceState

load_dotenv()

URL = os.getenv("SUPABASE_URL") or "http://127.0.0.1:54321"
ANON_KEY = (
    os.getenv("SUPABASE_ANON_KEY")
    or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0"
)


@pytest.fixture
def socket() -> AsyncRealtimeClient:
    url = f"{URL}/realtime/v1"
    return AsyncRealtimeClient(url, ANON_KEY)


@pytest.mark.asyncio
async def test_presence(socket: AsyncRealtimeClient):
    await socket.connect()

    channel: AsyncRealtimeChannel = socket.channel("room")

    join_events: List[Tuple[str, List[Dict], List[Dict]]] = []
    leave_events: List[Tuple[str, List[Dict], List[Dict]]] = []

    sync_event = asyncio.Event()

    def on_sync():
        sync_event.set()

    def on_join(key: str, current_presences: List[Dict], new_presences: List[Dict]):
        join_events.append((key, current_presences, new_presences))

    def on_leave(key: str, current_presences: List[Dict], left_presences: List[Dict]):
        leave_events.append((key, current_presences, left_presences))

    await (
        channel.on_presence_sync(on_sync)
        .on_presence_join(on_join)
        .on_presence_leave(on_leave)
        .subscribe()
    )

    # Wait for the first sync event, which should be immediate
    await asyncio.wait_for(sync_event.wait(), 5)
    sync_event.clear()

    # Track first user
    user1 = {"user_id": "1", "online_at": datetime.datetime.now().isoformat()}
    await channel.track(user1)

    await asyncio.wait_for(sync_event.wait(), 5)
    sync_event.clear()

    # Assert first user is in the presence state
    presences = [(state, value) for state, value in channel.presence.state.items()]

    assert len(presences) == 1
    assert len(presences[0][1]) == 1
    assert presences[0][1][0]["user_id"] == user1["user_id"]
    assert presences[0][1][0]["online_at"] == user1["online_at"]
    assert "presence_ref" in presences[0][1][0]

    assert len(join_events) == 1
    assert len(join_events[0][2]) == 1
    assert join_events[0][2][0]["user_id"] == user1["user_id"]
    assert join_events[0][2][0]["online_at"] == user1["online_at"]
    assert "presence_ref" in join_events[0][2][0]

    # Track second user
    user2 = {"user_id": "2", "online_at": datetime.datetime.now().isoformat()}
    await channel.track(user2)

    await asyncio.wait_for(sync_event.wait(), 5)
    sync_event.clear()

    # Assert both users are in the presence state
    presences = channel.presence.state
    for key, value in presences.items():
        assert len(value) == 1
        assert value[0]["user_id"] in ["1", "2"]
        assert "online_at" in value[0]
        assert "presence_ref" in value[0]
    assert len(join_events) == 2
    assert len(join_events[1][2]) == 1
    assert join_events[1][2][0]["user_id"] == user2["user_id"]
    assert join_events[1][2][0]["online_at"] == user2["online_at"]
    assert "presence_ref" in join_events[1][2][0]

    # Untrack all users
    await channel.untrack()

    await asyncio.wait_for(sync_event.wait(), 5)

    # Assert presence state is empty and leave events were triggered
    assert channel.presence.state == {}
    assert len(leave_events) == 2
    assert leave_events[0] != leave_events[1]

    await socket.close()


def test_transform_state_raw_presence_state():
    raw_state: RawPresenceState = {
        "user1": {
            "metas": [
                {"phx_ref": "ABC123", "user_id": "user1", "status": "online"},
                {
                    "phx_ref": "DEF456",
                    "phx_ref_prev": "ABC123",
                    "user_id": "user1",
                    "status": "away",
                },
            ]
        },
        "user2": {
            "metas": [{"phx_ref": "GHI789", "user_id": "user2", "status": "offline"}]
        },
    }

    expected_output = {
        "user1": [
            {"presence_ref": "ABC123", "user_id": "user1", "status": "online"},
            {"presence_ref": "DEF456", "user_id": "user1", "status": "away"},
        ],
        "user2": [{"presence_ref": "GHI789", "user_id": "user2", "status": "offline"}],
    }

    result = AsyncRealtimePresence._transform_state(raw_state)
    assert result == expected_output


def test_transform_state_empty_input():
    empty_state = {}
    result = AsyncRealtimePresence._transform_state(empty_state)
    assert result == {}


def test_transform_state_additional_fields():
    state_with_additional_fields = {
        "user1": {
            "metas": [
                {
                    "phx_ref": "ABC123",
                    "user_id": "user1",
                    "status": "online",
                    "extra": "data",
                }
            ]
        }
    }

    expected_output = {
        "user1": [
            {
                "presence_ref": "ABC123",
                "user_id": "user1",
                "status": "online",
                "extra": "data",
            }
        ]
    }

    result = AsyncRealtimePresence._transform_state(state_with_additional_fields)
    assert result == expected_output


def test_presence_has_callback_attached():
    """Test that _has_callback_attached property correctly detects presence callbacks."""
    presence = AsyncRealtimePresence()

    # Initially no callbacks should be attached
    assert not presence._has_callback_attached

    # After setting sync callback
    presence.on_sync(lambda: None)
    assert presence._has_callback_attached

    # Reset and test with join callback
    presence = AsyncRealtimePresence()
    presence.on_join(lambda key, current, new: None)
    assert presence._has_callback_attached

    # Reset and test with leave callback
    presence = AsyncRealtimePresence()
    presence.on_leave(lambda key, current, left: None)
    assert presence._has_callback_attached


def test_presence_config_includes_enabled_field():
    """Test that presence config correctly includes enabled flag."""
    from realtime.types import RealtimeChannelPresenceConfig

    # Test creating presence config with enabled field
    config: RealtimeChannelPresenceConfig = {
        "key": "user123",
        "enabled": True
    }
    assert config["key"] == "user123"
    assert config["enabled"] == True

    # Test with enabled False
    config_disabled: RealtimeChannelPresenceConfig = {
        "key": "",
        "enabled": False
    }
    assert config_disabled["key"] == ""
    assert config_disabled["enabled"] == False


@pytest.mark.asyncio
async def test_presence_enabled_when_callbacks_attached():
    """Test that presence.enabled is set correctly based on callback attachment."""
    from unittest.mock import Mock, AsyncMock

    socket = AsyncRealtimeClient(f"{URL}/realtime/v1", ANON_KEY)
    channel = socket.channel("test")

    # Mock the join_push to capture the payload
    mock_join_push = Mock()
    mock_join_push.receive = Mock(return_value=mock_join_push)
    mock_join_push.update_payload = Mock()
    mock_join_push.resend = AsyncMock()
    channel.join_push = mock_join_push

    # Mock socket connection by setting _ws_connection
    mock_ws = Mock()
    socket._ws_connection = mock_ws
    socket._leave_open_topic = AsyncMock()

    # Add presence callback before subscription
    channel.on_presence_sync(lambda: None)

    await channel.subscribe()

    # Verify that update_payload was called
    assert mock_join_push.update_payload.called

    # Get the payload that was passed to update_payload
    call_args = mock_join_push.update_payload.call_args
    payload = call_args[0][0]

    # Verify presence.enabled is True because callback is attached
    assert payload["config"]["presence"]["enabled"] == True


@pytest.mark.asyncio
async def test_resubscribe_on_presence_callback_addition():
    """Test that channel resubscribes when presence callbacks are added after joining."""
    from unittest.mock import AsyncMock
    import asyncio

    socket = AsyncRealtimeClient(f"{URL}/realtime/v1", ANON_KEY)
    channel = socket.channel("test")

    # Mock the channel as joined
    channel.state = "joined"
    channel._joined_once = True

    # Mock resubscribe method
    channel._resubscribe = AsyncMock()

    # Add presence callbacks after joining
    channel.on_presence_sync(lambda: None)

    # Wait a bit for async tasks to complete
    await asyncio.sleep(0.1)

    # Verify resubscribe was called
    assert channel._resubscribe.call_count == 1
