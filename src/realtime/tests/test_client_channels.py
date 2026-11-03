import asyncio
import json
import logging
from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import patch

import pytest

from realtime import AsyncRealtimeClient
from realtime._async.presence import AsyncRealtimePresence
from realtime.message import Message
from realtime.types import (
    ChannelEvents,
    ChannelStates,
    Presence,
    RawPresenceStateEntry,
)

URL = "ws://localhost/realtime/v1"


class FakeConnection:
    def __init__(self) -> None:
        self.sent: list[dict[str, Any]] = []
        self.closed = False

    async def send(self, message: str) -> None:
        self.sent.append(json.loads(message))

    async def close(self) -> None:
        self.closed = True

    def __aiter__(self) -> AsyncIterator[str]:
        return self

    async def __anext__(self) -> str:
        await asyncio.Event().wait()
        raise StopAsyncIteration

    def events(self, topic: str | None = None) -> list[str]:
        return [m["event"] for m in self.sent if topic is None or m["topic"] == topic]


async def connected_socket(
    **kwargs: Any,
) -> tuple[AsyncRealtimeClient, FakeConnection]:
    connection = FakeConnection()

    async def fake_connect(*args: Any, **kwargs: Any) -> FakeConnection:
        return connection

    socket = AsyncRealtimeClient(URL, "token", **kwargs)
    with patch("realtime._async.client.connect", new=fake_connect):
        await socket.connect()
    return socket, connection


async def subscribed_channel(socket: AsyncRealtimeClient, topic: str) -> Any:
    channel = socket.channel(topic)
    with patch.object(channel.join_push, "start_timeout"):
        await channel.subscribe()
    channel.state = ChannelStates.JOINED
    return channel


def test_constructor_rejects_non_websocket_url() -> None:
    with pytest.raises(ValueError):
        AsyncRealtimeClient("ftp://localhost/realtime/v1", "token")


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("http://localhost/realtime/v1", "ws://localhost/realtime/v1/websocket"),
        ("HTTPS://example.co/realtime/v1", "wss://example.co/realtime/v1/websocket"),
    ],
)
def test_constructor_converts_http_urls(url: str, expected: str) -> None:
    socket = AsyncRealtimeClient(url)

    assert socket.url == expected


def test_endpoint_url_merges_params_and_version() -> None:
    socket = AsyncRealtimeClient(URL, "token", params={"log_level": "info"})

    assert socket.endpoint_url() == (
        "ws://localhost/realtime/v1/websocket?log_level=info&apikey=token&vsn=1.0.0"
    )


def test_channel_returns_existing_channel_for_same_topic() -> None:
    socket = AsyncRealtimeClient(URL, "token")

    first = socket.channel("room")
    second = socket.channel("room")

    assert first is second
    assert socket.get_channels() == [first]


def test_channel_replaces_channel_that_is_leaving() -> None:
    socket = AsyncRealtimeClient(URL, "token")
    first = socket.channel("room")
    first.state = ChannelStates.LEAVING

    second = socket.channel("room")

    assert second is not first
    assert socket.get_channels() == [second]


@pytest.mark.asyncio
async def test_send_buffers_until_connected() -> None:
    socket = AsyncRealtimeClient(URL, "token")
    message = Message(topic="phoenix", event="heartbeat", payload={}, ref="1")

    await socket.send(message)

    assert len(socket.send_buffer) == 1
    connection = FakeConnection()

    async def fake_connect(*args: Any, **kwargs: Any) -> FakeConnection:
        return connection

    with patch("realtime._async.client.connect", new=fake_connect):
        await socket.connect()

    assert socket.send_buffer == []
    assert connection.sent[0] == {
        "topic": "phoenix",
        "event": "heartbeat",
        "payload": {},
        "ref": "1",
        "join_ref": None,
    }
    await socket.close()


@pytest.mark.asyncio
async def test_send_with_dictionary_is_deprecated_but_sent(
    caplog: pytest.LogCaptureFixture,
) -> None:
    socket, connection = await connected_socket()

    with caplog.at_level(logging.WARNING, logger="realtime._async.client"):
        await socket.send(
            {"topic": "phoenix", "event": "heartbeat", "payload": {}, "ref": "9"}
        )

    assert "deprecated" in caplog.text
    assert connection.sent[-1]["ref"] == "9"
    await socket.close()


@pytest.mark.asyncio
async def test_listen_is_deprecated(caplog: pytest.LogCaptureFixture) -> None:
    socket = AsyncRealtimeClient(URL, "token")

    with caplog.at_level(logging.WARNING, logger="realtime._async.client"):
        await socket.listen()

    assert "listen is deprecated" in caplog.text


@pytest.mark.asyncio
async def test_close_without_connection_is_noop() -> None:
    socket = AsyncRealtimeClient(URL, "token")

    await socket.close()

    assert not socket.is_connected


@pytest.mark.asyncio
async def test_remove_channel_leaves_and_closes_after_last_channel() -> None:
    socket, connection = await connected_socket()
    first = await subscribed_channel(socket, "first")
    second = await subscribed_channel(socket, "second")

    await socket.remove_channel(first)

    assert socket.get_channels() == [second]
    assert connection.events("realtime:first")[-1] == ChannelEvents.leave
    assert socket.is_connected

    await socket.remove_channel(second)

    assert socket.get_channels() == []
    assert connection.closed
    assert not socket.is_connected


