import asyncio
import json
from unittest.mock import patch

import pytest
from subscribe_helpers import start_join

from realtime import AsyncRealtimeClient
from realtime.message import ReplyPostgresChanges
from realtime.types import ChannelStates, RealtimeAcknowledgementStatus

URL = "ws://localhost/realtime/v1"

pytestmark = pytest.mark.filterwarnings("ignore::DeprecationWarning")


class RecordingConnection:
    def __init__(self, auto_reply: bool = False) -> None:
        self.sent: list[dict] = []
        self.auto_reply = auto_reply
        self.incoming: asyncio.Queue[str] = asyncio.Queue()

    async def send(self, data: str) -> None:
        message = json.loads(data)
        self.sent.append(message)
        if self.auto_reply and message["event"] == "phx_join":
            self.incoming.put_nowait(
                json.dumps(
                    {
                        "event": "phx_reply",
                        "topic": message["topic"],
                        "ref": message["ref"],
                        "payload": {
                            "status": "ok",
                            "response": {"postgres_changes": []},
                        },
                    }
                )
            )

    async def close(self) -> None:
        pass

    def __aiter__(self) -> "RecordingConnection":
        return self

    async def __anext__(self) -> str:
        return await self.incoming.get()


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
        task = await start_join(channel, channel.join())

    assert not task.done()
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
        await start_join(channel, channel.join())

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
        task = await start_join(channel, channel.join())

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
    assert await task is channel

    assert await channel.join() is channel
    assert len(join_messages(connection)) == 1
    assert channel.is_joined

    await socket.close()


@pytest.mark.asyncio
async def test_join_after_subscribe_does_not_raise_or_rejoin() -> None:
    connection = RecordingConnection()
    socket = await connected_socket(connection)
    channel = socket.channel("room")

    with patch.object(channel.join_push, "start_timeout"):
        subscribe = await start_join(channel, channel.subscribe())
        join = asyncio.create_task(channel.join())
        await asyncio.sleep(0)
        assert not join.done()

        channel.join_push.trigger(
            RealtimeAcknowledgementStatus.Ok, ReplyPostgresChanges(postgres_changes=[])
        )
        assert await join is channel
        assert await subscribe is channel

    assert len(join_messages(connection)) == 1

    await socket.close()


@pytest.mark.asyncio
async def test_join_timeout_reports_errored_state() -> None:
    connection = RecordingConnection()
    socket = await connected_socket(connection)
    channel = socket.channel("room")

    with patch.object(channel.join_push, "start_timeout"):
        task = await start_join(channel, channel.join())

    with patch.object(channel.rejoin_timer, "schedule_timeout") as schedule:
        channel.join_push.trigger(RealtimeAcknowledgementStatus.Timeout, {})

    assert channel.is_errored
    schedule.assert_called_once()
    assert await task is channel

    await socket.close()


@pytest.mark.asyncio
async def test_join_emits_deprecation_warning() -> None:
    connection = RecordingConnection(auto_reply=True)
    socket = await connected_socket(connection)
    channel = socket.channel("room")

    with (
        pytest.warns(DeprecationWarning, match=r"join\(\) is deprecated") as record,
    ):
        await channel.join()

    assert "subscribe()" in str(record[0].message)
    assert record[0].filename == __file__

    await socket.close()


@pytest.mark.asyncio
@pytest.mark.filterwarnings("error::DeprecationWarning")
async def test_subscribe_does_not_emit_deprecation_warning() -> None:
    connection = RecordingConnection(auto_reply=True)
    socket = await connected_socket(connection)
    channel = socket.channel("room")

    await channel.subscribe()
    assert channel.is_joined

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
        task = await start_join(channel, channel.join())

    assert socket.is_connected
    assert len(join_messages(connection)) == 1
    assert channel.subscribe_callback is None
    channel.join_push.trigger(
        RealtimeAcknowledgementStatus.Ok, ReplyPostgresChanges(postgres_changes=[])
    )
    assert channel.is_joined
    assert await task is channel

    await socket.close()
