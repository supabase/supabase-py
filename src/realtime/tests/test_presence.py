import asyncio
import datetime
import os
from collections.abc import AsyncIterator, Awaitable, Callable
from unittest.mock import AsyncMock

import pytest
from dotenv import load_dotenv
from pydantic import TypeAdapter

from realtime import (
    ChannelNotJoinedError,
    ChannelStates,
    PushRejectedError,
    RealtimeChannel,
    RealtimeChannelOptions,
    RealtimeClient,
    RealtimeError,
)
from realtime.client import connect_once
from realtime.message import (
    Message,
    PresenceDiffMessage,
    ReplyMessage,
    ServerMessageAdapter,
)
from realtime.presence import (
    PresenceEvent,
    PresenceJoin,
    PresenceLeave,
    PresenceSync,
    RealtimePresence,
    _transform_state,
)
from realtime.types import ChannelEvents, Presence, RawPresenceDiff, RawPresenceState

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


async def next_events(
    events: AsyncIterator[PresenceEvent], count: int
) -> list[PresenceEvent]:
    return [await asyncio.wait_for(anext(events), timeout=5) for _ in range(count)]


@pytest.mark.asyncio
async def test_presence(socket: RealtimeClient) -> None:
    user1 = {
        "user_id": "1",
        "online_at": datetime.datetime.now(datetime.UTC).isoformat(),
    }
    user2 = {
        "user_id": "2",
        "online_at": datetime.datetime.now(datetime.UTC).isoformat(),
    }

    chan = socket.channel("room")
    events = chan.presence_events()
    async with chan:
        assert await next_events(events, 1) == [PresenceSync()]

        await chan.track(user1)
        join, sync = await next_events(events, 2)
        assert isinstance(join, PresenceJoin)
        assert sync == PresenceSync()
        assert join.current_presences == []
        assert join.new_presences[0].model_extra == user1
        assert join.new_presences[0].presence_ref
        [(key, presences)] = chan.presence_state().items()
        assert key == join.key
        assert [p.model_extra for p in presences] == [user1]

        await chan.track(user2)
        join, leave, sync = await next_events(events, 3)
        assert isinstance(join, PresenceJoin)
        assert isinstance(leave, PresenceLeave)
        assert sync == PresenceSync()
        assert join.new_presences[0].model_extra == user2
        assert leave.left_presences[0].model_extra == user1
        assert join.key == leave.key == key

        await chan.untrack()
        leave, sync = await next_events(events, 2)
        assert isinstance(leave, PresenceLeave)
        assert leave.left_presences[0].model_extra == user2
        assert leave.current_presences == []
        assert chan.presence_state() == {}


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


def test_sync_diff_processes_every_leave_key() -> None:
    """Leaves for a key the client never tracked must not skip the remaining keys."""
    presence = RealtimePresence()

    presence._on_state_event(raw_state({"bob": {"metas": [{"phx_ref": "ref-bob"}]}}))
    assert list(presence.state) == ["bob"]

    events = presence._on_diff_event(
        raw_diff(
            joins={},
            leaves={
                "alice": {"metas": [{"phx_ref": "ref-alice"}]},
                "bob": {"metas": [{"phx_ref": "ref-bob"}]},
            },
        )
    )

    assert presence.state == {}
    assert [event.key for event in events if isinstance(event, PresenceLeave)] == [
        "bob"
    ]


def test_diff_join_for_known_presence_is_not_reported_twice() -> None:
    presence = RealtimePresence()
    state = raw_state({"k": {"metas": [{"phx_ref": "A", "user_id": "1"}]}})
    assert len(presence._on_state_event(state)) == 2

    joins = {"k": {"metas": [{"phx_ref": "A", "user_id": "1"}]}}
    events = presence._on_diff_event(raw_diff(joins=joins, leaves={}))

    assert events == [PresenceSync()]
    assert presence.state == {"k": [Presence(presence_ref="A", user_id="1")]}


def test_diff_leave_for_presence_already_gone_is_not_reported() -> None:
    presence = RealtimePresence()
    presence._on_state_event(raw_state({"k": {"metas": [{"phx_ref": "B"}]}}))

    leaves = {"k": {"metas": [{"phx_ref": "A"}]}}
    events = presence._on_diff_event(raw_diff(joins={}, leaves=leaves))

    assert events == [PresenceSync()]
    assert presence.state == {"k": [Presence(presence_ref="B")]}


