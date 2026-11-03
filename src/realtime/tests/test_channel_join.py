import asyncio
import json
import logging
from unittest.mock import patch

import pytest

from realtime import AsyncRealtimeClient
from realtime.message import ReplyPostgresChanges
from realtime.types import ChannelStates, RealtimeAcknowledgementStatus

URL = "ws://localhost/realtime/v1"


class RecordingConnection:
    def __init__(self) -> None:
        self.sent: list[dict] = []

    async def send(self, data: str) -> None:
        self.sent.append(json.loads(data))

    async def close(self) -> None:
        pass

    def __aiter__(self) -> "RecordingConnection":
        return self

    async def __anext__(self) -> str:
        await asyncio.Event().wait()
        raise StopAsyncIteration


async def connected_socket(connection: RecordingConnection) -> AsyncRealtimeClient:
    socket = AsyncRealtimeClient(URL, "apikey")

    async def fake_connect(*args, **kwargs) -> RecordingConnection:
        return connection

    with patch("realtime._async.client.connect", side_effect=fake_connect):
        await socket.connect()
    return socket


def join_messages(connection: RecordingConnection) -> list[dict]:
    return [message for message in connection.sent if message["event"] == "phx_join"]


@pytest.mark.asyncio
async def test_join_sends_single_level_config_with_access_token() -> None:
    connection = RecordingConnection()
    socket = await connected_socket(connection)
    socket.access_token = "user-jwt"
    channel = socket.channel(
        "room",
        params={
            "config": {
                "broadcast": {"ack": False, "self": False},
                "presence": {"key": "", "enabled": False},
                "private": True,
            }
        },
    )

    with patch.object(channel.join_push, "start_timeout"):
        result = await channel.join()

    assert result is channel
    [message] = join_messages(connection)
    assert message["topic"] == "realtime:room"
    assert message["payload"]["access_token"] == "user-jwt"
    config = message["payload"]["config"]
    assert "config" not in config
    assert config["private"] is True
    assert config["postgres_changes"] == []

    await socket.close()


@pytest.mark.asyncio
async def test_join_omits_access_token_when_socket_has_none() -> None:
    connection = RecordingConnection()
    socket = await connected_socket(connection)
    socket.access_token = None
    channel = socket.channel("room")

    with patch.object(channel.join_push, "start_timeout"):
        await channel.join()

    [message] = join_messages(connection)
    assert "access_token" not in message["payload"]
    assert "config" not in message["payload"]["config"]

    await socket.close()


@pytest.mark.asyncio
async def test_join_goes_through_join_push() -> None:
    connection = RecordingConnection()
    socket = await connected_socket(connection)
    channel = socket.channel("room")

    with patch.object(channel.join_push, "start_timeout") as start_timeout:
        await channel.join()

    start_timeout.assert_called_once()
    assert channel.is_joining
    assert channel._joined_once
    [message] = join_messages(connection)
    assert message["ref"] == channel.join_push.ref
    assert message["join_ref"] == channel.join_push.ref

    channel.join_push.trigger(
        RealtimeAcknowledgementStatus.Ok, ReplyPostgresChanges(postgres_changes=[])
    )
    assert channel.state == ChannelStates.JOINED

    with pytest.raises(Exception, match="subscribe multiple times"):
        await channel.join()

    await socket.close()


@pytest.mark.asyncio
async def test_join_timeout_reports_errored_state() -> None:
    connection = RecordingConnection()
    socket = await connected_socket(connection)
    channel = socket.channel("room")

    with patch.object(channel.join_push, "start_timeout"):
        await channel.join()

    with patch.object(channel.rejoin_timer, "schedule_timeout") as schedule:
        channel.join_push.trigger(RealtimeAcknowledgementStatus.Timeout, {})

    assert channel.is_errored
    schedule.assert_called_once()

    await socket.close()


@pytest.mark.asyncio
async def test_join_logs_deprecation_warning(
    caplog: pytest.LogCaptureFixture,
) -> None:
    connection = RecordingConnection()
    socket = await connected_socket(connection)
    channel = socket.channel("room")

    with (
        caplog.at_level(logging.WARNING, logger="realtime._async.channel"),
        patch.object(channel.join_push, "start_timeout"),
    ):
        await channel.join()

    assert any(
        "AsyncRealtimeChannel.join is deprecated" in record.getMessage()
        and "subscribe" in record.getMessage()
        for record in caplog.records
        if record.levelno == logging.WARNING
    )

    await socket.close()


@pytest.mark.asyncio
async def test_subscribe_does_not_log_deprecation_warning(
    caplog: pytest.LogCaptureFixture,
) -> None:
    connection = RecordingConnection()
    socket = await connected_socket(connection)
    channel = socket.channel("room")

    with (
        caplog.at_level(logging.WARNING, logger="realtime._async.channel"),
        patch.object(channel.join_push, "start_timeout"),
    ):
        await channel.subscribe()

    assert not any("deprecated" in record.getMessage() for record in caplog.records)

    await socket.close()


@pytest.mark.asyncio
async def test_join_connects_socket_when_disconnected() -> None:
    connection = RecordingConnection()
    socket = AsyncRealtimeClient(URL, "apikey")
    channel = socket.channel("room")

    async def fake_connect(*args, **kwargs) -> RecordingConnection:
        return connection

    with (
        patch("realtime._async.client.connect", side_effect=fake_connect),
        patch.object(channel.join_push, "start_timeout"),
    ):
        await channel.join()

    assert socket.is_connected
    assert len(join_messages(connection)) == 1
    assert channel.subscribe_callback is None
    channel.join_push.trigger(
        RealtimeAcknowledgementStatus.Ok, ReplyPostgresChanges(postgres_changes=[])
    )
    assert channel.is_joined

    await socket.close()
