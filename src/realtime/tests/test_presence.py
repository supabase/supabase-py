import asyncio
import datetime
import os
from typing import AsyncIterator, Dict, List, Tuple

import pytest
from dotenv import load_dotenv

from realtime import RealtimeChannel, RealtimeClient
from realtime.client import connect_once
from realtime.message import PresenceDiffMessage, ServerMessage
from realtime.presence import PresenceJoin, PresenceLeave, _transform_state
from realtime.types import ChannelStates, Presence, RawPresenceState

load_dotenv()

URL = os.getenv("SUPABASE_URL") or "http://127.0.0.1:54321"
PUBLISHABLE_KEY = (
    os.getenv("SUPABASE_PUBLISHABLE_KEY")
    or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0"
)


async def get_token() -> str:
    return PUBLISHABLE_KEY


@pytest.fixture
async def socket() -> AsyncIterator[RealtimeClient]:
    url = f"{URL}/realtime/v1"
    async with connect_once(url, get_token) as client:
        yield client


@pytest.mark.asyncio
async def test_presence(socket: RealtimeClient):
    user1 = {"user_id": "1", "online_at": datetime.datetime.now().isoformat()}
    user2 = {"user_id": "2", "online_at": datetime.datetime.now().isoformat()}

    async with socket.channel("room") as chan:
        res = await chan.track(user1)
        messages_stream = chan.messages
        fst_join = await messages_stream.__anext__()
        if not isinstance(fst_join, PresenceJoin):
            raise Exception("unexpected message")

        presences = list(chan.presence.state.items())

        assert len(presences) == 1
        assert len(presences[0][1]) == 1
        assert presences[0][1][0].get("user_id", "") == user1["user_id"]
        assert presences[0][1][0].get("online_at", "") == user1["online_at"]
        assert "presence_ref" in presences[0][1][0]

        assert fst_join.new_presences[0].get("user_id", "") == user1["user_id"]
        assert fst_join.new_presences[0].get("online_at", "") == user1["online_at"]
        assert "presence_ref" in fst_join.new_presences[0]

        await chan.track(user2)
        snd_join = await messages_stream.__anext__()
        if not isinstance(snd_join, PresenceJoin):
            raise Exception("unexpected message")

        assert snd_join.new_presences[0].get("user_id", "") == user2["user_id"]
        assert snd_join.new_presences[0].get("online_at", "") == user2["online_at"]
        assert "presence_ref" in snd_join.new_presences[0]

        await chan.untrack()
        fst_leave = await messages_stream.__anext__()
        if not isinstance(fst_leave, PresenceLeave):
            raise Exception("unexpected message")
        snd_leave = await messages_stream.__anext__()
        if not isinstance(snd_leave, PresenceLeave):
            raise Exception("unexpected message")
        assert chan.presence.state == {}
        assert fst_leave != snd_leave


def test_transform_state_raw_presence_state() -> None:
    raw_state: RawPresenceState = {
        "user1": {
            "metas": [
                {"phx_ref": "ABC123", "user_id": "user1", "status": "online"},  # type: ignore
                {  # type: ignore
                    "phx_ref": "DEF456",
                    "phx_ref_prev": "ABC123",
                    "user_id": "user1",
                    "status": "away",
                },
            ]
        },
        "user2": {
            "metas": [{"phx_ref": "GHI789", "user_id": "user2", "status": "offline"}]  # type: ignore
        },
    }

    expected_output = {
        "user1": [
            {"presence_ref": "ABC123", "user_id": "user1", "status": "online"},
            {"presence_ref": "DEF456", "user_id": "user1", "status": "away"},
        ],
        "user2": [{"presence_ref": "GHI789", "user_id": "user2", "status": "offline"}],
    }

    result = _transform_state(raw_state)
    assert result == expected_output


def test_transform_state_empty_input() -> None:
    empty_state: RawPresenceState = {}
    result = _transform_state(empty_state)
    assert result == {}


def test_transform_state_additional_fields() -> None:
    state_with_additional_fields: RawPresenceState = {
        "user1": {
            "metas": [
                {  # type: ignore
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

    result = _transform_state(state_with_additional_fields)
    assert result == expected_output
