import datetime
import os
from collections.abc import AsyncIterator

import pytest
from dotenv import load_dotenv
from pydantic import TypeAdapter

from realtime import RealtimeClient
from realtime.client import connect_once
from realtime.message import (
    PostgresChangesMessage,
    PresenceDiffMessage,
    ServerMessageAdapter,
)
from realtime.presence import (
    PresenceJoin,
    PresenceLeave,
    RealtimePresence,
    _transform_state,
)
from realtime.types import Presence, RawPresenceDiff, RawPresenceState

load_dotenv()

RawPresenceStateAdapter: TypeAdapter[RawPresenceState] = TypeAdapter(RawPresenceState)


def raw_state(state: object) -> RawPresenceState:
    return RawPresenceStateAdapter.validate_python(state)


def raw_diff(joins: object, leaves: object) -> RawPresenceDiff:
    return RawPresenceDiff.model_validate({"joins": joins, "leaves": leaves})


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
async def test_presence(socket: RealtimeClient) -> None:
    user1 = {"user_id": "1", "online_at": datetime.datetime.now().isoformat()}
    user2 = {"user_id": "2", "online_at": datetime.datetime.now().isoformat()}

    async with socket.channel("room") as chan:
        await chan.track(user1)
        messages_stream = chan.messages
        fst_join = await messages_stream.__anext__()
        if not isinstance(fst_join, PresenceJoin):
            raise Exception("unexpected message")

        presences = list(chan.presence.state.items())

        assert len(presences) == 1
        assert len(presences[0][1]) == 1
        assert presences[0][1][0].model_extra == user1
        assert presences[0][1][0].presence_ref

        assert fst_join.new_presences[0].model_extra == user1
        assert fst_join.new_presences[0].presence_ref

        await chan.track(user2)
        snd_join = await messages_stream.__anext__()
        if not isinstance(snd_join, PresenceJoin):
            raise Exception("unexpected message")

        assert snd_join.new_presences[0].model_extra == user2
        assert snd_join.new_presences[0].presence_ref

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
    state = raw_state(
        {
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
                "metas": [
                    {"phx_ref": "GHI789", "user_id": "user2", "status": "offline"}
                ]
            },
        }
    )

    expected_output = {
        "user1": [
            Presence(presence_ref="ABC123", user_id="user1", status="online"),
            Presence(presence_ref="DEF456", user_id="user1", status="away"),
        ],
        "user2": [Presence(presence_ref="GHI789", user_id="user2", status="offline")],
    }

    assert _transform_state(state) == expected_output


def test_transform_state_empty_input() -> None:
    assert _transform_state({}) == {}


def test_transform_state_additional_fields() -> None:
    state = raw_state(
        {
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
    )

    result = _transform_state(state)

    assert result == {
        "user1": [
            Presence(
                presence_ref="ABC123", user_id="user1", status="online", extra="data"
            )
        ]
    }
    assert result["user1"][0].model_extra == {
        "user_id": "user1",
        "status": "online",
        "extra": "data",
    }


def test_transform_state_uses_phx_ref_over_tracked_presence_ref() -> None:
    state = raw_state(
        {"user1": {"metas": [{"phx_ref": "ABC123", "presence_ref": "tracked"}]}}
    )

    assert _transform_state(state) == {"user1": [Presence(presence_ref="ABC123")]}


def test_postgres_changes_message_accepts_a_list_of_errors() -> None:
    message = ServerMessageAdapter.validate_python(
        {
            "event": "postgres_changes",
            "topic": "realtime:room",
            "ref": None,
            "payload": {
                "ids": [1],
                "data": {
                    "schema": "public",
                    "table": "todos",
                    "commit_timestamp": "2026-11-04T00:00:00Z",
                    "type": "INSERT",
                    "errors": ["Error 413: Payload Too Large"],
                    "columns": [{"name": "id", "type": "int8"}],
                },
            },
        }
    )

    assert isinstance(message, PostgresChangesMessage)
    assert message.payload.data.errors == ["Error 413: Payload Too Large"]
    assert message.payload.data.schema_ == "public"


def test_sync_diff_processes_every_leave_key() -> None:
    """Leaves for a key the client never tracked must not skip the remaining keys."""
    presence = RealtimePresence()

    list(
        presence._on_state_event(
            raw_state({"bob": {"metas": [{"phx_ref": "ref-bob"}]}})
        )
    )
    assert list(presence.state) == ["bob"]

    events = list(
        presence._on_diff_event(
            raw_diff(
                joins={},
                leaves={
                    "alice": {"metas": [{"phx_ref": "ref-alice"}]},
                    "bob": {"metas": [{"phx_ref": "ref-bob"}]},
                },
            )
        )
    )

    assert presence.state == {}
    assert [event.key for event in events if isinstance(event, PresenceLeave)] == [
        "bob"
    ]


def test_diff_join_for_known_presence_is_not_reported_twice() -> None:
    presence = RealtimePresence()
    state = raw_state({"k": {"metas": [{"phx_ref": "A", "user_id": "1"}]}})
    assert len(list(presence._on_state_event(state))) == 1

    joins = {"k": {"metas": [{"phx_ref": "A", "user_id": "1"}]}}
    events = list(presence._on_diff_event(raw_diff(joins=joins, leaves={})))

    assert events == []
    assert presence.state == {"k": [Presence(presence_ref="A", user_id="1")]}


def test_diff_leave_for_presence_already_gone_is_not_reported() -> None:
    presence = RealtimePresence()
    list(presence._on_state_event(raw_state({"k": {"metas": [{"phx_ref": "B"}]}})))

    leaves = {"k": {"metas": [{"phx_ref": "A"}]}}
    events = list(presence._on_diff_event(raw_diff(joins={}, leaves=leaves)))

    assert events == []
    assert presence.state == {"k": [Presence(presence_ref="B")]}


def test_diff_join_reports_only_new_presences_for_a_key() -> None:
    presence = RealtimePresence()
    list(presence._on_state_event(raw_state({"k": {"metas": [{"phx_ref": "A"}]}})))

    joins = {"k": {"metas": [{"phx_ref": "A"}, {"phx_ref": "B"}]}}
    events = list(presence._on_diff_event(raw_diff(joins=joins, leaves={})))

    assert events == [
        PresenceJoin("k", [Presence(presence_ref="A")], [Presence(presence_ref="B")])
    ]
    assert presence.state == {
        "k": [Presence(presence_ref="A"), Presence(presence_ref="B")]
    }


def test_unchanged_state_resync_reports_nothing() -> None:
    presence = RealtimePresence()
    list(presence._on_state_event(raw_state({"k": {"metas": [{"phx_ref": "A"}]}})))

    resync = raw_state({"k": {"metas": [{"phx_ref": "A"}]}})
    assert list(presence._on_state_event(resync)) == []


def test_presence_diff_message_payload_is_validated_into_models() -> None:
    message = ServerMessageAdapter.validate_python(
        {
            "event": "presence_diff",
            "topic": "realtime:room",
            "ref": None,
            "payload": {
                "joins": {"k": {"metas": [{"phx_ref": "A", "user_id": "1"}]}},
                "leaves": {},
            },
        }
    )

    assert isinstance(message, PresenceDiffMessage)
    assert isinstance(message.payload, RawPresenceDiff)
    meta = message.payload.joins["k"].metas[0]
    assert meta.phx_ref == "A"
    assert meta.model_extra == {"user_id": "1"}