def test_diff_join_reports_only_new_presences_for_a_key() -> None:
    presence = RealtimePresence()
    presence._on_state_event(raw_state({"k": {"metas": [{"phx_ref": "A"}]}}))

    joins = {"k": {"metas": [{"phx_ref": "A"}, {"phx_ref": "B"}]}}
    events = presence._on_diff_event(raw_diff(joins=joins, leaves={}))

    assert events == [
        PresenceJoin("k", [Presence(presence_ref="A")], [Presence(presence_ref="B")]),
        PresenceSync(),
    ]
    assert presence.state == {
        "k": [Presence(presence_ref="A"), Presence(presence_ref="B")]
    }


def test_unchanged_state_resync_reports_nothing() -> None:
    presence = RealtimePresence()
    presence._on_state_event(raw_state({"k": {"metas": [{"phx_ref": "A"}]}}))

    resync = raw_state({"k": {"metas": [{"phx_ref": "A"}]}})
    assert presence._on_state_event(resync) == [PresenceSync()]


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


def meta(ref: str, **payload: str) -> dict[str, str]:
    return {"phx_ref": ref, **payload}


def presence_message(
    channel: RealtimeChannel,
    event: ChannelEvents,
    payload: dict[str, object],
    join_ref: str | None,
) -> Message:
    return Message.model_validate(
        {
            "event": event,
            "topic": channel.topic,
            "payload": payload,
            "join_ref": join_ref,
        }
    )


def joined_channel(*, enabled: bool = False) -> RealtimeChannel:
    channel = RealtimeClient("http://localhost").channel(
        "room", RealtimeChannelOptions().presence(enabled=enabled)
    )
    channel.join_ref = "1"
    channel.presence._on_join("1")
    channel.state = ChannelStates.JOINED
    channel._presence_on = channel.options.presence_enabled
    return channel


def receive_state(
    channel: RealtimeChannel, state: dict[str, object], join_ref: str | None = "1"
) -> None:
    channel._receive(
        presence_message(channel, ChannelEvents.presence_state, state, join_ref)
    )


def receive_diff(
    channel: RealtimeChannel,
    joins: dict[str, object] | None = None,
    leaves: dict[str, object] | None = None,
    join_ref: str | None = None,
) -> None:
    payload: dict[str, object] = {"joins": joins or {}, "leaves": leaves or {}}
    channel._receive(
        presence_message(channel, ChannelEvents.presence_diff, payload, join_ref)
    )


def queued_events(channel: RealtimeChannel) -> list[object]:
    [queue] = channel._presence_listeners
    events: list[object] = []
    while not queue.empty():
        events.append(queue.get_nowait())
    return events


def test_a_presence_message_from_another_join_is_dropped() -> None:
    presence = RealtimePresence()
    presence._on_join("2")

    state = raw_state({"k": {"metas": [meta("A")]}})
    assert presence._on_state_event(state, join_ref="1") == []
    assert presence.state == {}

    diff = raw_diff(joins={"k": {"metas": [meta("B")]}}, leaves={})
    presence._on_state_event(raw_state({}), join_ref="2")
    assert presence._on_diff_event(diff, join_ref="1") == []
    assert presence.state == {}


def test_a_diff_without_a_join_ref_is_applied() -> None:
    presence = RealtimePresence()
    presence._on_join("2")
    presence._on_state_event(raw_state({}), join_ref="2")

    diff = raw_diff(joins={"k": {"metas": [meta("A")]}}, leaves={})
    events = presence._on_diff_event(diff, join_ref=None)

    assert events == [
        PresenceJoin("k", [], [Presence(presence_ref="A")]),
        PresenceSync(),
    ]


def test_diffs_before_the_first_state_are_buffered_and_reported_once() -> None:
    presence = RealtimePresence()
    presence._on_join("1")

    early_join = raw_diff(joins={"k": {"metas": [meta("A")]}}, leaves={})
    early_leave = raw_diff(joins={}, leaves={"gone": {"metas": [meta("G")]}})
    assert presence._on_diff_event(early_join) == []
    assert presence._on_diff_event(early_leave) == []
    assert presence.state == {}

    state = raw_state({"k": {"metas": [meta("A")]}, "gone": {"metas": [meta("G")]}})
    events = presence._on_state_event(state, join_ref="1")

    assert events == [
        PresenceJoin("k", [], [Presence(presence_ref="A")]),
        PresenceSync(),
    ]
    assert presence.state == {"k": [Presence(presence_ref="A")]}


