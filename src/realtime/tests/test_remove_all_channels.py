import asyncio
import json
from unittest.mock import AsyncMock, patch

import pytest

from realtime import AsyncRealtimeClient
from realtime.types import ChannelEvents, ChannelStates

URL = "ws://localhost/realtime/v1"
TOPICS = ["first", "second", "third"]


class RecordingConnection:
    def __init__(self, reply_to_leave: bool = False) -> None:
        self.sent: list[dict] = []
        self.close = AsyncMock()
        self.reply_to_leave = reply_to_leave
        self.incoming: asyncio.Queue[str] = asyncio.Queue()

    async def send(self, message: str) -> None:
        data = json.loads(message)
        self.sent.append(data)
        if self.reply_to_leave and data["event"] == ChannelEvents.leave:
            reply = {
                "topic": data["topic"],
                "event": ChannelEvents.reply,
                "payload": {"status": "ok", "response": {}},
                "ref": data["ref"],
            }
            await self.incoming.put(json.dumps(reply))
            for _ in range(5):
                await asyncio.sleep(0)

    def __aiter__(self) -> "RecordingConnection":
        return self

    async def __anext__(self) -> str:
        return await self.incoming.get()

    def leaves(self) -> list[str]:
        return [m["topic"] for m in self.sent if m["event"] == ChannelEvents.leave]


async def connected_socket(connection: RecordingConnection) -> AsyncRealtimeClient:
    socket = AsyncRealtimeClient(URL, "token", auto_reconnect=False)
    with patch(
        "realtime._async.client.connect", new=AsyncMock(return_value=connection)
    ):
        await socket.connect()
    for topic in TOPICS:
        socket.channel(topic)
    return socket


@pytest.mark.asyncio
async def test_remove_all_channels_forgets_every_channel() -> None:
    connection = RecordingConnection()
    socket = await connected_socket(connection)

    await socket.remove_all_channels()

    assert socket.get_channels() == []
    assert sorted(connection.leaves()) == sorted(
        f"realtime:{topic}" for topic in TOPICS
    )
    connection.close.assert_awaited_once()
    assert not socket.is_connected


@pytest.mark.asyncio
async def test_channel_after_remove_all_channels_is_fresh() -> None:
    connection = RecordingConnection()
    socket = await connected_socket(connection)
    removed = socket.get_channels()[0]

    await socket.remove_all_channels()
    fresh = socket.channel("first")

    assert fresh is not removed
    assert fresh.is_closed
    assert socket.get_channels() == [fresh]


@pytest.mark.asyncio
async def test_remove_all_channels_survives_leave_replies_during_removal() -> None:
    connection = RecordingConnection(reply_to_leave=True)
    socket = await connected_socket(connection)

    await socket.remove_all_channels()

    assert socket.get_channels() == []
    assert sorted(connection.leaves()) == sorted(
        f"realtime:{topic}" for topic in TOPICS
    )
    connection.close.assert_awaited_once()


@pytest.mark.asyncio
async def test_remove_all_channels_continues_when_unsubscribe_fails() -> None:
    connection = RecordingConnection()
    socket = await connected_socket(connection)
    failing = socket.get_channels()[0]

    with (
        patch.object(failing, "unsubscribe", side_effect=ConnectionError),
        pytest.raises(ConnectionError),
    ):
        await socket.remove_all_channels()

    assert socket.get_channels() == []
    assert sorted(connection.leaves()) == ["realtime:second", "realtime:third"]
    connection.close.assert_awaited_once()
    assert not socket.is_connected


@pytest.mark.asyncio
async def test_remove_all_channels_forgets_every_channel_when_cancelled() -> None:
    connection = RecordingConnection()
    socket = await connected_socket(connection)
    cancelled, errored, _ = socket.get_channels()
    errored.state = ChannelStates.ERRORED
    errored.rejoin_timer.schedule_timeout()

    with (
        patch.object(cancelled, "unsubscribe", side_effect=asyncio.CancelledError),
        pytest.raises(asyncio.CancelledError),
    ):
        await socket.remove_all_channels()

    assert socket.get_channels() == []
    assert errored.rejoin_timer.timer is None
    assert errored.is_closed
    connection.close.assert_awaited_once()
