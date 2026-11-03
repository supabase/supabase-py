import asyncio
import json
from collections.abc import AsyncIterator, Awaitable, Callable
from contextlib import asynccontextmanager
from typing import Any
from unittest.mock import patch

import pytest
from websockets.asyncio.server import ServerConnection, serve

from realtime import AsyncRealtimeClient
from realtime.types import ChannelStates, RealtimeSubscribeStates

Statuses = list[tuple[RealtimeSubscribeStates, Exception | None]]
JoinHandler = Callable[[ServerConnection, dict[str, Any]], Awaitable[None]]


async def reply(
    connection: ServerConnection,
    message: dict[str, Any],
    status: str,
    response: dict[str, Any],
) -> None:
    await connection.send(
        json.dumps(
            {
                "event": "phx_reply",
                "topic": message["topic"],
                "ref": message["ref"],
                "payload": {"status": status, "response": response},
            }
        )
    )


@asynccontextmanager
async def realtime_server(
    on_join: JoinHandler,
    join_received: asyncio.Event | None = None,
    **client_options: Any,
) -> AsyncIterator[AsyncRealtimeClient]:
    async def handler(connection: ServerConnection) -> None:
        async for raw in connection:
            message = json.loads(raw)
            if message["event"] == "phx_join":
                if join_received:
                    join_received.set()
                await on_join(connection, message)
            elif message["event"] == "phx_leave":
                await reply(connection, message, "ok", {})

    async with serve(handler, "127.0.0.1", 0) as server:
        port = next(iter(server.sockets)).getsockname()[1]
        client = AsyncRealtimeClient(
            f"ws://127.0.0.1:{port}/realtime/v1", auto_reconnect=False, **client_options
        )
        try:
            yield client
        finally:
            await client.close()


def recorder(statuses: Statuses) -> Callable[[RealtimeSubscribeStates, Any], None]:
    return lambda status, error: statuses.append((status, error))


@pytest.mark.asyncio
async def test_subscribe_returns_after_ok_reply() -> None:
    async def on_join(connection: ServerConnection, message: dict[str, Any]) -> None:
        await asyncio.sleep(0.2)
        await reply(connection, message, "ok", {"postgres_changes": []})

    statuses: Statuses = []
    async with realtime_server(on_join) as client:
        channel = client.channel("room")
        assert await channel.subscribe(recorder(statuses)) is channel

        assert statuses == [(RealtimeSubscribeStates.SUBSCRIBED, None)]
        assert channel.is_joined
        assert channel._subscribe_waiter is None


@pytest.mark.asyncio
async def test_subscribe_returns_after_ok_reply_without_callback() -> None:
    async def on_join(connection: ServerConnection, message: dict[str, Any]) -> None:
        await asyncio.sleep(0.2)
        await reply(connection, message, "ok", {"postgres_changes": []})

    async with realtime_server(on_join) as client:
        channel = await client.channel("room").subscribe()

        assert channel.is_joined


@pytest.mark.asyncio
async def test_subscribe_returns_after_error_reply() -> None:
    async def on_join(connection: ServerConnection, message: dict[str, Any]) -> None:
        await reply(connection, message, "error", {"reason": "Unauthorized"})

    statuses: Statuses = []
    async with realtime_server(on_join) as client:
        channel = client.channel("room")
        await channel.subscribe(recorder(statuses))

        [(status, error)] = statuses
        assert status == RealtimeSubscribeStates.CHANNEL_ERROR
        assert isinstance(error, Exception)
        assert json.loads(str(error)) == {"reason": "Unauthorized"}
        assert channel.is_errored


@pytest.mark.asyncio
async def test_subscribe_returns_after_join_timeout() -> None:
    async def on_join(connection: ServerConnection, message: dict[str, Any]) -> None:
        pass

    statuses: Statuses = []
    async with realtime_server(on_join, timeout=1) as client:
        channel = client.channel("room")
        loop = asyncio.get_running_loop()
        started = loop.time()
        await channel.subscribe(recorder(statuses))

        assert loop.time() - started >= 0.9
        assert statuses == [(RealtimeSubscribeStates.TIMED_OUT, None)]
        assert channel.is_errored


@pytest.mark.asyncio
@pytest.mark.filterwarnings("ignore::DeprecationWarning")
async def test_cancelled_subscribe_keeps_joining_in_background() -> None:
    release = asyncio.Event()

    async def on_join(connection: ServerConnection, message: dict[str, Any]) -> None:
        await release.wait()
        await reply(connection, message, "ok", {"postgres_changes": []})

    statuses: Statuses = []
    joined = asyncio.Event()

    def on_status(status: RealtimeSubscribeStates, error: Exception | None) -> None:
        statuses.append((status, error))
        joined.set()

    join_received = asyncio.Event()
    async with realtime_server(on_join, join_received) as client:
        channel = client.channel("room")
        task = asyncio.create_task(channel.subscribe(on_status))
        await asyncio.wait_for(join_received.wait(), 2)

        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task
        assert channel.is_joining
        join = asyncio.create_task(channel.join())
        await asyncio.sleep(0.1)
        assert not join.done()

        release.set()
        await asyncio.wait_for(joined.wait(), 2)
        assert await asyncio.wait_for(join, 2) is channel
        assert channel.is_joined
        assert channel._subscribe_waiter is None
        assert statuses == [(RealtimeSubscribeStates.SUBSCRIBED, None)]