def test_a_rejoin_keeps_the_state_and_reports_only_what_changed() -> None:
    presence = RealtimePresence()
    presence._on_join("1")
    presence._on_state_event(
        raw_state({"stay": {"metas": [meta("S")]}, "go": {"metas": [meta("G")]}}),
        join_ref="1",
    )

    presence._on_join("2")
    diff = raw_diff(joins={"late": {"metas": [meta("L")]}}, leaves={})
    assert presence._on_diff_event(diff) == []
    assert set(presence.state) == {"stay", "go"}

    events = presence._on_state_event(
        raw_state({"stay": {"metas": [meta("S")]}, "new": {"metas": [meta("N")]}}),
        join_ref="2",
    )

    assert events == [
        PresenceJoin("new", [], [Presence(presence_ref="N")]),
        PresenceJoin("late", [], [Presence(presence_ref="L")]),
        PresenceLeave("go", [], [Presence(presence_ref="G")]),
        PresenceSync(),
    ]


def test_a_leave_carries_the_held_payload() -> None:
    presence = RealtimePresence()
    presence._on_state_event(raw_state({"k": {"metas": [meta("A", user="a")]}}))

    events = presence._on_diff_event(
        raw_diff(joins={}, leaves={"k": {"metas": [meta("A")]}})
    )

    assert events == [
        PresenceLeave("k", [], [Presence(presence_ref="A", user="a")]),
        PresenceSync(),
    ]


def test_a_diff_applies_joins_before_leaves_and_keeps_the_order() -> None:
    presence = RealtimePresence()
    presence._on_state_event(raw_state({"k": {"metas": [meta("A", v="1"), meta("B")]}}))

    events = presence._on_diff_event(
        raw_diff(
            joins={"k": {"metas": [meta("A", v="2"), meta("C")]}},
            leaves={"k": {"metas": [meta("B")]}},
        )
    )

    assert presence.state == {
        "k": [Presence(presence_ref="A", v="2"), Presence(presence_ref="C")]
    }
    assert events == [
        PresenceJoin(
            "k",
            [Presence(presence_ref="A", v="1"), Presence(presence_ref="B")],
            [Presence(presence_ref="C")],
        ),
        PresenceLeave(
            "k",
            [Presence(presence_ref="A", v="2"), Presence(presence_ref="C")],
            [Presence(presence_ref="B")],
        ),
        PresenceSync(),
    ]


def test_presence_state_returns_a_snapshot() -> None:
    channel = joined_channel()
    receive_state(channel, {"k": {"metas": [meta("A")]}})
    snapshot = channel.presence_state()

    receive_diff(
        channel, joins={"k": {"metas": [meta("B")]}, "j": {"metas": [meta("J")]}}
    )

    assert snapshot == {"k": [Presence(presence_ref="A")]}
    assert set(channel.presence_state()) == {"k", "j"}


def test_presence_events_are_not_yielded_by_messages() -> None:
    channel = joined_channel(enabled=True)
    channel.presence_events()

    receive_state(channel, {"k": {"metas": [meta("A")]}})

    assert channel.message_stream.empty()
    assert queued_events(channel) == [
        PresenceJoin("k", [], [Presence(presence_ref="A")]),
        PresenceSync(),
    ]


async def test_unsubscribe_clears_the_state_and_reports_every_leave() -> None:
    channel = joined_channel()
    channel.state = ChannelStates.CLOSED
    channel.presence_events()
    receive_state(
        channel, {"a": {"metas": [meta("A1"), meta("A2")]}, "b": {"metas": [meta("B")]}}
    )
    queued_events(channel)

    await channel.unsubscribe()

    assert channel.presence_state() == {}
    assert queued_events(channel) == [
        PresenceLeave(
            "a", [], [Presence(presence_ref="A1"), Presence(presence_ref="A2")]
        ),
        PresenceLeave("b", [], [Presence(presence_ref="B")]),
        PresenceSync(),
    ]


