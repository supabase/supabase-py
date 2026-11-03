import asyncio
import json
import logging
from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
import websockets

from realtime import AsyncRealtimeClient
from realtime._async.channel import AsyncRealtimeChannel
from realtime.exceptions import AuthorizationError, NotConnectedError
from realtime.message import Message, ServerMessageAdapter
from realtime.types import (
    BroadcastPayload,
    ChannelEvents,
    ChannelStates,
    RealtimePostgresChangesListenEvent,
    RealtimeSubscribeStates,
)

URL = "ws://localhost/realtime/v1"


class FakeConnection:
    def __init__(self, incoming: list[str] | None = None) -> None:
        self.sent: list[dict[str, Any]] = []
        self.incoming = list(incoming or [])
        self.close_code = 1000

    async def send(self, message: str) -> None:
        self.sent.append(json.loads(message))

    async def close(self) -> None:
        pass

    def __aiter__(self) -> AsyncIterator[str]:
        return self

    async def __anext__(self) -> str:
        if self.incoming:
            return self.incoming.pop(0)
        await asyncio.Event().wait()
        raise StopAsyncIteration


async def connected_socket(
    connection: FakeConnection | None = None, **kwargs: Any
) -> tuple[AsyncRealtimeClient, FakeConnection]:
    conn = connection or FakeConnection()

    async def fake_connect(*args: Any, **kwargs: Any) -> FakeConnection:
        return conn

    socket = AsyncRealtimeClient(URL, "token", **kwargs)
    with patch("realtime._async.client.connect", new=fake_connect):
        await socket.connect()
    return socket, conn


async def stop_background_tasks(socket: AsyncRealtimeClient) -> None:
    for task in (socket._heartbeat_task, socket._listen_task):
        if task:
            task.cancel()
    await asyncio.sleep(0)
    socket._heartbeat_task = None
    socket._listen_task = None


def reply(
    channel: AsyncRealtimeChannel, ref: str, status: str, response: dict[str, Any]
) -> None:
    channel._handle_message(
        ServerMessageAdapter.validate_python(
            {
                "topic": channel.topic,
                "event": "phx_reply",
                "ref": ref,
                "join_ref": ref,
                "payload": {"status": status, "response": response},
            }
        )
    )


async def subscribe_with_postgres_changes(
    socket: AsyncRealtimeClient,
    connection: FakeConnection,
) -> tuple[AsyncRealtimeChannel, list[tuple[RealtimeSubscribeStates, Any]], str]:
    channel = socket.channel("db")
    channel.on_postgres_changes(
        RealtimePostgresChangesListenEvent.Insert, lambda payload: None, table="todos"
    )
    channel.on_postgres_changes(
        RealtimePostgresChangesListenEvent.Update,
        lambda payload: None,
        table="todos",
        filter="id=eq.1",
    )
    states: list[tuple[RealtimeSubscribeStates, Any]] = []
    with patch.object(channel.join_push, "start_timeout"):
        await channel.subscribe(lambda state, error: states.append((state, error)))
    join = connection.sent[-1]
    assert join["event"] == ChannelEvents.join
    return channel, states, join["ref"]


SERVER_BINDINGS = [
    {"id": 11, "event": "INSERT", "schema": "public", "table": "todos"},
    {
        "id": 12,
        "event": "UPDATE",
        "schema": "public",
        "table": "todos",
        "filter": "id=eq.1",
    },
]


@pytest.mark.asyncio
async def test_join_reply_assigns_server_ids_to_postgres_bindings() -> None:
    socket, connection = await connected_socket()
    channel, states, ref = await subscribe_with_postgres_changes(socket, connection)

    join_config = connection.sent[-1]["payload"]["config"]
    assert join_config["postgres_changes"] == [
        {"event": "INSERT", "schema": "public", "table": "todos"},
        {"event": "UPDATE", "schema": "public", "table": "todos", "filter": "id=eq.1"},
    ]

    reply(channel, ref, "ok", {"postgres_changes": SERVER_BINDINGS})

    assert [c.id for c in channel.postgres_changes_callbacks] == [11, 12]
    assert states == [(RealtimeSubscribeStates.SUBSCRIBED, None)]
    await socket.close()


@pytest.mark.asyncio
async def test_join_reply_with_mismatched_binding_reports_channel_error() -> None:
    socket, connection = await connected_socket()
    channel, states, ref = await subscribe_with_postgres_changes(socket, connection)
    mismatched = [SERVER_BINDINGS[0], {**SERVER_BINDINGS[1], "filter": "id=eq.2"}]

    reply(channel, ref, "ok", {"postgres_changes": mismatched})
    await asyncio.sleep(0)

    assert len(states) == 1
    assert states[0][0] == RealtimeSubscribeStates.CHANNEL_ERROR
    assert "mismatch" in str(states[0][1])
    assert connection.sent[-1]["event"] == ChannelEvents.leave
    await socket.close()