@pytest.mark.asyncio
async def test_remove_channel_ignores_stale_channel() -> None:
    socket, connection = await connected_socket()
    stale = await subscribed_channel(socket, "room")
    stale.state = ChannelStates.LEAVING
    current = await subscribed_channel(socket, "room")
    sent_before = len(connection.sent)

    await socket.remove_channel(stale)

    assert socket.get_channels() == [current]
    assert len(connection.sent) == sent_before
    await socket.close()


@pytest.mark.asyncio
async def test_remove_all_channels_leaves_every_channel_and_closes() -> None:
    socket, connection = await connected_socket()
    await subscribed_channel(socket, "first")
    await subscribed_channel(socket, "second")

    await socket.remove_all_channels()

    assert connection.events("realtime:first")[-1] == ChannelEvents.leave
    assert connection.events("realtime:second")[-1] == ChannelEvents.leave
    assert connection.closed
    assert not socket.is_connected


@pytest.mark.asyncio
async def test_remove_all_channels_forgets_channels() -> None:
    socket, _ = await connected_socket()
    await subscribed_channel(socket, "first")

    await socket.remove_all_channels()

    assert socket.get_channels() == []


@pytest.mark.asyncio
async def test_set_auth_pushes_token_to_joined_channels_only() -> None:
    socket, connection = await connected_socket()
    joined = await subscribed_channel(socket, "joined")
    joining = socket.channel("joining")
    with patch.object(joining.join_push, "start_timeout"):
        await joining.subscribe()

    await socket.set_auth("new-token")

    assert socket.access_token == "new-token"
    assert connection.events("realtime:joined")[-1] == ChannelEvents.access_token
    assert connection.events("realtime:joining")[-1] == ChannelEvents.join
    assert joined.join_push.payload["access_token"] == "new-token"
    assert joining.join_push.payload["access_token"] == "new-token"
    await socket.close()


@pytest.mark.asyncio
async def test_push_before_subscribe_raises() -> None:
    socket = AsyncRealtimeClient(URL, "token")
    channel = socket.channel("room")

    with pytest.raises(Exception, match="before joining"):
        await channel.push("event", {})


@pytest.mark.asyncio
async def test_push_while_disconnected_is_buffered() -> None:
    socket, _ = await connected_socket()
    channel = await subscribed_channel(socket, "room")
    await socket.close()

    with patch("realtime._async.push.AsyncPush.start_timeout"):
        push = await channel.push("event", {"a": 1})

    assert channel._push_buffer == [push]


@pytest.mark.parametrize(
    "register",
    [
        lambda channel: channel.on_presence_sync(lambda: None),
        lambda channel: channel.on_presence_join(lambda key, cur, new: None),
        lambda channel: channel.on_presence_leave(lambda key, cur, left: None),
    ],
    ids=["sync", "join", "leave"],
)
@pytest.mark.asyncio
async def test_presence_callbacks_on_joined_channel_resubscribe(register: Any) -> None:
    socket, connection = await connected_socket()
    channel = await subscribed_channel(socket, "room")

    with patch.object(channel, "_resubscribe") as resubscribe:
        register(channel)
        await asyncio.sleep(0)

    resubscribe.assert_called_once()
    await socket.close()


def _raw(*refs: str, **meta: Any) -> RawPresenceStateEntry:
    return {"metas": [{"phx_ref": ref, **meta} for ref in refs]}  # type: ignore[typeddict-item]


def test_presence_state_event_reports_joins_and_leaves_for_existing_keys() -> None:
    presence = AsyncRealtimePresence()
    joins: list[tuple[str, list[Presence], list[Presence]]] = []
    leaves: list[tuple[str, list[Presence], list[Presence]]] = []
    syncs: list[None] = []
    presence.on_join(lambda key, cur, new: joins.append((key, cur, new)))
    presence.on_leave(lambda key, cur, left: leaves.append((key, cur, left)))
    presence.on_sync(lambda: syncs.append(None))

    presence._on_state_event({"alice": _raw("a1", "a2"), "bob": _raw("b1")})
    joins.clear()
    leaves.clear()

    presence._on_state_event({"alice": _raw("a2", "a3"), "carol": _raw("c1")})

    assert presence.state == {
        "alice": [{"presence_ref": "a2"}, {"presence_ref": "a3"}],
        "carol": [{"presence_ref": "c1"}],
    }
    assert [(key, new) for key, _, new in joins] == [
        ("alice", [{"presence_ref": "a3"}]),
        ("carol", [{"presence_ref": "c1"}]),
    ]
    assert sorted((key, left) for key, _, left in leaves) == [
        ("alice", [{"presence_ref": "a1"}]),
        ("bob", [{"presence_ref": "b1"}]),
    ]
    assert len(syncs) == 2


def test_presence_state_event_without_changes_reports_nothing() -> None:
    presence = AsyncRealtimePresence()
    presence._on_state_event({"alice": _raw("a1", status="online")})
    joins: list[str] = []
    leaves: list[str] = []
    presence.on_join(lambda key, cur, new: joins.append(key))
    presence.on_leave(lambda key, cur, left: leaves.append(key))

    presence._on_state_event({"alice": _raw("a1", status="online")})

    assert joins == []
    assert leaves == []
    assert presence.state == {"alice": [{"presence_ref": "a1", "status": "online"}]}


def test_presence_diff_ignores_leaves_for_unknown_keys() -> None:
    presence = AsyncRealtimePresence()
    leaves: list[str] = []
    presence.on_leave(lambda key, cur, left: leaves.append(key))

    presence._on_diff_event({"joins": {}, "leaves": {"ghost": _raw("g1")}})

    assert leaves == []
    assert presence.state == {}