@pytest.mark.asyncio
async def test_unsubscribe_during_join_releases_subscribe() -> None:
    async def on_join(connection: ServerConnection, message: dict[str, Any]) -> None:
        pass

    statuses: Statuses = []
    closed = asyncio.Event()

    def on_status(status: RealtimeSubscribeStates, error: Exception | None) -> None:
        statuses.append((status, error))
        closed.set()

    join_received = asyncio.Event()
    async with realtime_server(on_join, join_received) as client:
        channel = client.channel("room")
        task = asyncio.create_task(channel.subscribe(on_status))
        await asyncio.wait_for(join_received.wait(), 2)

        await channel.unsubscribe()

        assert await asyncio.wait_for(task, 2) is channel
        await asyncio.wait_for(closed.wait(), 2)
        assert statuses == [(RealtimeSubscribeStates.CLOSED, None)]
        assert channel.state == ChannelStates.CLOSED


@pytest.mark.asyncio
async def test_socket_closed_during_join_releases_subscribe() -> None:
    async def on_join(connection: ServerConnection, message: dict[str, Any]) -> None:
        await connection.close()

    statuses: Statuses = []
    async with realtime_server(on_join) as client:
        channel = client.channel("room")
        await asyncio.wait_for(channel.subscribe(recorder(statuses)), 2)

        assert [status for status, _ in statuses] == [
            RealtimeSubscribeStates.CHANNEL_ERROR
        ]
        assert channel.is_errored


async def never_reply(connection: ServerConnection, message: dict[str, Any]) -> None:
    pass


@pytest.mark.asyncio
async def test_client_close_during_join_releases_subscribe() -> None:
    join_received = asyncio.Event()
    async with realtime_server(never_reply, join_received) as client:
        channel = client.channel("room")
        task = asyncio.create_task(channel.subscribe())
        await asyncio.wait_for(join_received.wait(), 2)

        await client.close()

        assert await asyncio.wait_for(task, 2) is channel


@pytest.mark.asyncio
async def test_remove_channel_during_join_releases_subscribe() -> None:
    join_received = asyncio.Event()
    async with realtime_server(never_reply, join_received) as client:
        channel = client.channel("room")
        task = asyncio.create_task(channel.subscribe())
        await asyncio.wait_for(join_received.wait(), 2)

        await client.remove_channel(channel)

        assert await asyncio.wait_for(task, 2) is channel


@pytest.mark.asyncio
async def test_cancelled_remove_all_channels_releases_remaining_subscribes() -> None:
    join_received = asyncio.Event()
    async with realtime_server(never_reply, join_received) as client:
        first = client.channel("first")
        second = client.channel("second")
        first_task = asyncio.create_task(first.subscribe())
        await asyncio.wait_for(join_received.wait(), 2)
        join_received.clear()
        second_task = asyncio.create_task(second.subscribe())
        await asyncio.wait_for(join_received.wait(), 2)

        with (
            patch.object(first, "unsubscribe", side_effect=asyncio.CancelledError),
            pytest.raises(asyncio.CancelledError),
        ):
            await client.remove_all_channels()

        assert await asyncio.wait_for(second_task, 2) is second
        assert second.is_closed
        first_task.cancel()


@pytest.mark.asyncio
@pytest.mark.filterwarnings("ignore::DeprecationWarning")
async def test_join_waits_for_pending_subscribe() -> None:
    release = asyncio.Event()

    async def on_join(connection: ServerConnection, message: dict[str, Any]) -> None:
        await release.wait()
        await reply(connection, message, "ok", {"postgres_changes": []})

    join_received = asyncio.Event()
    async with realtime_server(on_join, join_received) as client:
        channel = client.channel("room")
        subscribe_task = asyncio.create_task(channel.subscribe())
        await asyncio.wait_for(join_received.wait(), 2)
        join_task = asyncio.create_task(channel.join())
        await asyncio.sleep(0.1)
        assert not join_task.done()

        release.set()

        assert await asyncio.wait_for(join_task, 2) is channel
        assert await subscribe_task is channel
        assert channel.is_joined


@pytest.mark.asyncio
@pytest.mark.filterwarnings("ignore::DeprecationWarning")
async def test_cancelling_subscribe_does_not_cancel_a_waiting_join() -> None:
    release = asyncio.Event()

    async def on_join(connection: ServerConnection, message: dict[str, Any]) -> None:
        await release.wait()
        await reply(connection, message, "ok", {"postgres_changes": []})

    join_received = asyncio.Event()
    async with realtime_server(on_join, join_received) as client:
        channel = client.channel("room")
        subscribe_task = asyncio.create_task(channel.subscribe())
        await asyncio.wait_for(join_received.wait(), 2)
        join_task = asyncio.create_task(channel.join())
        await asyncio.sleep(0.1)

        subscribe_task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await subscribe_task
        await asyncio.sleep(0.1)
        assert not join_task.done()

        release.set()
        assert await asyncio.wait_for(join_task, 2) is channel
        assert channel.is_joined


@pytest.mark.asyncio
async def test_raising_callback_does_not_block_other_channels_on_socket_error() -> None:
    def raising(status: RealtimeSubscribeStates, error: Exception | None) -> None:
        raise RuntimeError("callback failed")

    statuses: Statuses = []
    join_received = asyncio.Event()
    async with realtime_server(never_reply, join_received) as client:
        first = client.channel("first")
        second = client.channel("second")
        first_task = asyncio.create_task(first.subscribe(raising))
        await asyncio.wait_for(join_received.wait(), 2)
        join_received.clear()
        second_task = asyncio.create_task(second.subscribe(recorder(statuses)))
        await asyncio.wait_for(join_received.wait(), 2)

        client._set_channels_errored(Exception("dropped"))

        assert await asyncio.wait_for(first_task, 2) is first
        assert await asyncio.wait_for(second_task, 2) is second
        assert [status for status, _ in statuses] == [
            RealtimeSubscribeStates.CHANNEL_ERROR
        ]
        assert first.is_errored
        assert second.is_errored