async def test_the_first_state_after_resubscribing_reports_every_join() -> None:
    channel = joined_channel()
    channel.state = ChannelStates.CLOSED
    receive_state(channel, {"a": {"metas": [meta("A")]}})
    await channel.unsubscribe()

    channel.presence_events()
    channel.join_ref = "3"
    channel.presence._on_join("3")
    receive_state(channel, {"a": {"metas": [meta("A")]}}, join_ref="3")

    assert queued_events(channel) == [
        PresenceJoin("a", [], [Presence(presence_ref="A")]),
        PresenceSync(),
    ]


def test_a_presence_listener_on_a_channel_joined_with_presence_off_is_rejected() -> (
    None
):
    channel = joined_channel()

    with pytest.raises(RealtimeError):
        channel.presence_events()

    assert channel._presence_listeners == {}


def test_a_presence_listener_is_accepted_when_presence_is_on() -> None:
    joined_channel(enabled=True).presence_events()
    channel = joined_channel()
    channel._presence_on = True
    channel.presence_events()


@pytest.mark.parametrize(
    ("listen", "enabled", "expected"),
    [(False, False, False), (True, False, True), (False, True, True)],
)
async def test_presence_is_enabled_by_a_listener_or_the_option(
    listen: bool, enabled: bool, expected: bool, monkeypatch: pytest.MonkeyPatch
) -> None:
    channel = RealtimeClient("http://localhost").channel(
        "room", RealtimeChannelOptions().presence(enabled=enabled)
    )
    if listen:
        channel.presence_events()
    sent: list[Message] = []

    async def send(message: Message) -> ReplyMessage:
        sent.append(message)
        raise RuntimeError("stop")

    async def connect() -> None:
        return None

    async def refresh_token() -> None:
        return None

    monkeypatch.setattr(channel.socket, "connect", connect)
    monkeypatch.setattr(channel.socket, "_refresh_token", refresh_token)
    monkeypatch.setattr(channel.socket, "_send", send)
    with pytest.raises(RuntimeError):
        await channel.subscribe()

    config = sent[0].payload["config"]
    assert isinstance(config, dict)
    presence = config["presence"]
    assert isinstance(presence, dict)
    assert presence["enabled"] is expected


PRESENCE_CALLS: dict[str, Callable[[RealtimeChannel], Awaitable[None]]] = {
    "track": lambda channel: channel.track({"user": "a"}),
    "untrack": lambda channel: channel.untrack(),
}


@pytest.mark.parametrize(
    "state", [ChannelStates.CLOSED, ChannelStates.JOINING, ChannelStates.ERRORED]
)
@pytest.mark.parametrize("call", PRESENCE_CALLS.values(), ids=PRESENCE_CALLS.keys())
async def test_track_and_untrack_raise_when_the_channel_is_not_joined(
    state: ChannelStates,
    call: Callable[[RealtimeChannel], Awaitable[None]],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    channel = RealtimeClient("http://localhost").channel("room")
    channel.state = state
    send = AsyncMock()
    monkeypatch.setattr(channel, "_send_event", send)

    with pytest.raises(ChannelNotJoinedError):
        await call(channel)

    send.assert_not_awaited()


def reply(status: str, response: dict[str, object]) -> ReplyMessage:
    return ReplyMessage.model_validate(
        {
            "event": ChannelEvents.reply,
            "topic": "realtime:room",
            "payload": {"status": status, "response": response},
            "ref": "2",
        }
    )


@pytest.mark.parametrize(
    ("response", "reason"),
    [
        (
            {"reason": "Presence track payload must be a map"},
            "Presence track payload must be a map",
        ),
        ({}, None),
    ],
)
async def test_track_raises_the_servers_error(
    response: dict[str, object], reason: str | None, monkeypatch: pytest.MonkeyPatch
) -> None:
    channel = joined_channel()
    monkeypatch.setattr(
        channel, "_send_event", AsyncMock(return_value=reply("error", response))
    )

    with pytest.raises(PushRejectedError) as error:
        await channel.track({"user": "a"})

    assert error.value.reason == reason
    assert not channel._presence_on


async def test_a_successful_track_turns_presence_on(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    channel = joined_channel()
    ok = reply("ok", {"postgres_changes": []})
    monkeypatch.setattr(channel, "_send_event", AsyncMock(return_value=ok))

    await channel.track({"user": "a"})

    assert channel._presence_on
    channel.presence_events()