@pytest.mark.asyncio
async def test_join_reply_with_missing_server_binding_reports_channel_error() -> None:
    socket, connection = await connected_socket()
    channel, states, ref = await subscribe_with_postgres_changes(socket, connection)

    reply(channel, ref, "ok", {"postgres_changes": SERVER_BINDINGS[:1]})
    await asyncio.sleep(0)

    assert [state for state, _ in states] == [RealtimeSubscribeStates.CHANNEL_ERROR]
    await socket.close()


@pytest.mark.asyncio
async def test_join_reply_with_empty_server_bindings_reports_channel_error() -> None:
    socket, connection = await connected_socket()
    channel, states, ref = await subscribe_with_postgres_changes(socket, connection)

    reply(channel, ref, "ok", {"postgres_changes": []})
    await asyncio.sleep(0)
    await socket.close()

    assert [state for state, _ in states] == [RealtimeSubscribeStates.CHANNEL_ERROR]


@pytest.mark.asyncio
async def test_join_reply_without_postgres_changes_keeps_bindings() -> None:
    socket, connection = await connected_socket()
    channel, states, ref = await subscribe_with_postgres_changes(socket, connection)

    reply(channel, ref, "ok", {})
    await socket.close()

    assert states == [(RealtimeSubscribeStates.SUBSCRIBED, None)]
    assert len(channel.postgres_changes_callbacks) == 2


@pytest.mark.asyncio
async def test_join_reply_error_reports_channel_error() -> None:
    socket, connection = await connected_socket()
    channel, states, ref = await subscribe_with_postgres_changes(socket, connection)

    with patch.object(channel.rejoin_timer, "schedule_timeout"):
        reply(channel, ref, "error", {"reason": "unauthorized"})

    assert states[0][0] == RealtimeSubscribeStates.CHANNEL_ERROR
    assert channel.is_errored
    await socket.close()


@pytest.mark.asyncio
async def test_join_sends_channel_config() -> None:
    socket, connection = await connected_socket()
    channel = socket.channel(
        "room",
        {
            "config": {
                "broadcast": {"self": True},
                "presence": {"key": "k", "enabled": True},
                "private": False,
            }
        },
    )

    await channel.join()
    await socket.close()

    payload = connection.sent[-1]["payload"]
    assert payload["config"]["broadcast"] == {"self": True}
    assert payload["config"]["presence"] == {"key": "k", "enabled": True}


@pytest.mark.asyncio
async def test_system_error_message_marks_channel_errored() -> None:
    socket, _ = await connected_socket()
    channel = socket.channel("room")
    channel.state = ChannelStates.JOINED
    states: list[RealtimeSubscribeStates] = []
    channel.subscribe_callback = lambda state, error: states.append(state)

    with patch.object(channel.rejoin_timer, "schedule_timeout") as schedule:
        channel._handle_message(
            ServerMessageAdapter.validate_python(
                {
                    "topic": channel.topic,
                    "event": "system",
                    "ref": None,
                    "payload": {
                        "status": "error",
                        "extension": "postgres_changes",
                        "channel": "room",
                        "message": "boom",
                    },
                }
            )
        )

    assert channel.is_errored
    assert states == [RealtimeSubscribeStates.CHANNEL_ERROR]
    schedule.assert_called_once()
    await socket.close()


@pytest.mark.asyncio
async def test_listen_skips_invalid_messages_and_routes_valid_ones(
    caplog: pytest.LogCaptureFixture,
) -> None:
    broadcast = {
        "topic": "realtime:room",
        "event": "broadcast",
        "ref": None,
        "payload": {"type": "broadcast", "event": "ping", "payload": {"n": 1}},
    }
    other_topic = {**broadcast, "topic": "realtime:other"}
    connection = FakeConnection(
        ["not json", json.dumps(other_topic), json.dumps(broadcast)]
    )
    socket = AsyncRealtimeClient(URL, "token")
    channel = socket.channel("room")
    received: list[BroadcastPayload] = []
    channel.on_broadcast("ping", lambda payload: received.append(payload))
    socket._ws_connection = connection  # type: ignore[assignment]

    with caplog.at_level(logging.ERROR, logger="realtime._async.client"):
        listen = asyncio.create_task(socket._listen())
        for _ in range(10):
            await asyncio.sleep(0)
        listen.cancel()

    assert "Unrecognized message format" in caplog.text
    assert [r["payload"] for r in received] == [{"n": 1}]


