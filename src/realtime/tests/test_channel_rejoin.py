import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from realtime import AsyncRealtimeClient
from realtime._async.channel import AsyncRealtimeChannel
from realtime.types import ChannelStates, RealtimeAcknowledgementStatus

URL = "ws://localhost/realtime/v1"


class OpenConnection:
    def __init__(self) -> None:
        self.send = AsyncMock()
        self.close = AsyncMock()

    def __aiter__(self) -> "OpenConnection":
        return self

    async def __anext__(self) -> str:
        await asyncio.Event().wait()
        raise StopAsyncIteration


async def connected_socket() -> AsyncRealtimeClient:
    socket = AsyncRealtimeClient(URL, "token")
    socket._ws_connection = AsyncMock()
    await socket.connect()
    return socket


async def start_subscribe(
    channel: AsyncRealtimeChannel,
) -> asyncio.Task[AsyncRealtimeChannel]:
    task = asyncio.create_task(channel.subscribe())
    await asyncio.sleep(0)
    assert channel.join_push.sent
    return task


async def joining_channel(socket: AsyncRealtimeClient) -> AsyncRealtimeChannel:
    channel = socket.channel("rejoin")
    with patch.object(channel.join_push, "start_timeout"):
        await start_subscribe(channel)
    assert channel.is_joining
    return channel


def scheduled_delays(run_timer: AsyncMock) -> list[float]:
    return [call.args[0] for call in run_timer.call_args_list]


@pytest.mark.asyncio
async def test_rejoin_delays_follow_stepped_schedule() -> None:
    socket = await connected_socket()
    channel = await joining_channel(socket)

    with patch.object(channel.rejoin_timer, "_run_timer", new=AsyncMock()) as run:
        for _ in range(6):
            channel.state = ChannelStates.JOINING
            channel.join_push.trigger(RealtimeAcknowledgementStatus.Timeout, {})

        assert scheduled_delays(run) == [1, 2, 5, 10, 10, 10]
        assert channel.is_errored
        channel.rejoin_timer.reset()

    await socket.close()


@pytest.mark.asyncio
async def test_join_error_schedules_rejoin() -> None:
    socket = await connected_socket()
    channel = await joining_channel(socket)

    with patch.object(channel.rejoin_timer, "_run_timer", new=AsyncMock()) as run:
        channel.join_push.trigger(
            RealtimeAcknowledgementStatus.Error, {"reason": "Unauthorized: nope"}
        )

        assert scheduled_delays(run) == [1]
        assert channel.is_errored
        channel.rejoin_timer.reset()

    await socket.close()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "code",
    [
        "ChannelRateLimitReached",
        "ConnectionRateLimitReached",
        "ClientJoinRateLimitReached",
        "DatabaseConnectionRateLimitReached",
    ],
)
async def test_rate_limited_join_error_waits_thirty_seconds(code: str) -> None:
    socket = await connected_socket()
    channel = await joining_channel(socket)

    with patch.object(channel.rejoin_timer, "_run_timer", new=AsyncMock()) as run:
        channel.join_push.trigger(
            RealtimeAcknowledgementStatus.Error, {"reason": f"{code}: slow down"}
        )

        assert scheduled_delays(run) == [30]
        assert channel.rejoin_timer.tries == 1
        channel.rejoin_timer.reset()

    await socket.close()


@pytest.mark.asyncio
async def test_join_failure_does_not_schedule_rejoin_while_disconnected() -> None:
    socket = await connected_socket()
    channel = await joining_channel(socket)
    socket._ws_connection = None

    channel.join_push.trigger(RealtimeAcknowledgementStatus.Timeout, {})

    assert channel.is_errored
    assert channel.rejoin_timer.timer is None


@pytest.mark.asyncio
async def test_rejoin_timer_does_not_reschedule_itself() -> None:
    socket = await connected_socket()
    channel = await joining_channel(socket)
    channel.state = ChannelStates.ERRORED

    with patch.object(channel, "_rejoin", new=AsyncMock()) as rejoin:
        await channel.rejoin_timer.callback()

    rejoin.assert_awaited_once()
    assert channel.rejoin_timer.timer is None
    await socket.close()


@pytest.mark.asyncio
async def test_socket_open_resets_attempts_and_rejoins_errored_channels() -> None:
    socket = await connected_socket()
    errored = await joining_channel(socket)
    errored.state = ChannelStates.ERRORED
    errored.rejoin_timer.tries = 3
    closed = socket.channel("closed")
    closed.rejoin_timer.tries = 2

    with (
        patch.object(errored, "_rejoin", new=AsyncMock()) as rejoin_errored,
        patch.object(closed, "_rejoin", new=AsyncMock()) as rejoin_closed,
    ):
        await socket._on_connect()

    rejoin_errored.assert_awaited_once()
    rejoin_closed.assert_not_awaited()
    assert errored.rejoin_timer.tries == 0
    assert closed.rejoin_timer.tries == 0
    await socket.close()


@pytest.mark.asyncio
async def test_reconnect_rejoins_joined_channels_without_delay() -> None:
    socket = await connected_socket()
    channel = await joining_channel(socket)
    channel.state = ChannelStates.JOINED

    with (
        patch(
            "realtime._async.client.connect",
            new=AsyncMock(return_value=OpenConnection()),
        ),
        patch.object(channel, "_rejoin", new=AsyncMock()) as rejoin,
    ):
        await socket._reconnect(ConnectionError())

    rejoin.assert_awaited_once()
    assert channel.rejoin_timer.timer is None
    await socket.close()


@pytest.mark.asyncio
async def test_reconnect_rejoins_channel_that_a_stale_reply_marked_joined() -> None:
    socket = await connected_socket()
    channel = await joining_channel(socket)
    channel.state = ChannelStates.JOINED

    async def stale_join_reply(*args: object, **kwargs: object) -> OpenConnection:
        channel.state = ChannelStates.JOINED
        return OpenConnection()

    with (
        patch("realtime._async.client.connect", new=stale_join_reply),
        patch.object(channel, "_rejoin", new=AsyncMock()) as rejoin,
    ):
        await socket._reconnect(ConnectionError())

    rejoin.assert_awaited_once()
    assert socket._channels_to_rejoin == []
    await socket.close()


@pytest.mark.asyncio
async def test_reconnect_rejoins_once_after_a_failed_reconnect() -> None:
    socket = await connected_socket()
    channel = await joining_channel(socket)
    channel.state = ChannelStates.JOINED

    with (
        patch("realtime._async.client.connect", side_effect=ConnectionError),
        patch("realtime._async.client.asyncio.sleep", new=AsyncMock()),
        pytest.raises(ConnectionError),
    ):
        await socket._reconnect(ConnectionError())

    channel.state = ChannelStates.JOINED

    with (
        patch(
            "realtime._async.client.connect",
            new=AsyncMock(return_value=OpenConnection()),
        ),
        patch.object(channel, "_rejoin", new=AsyncMock()) as rejoin,
    ):
        await socket._reconnect(ConnectionError())

    rejoin.assert_awaited_once()
    await socket.close()