@pytest.mark.asyncio
async def test_listen_requires_connection() -> None:
    socket = AsyncRealtimeClient(URL, "token")

    with pytest.raises(NotConnectedError) as exc_info:
        await socket._listen()

    assert "AsyncRealtimeClient._listen()" in str(exc_info.value)


@pytest.mark.asyncio
async def test_connect_without_auto_reconnect_fails_after_one_attempt() -> None:
    attempts = 0

    async def failing_connect(*args: Any, **kwargs: Any) -> None:
        nonlocal attempts
        attempts += 1
        raise OSError("refused")

    socket = AsyncRealtimeClient(URL, "token", auto_reconnect=False)
    with (
        patch("realtime._async.client.connect", new=failing_connect),
        pytest.raises(OSError, match="refused"),
    ):
        await socket.connect()

    assert attempts == 1


@pytest.mark.asyncio
async def test_connect_retries_with_backoff_until_max_retries() -> None:
    attempts = 0

    async def failing_connect(*args: Any, **kwargs: Any) -> None:
        nonlocal attempts
        attempts += 1
        raise OSError("refused")

    socket = AsyncRealtimeClient(URL, "token", max_retries=3, initial_backoff=1)
    sleep = AsyncMock()
    with (
        patch("realtime._async.client.connect", new=failing_connect),
        patch("realtime._async.client.asyncio.sleep", new=sleep),
        pytest.raises(OSError),
    ):
        await socket.connect()

    assert attempts == 3
    assert [call.args[0] for call in sleep.call_args_list] == [1, 2]


@pytest.mark.asyncio
async def test_connect_with_zero_retries_raises_without_attempting() -> None:
    connect = AsyncMock()
    socket = AsyncRealtimeClient(URL, "token", max_retries=0)

    with (
        patch("realtime._async.client.connect", new=connect),
        pytest.raises(Exception, match="after 0 attempts"),
    ):
        await socket.connect()

    connect.assert_not_called()


@pytest.mark.asyncio
async def test_send_swallows_clean_close() -> None:
    socket, connection = await connected_socket()
    await stop_background_tasks(socket)
    connection.send = AsyncMock(  # type: ignore[method-assign]
        side_effect=websockets.exceptions.ConnectionClosedOK(None, None)
    )

    await socket.send(Message(topic="phoenix", event="heartbeat", payload={}, ref="1"))

    assert socket.is_connected
    await socket.close()


@pytest.mark.asyncio
async def test_send_on_abnormal_close_triggers_connect_error_handling() -> None:
    socket, connection = await connected_socket(auto_reconnect=False)
    await stop_background_tasks(socket)
    connection.send = AsyncMock(  # type: ignore[method-assign]
        side_effect=websockets.exceptions.ConnectionClosedError(None, None)
    )
    channel = socket.channel("room")
    channel._joined_once = True

    with patch("realtime._async.push.AsyncPush.start_timeout"):
        await channel.push("event", {})

    assert not socket.is_connected


@pytest.mark.asyncio
async def test_heartbeat_stops_on_clean_close() -> None:
    socket, connection = await connected_socket()
    await stop_background_tasks(socket)
    connection.send = AsyncMock(  # type: ignore[method-assign]
        side_effect=websockets.exceptions.ConnectionClosedOK(None, None)
    )

    with patch.object(socket, "send", new=AsyncMock(side_effect=connection.send)):
        await asyncio.wait_for(socket._heartbeat(), timeout=1)

    await socket.close()


@pytest.mark.asyncio
async def test_heartbeat_reports_abnormal_close() -> None:
    socket, _ = await connected_socket(auto_reconnect=False)
    await stop_background_tasks(socket)
    error = websockets.exceptions.ConnectionClosedError(None, None)

    with patch.object(socket, "send", new=AsyncMock(side_effect=error)):
        await asyncio.wait_for(socket._heartbeat(), timeout=1)

    assert not socket.is_connected


@pytest.mark.asyncio
async def test_presence_state_reflects_presence_events() -> None:
    socket = AsyncRealtimeClient(URL, "token")
    channel = socket.channel("room")

    channel.presence._on_state_event({"alice": {"metas": [{"phx_ref": "a1"}]}})

    assert channel.presence_state() == {"alice": [{"presence_ref": "a1"}]}


def test_authorization_error_has_default_message() -> None:
    assert str(AuthorizationError()) == "Authorization failed for private channel"
    assert str(AuthorizationError("denied")) == "denied"
