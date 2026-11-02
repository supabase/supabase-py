import asyncio
import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

import pytest
from websockets.asyncio.server import ServerConnection, serve
from websockets.datastructures import Headers
from websockets.exceptions import (
    ConnectionClosed,
    ConnectionClosedError,
    ConnectionClosedOK,
)
from websockets.http11 import Request, Response

from realtime import AsyncRealtimeClient
from realtime._async.channel import AsyncRealtimeChannel
from realtime.types import ChannelStates, RealtimeSubscribeStates


class StatusRecorder:
    def __init__(self) -> None:
        self.received: list[tuple[RealtimeSubscribeStates, Exception | None]] = []
        self._changed = asyncio.Event()

    def __call__(
        self, status: RealtimeSubscribeStates, error: Exception | None
    ) -> None:
        self.received.append((status, error))
        self._changed.set()

    @property
    def statuses(self) -> list[RealtimeSubscribeStates]:
        return [status for status, _ in self.received]

    async def wait_for(self, count: int) -> None:
        while len(self.received) < count:
            self._changed.clear()
            await asyncio.wait_for(self._changed.wait(), 5)


@asynccontextmanager
async def dropping_server(
    close_code: int, server_comes_back: bool, drop: asyncio.Event
) -> AsyncIterator[str]:
    connections = 0

    def reject_after_first(
        connection: ServerConnection, request: Request
    ) -> Response | None:
        if connections >= 1 and not server_comes_back:
            return Response(503, "Service Unavailable", Headers())
        return None

    async def handler(connection: ServerConnection) -> None:
        nonlocal connections
        connections += 1
        first = connections == 1
        async for raw in connection:
            message = json.loads(raw)
            if message["event"] != "phx_join":
                continue
            await connection.send(
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
            if first:
                await drop.wait()
                await connection.close(code=close_code, reason="server restarting")
                return

    async with serve(
        handler, "127.0.0.1", 0, process_request=reject_after_first
    ) as server:
        port = next(iter(server.sockets)).getsockname()[1]
        yield f"ws://127.0.0.1:{port}/realtime/v1"


async def shut_down(client: AsyncRealtimeClient, channel: AsyncRealtimeChannel) -> None:
    tasks = [
        task
        for task in (
            channel.rejoin_timer.timer,
            channel.join_push.timeout_task,
            client._listen_task,
            client._heartbeat_task,
        )
        if task is not None
    ]
    channel.rejoin_timer.reset()
    channel.join_push.destroy()
    await client.close()
    await asyncio.gather(*tasks, return_exceptions=True)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("close_code", "error_type"),
    [(1011, ConnectionClosedError), (1000, ConnectionClosedOK)],
)
@pytest.mark.parametrize("server_comes_back", [True, False])
async def test_subscription_callback_reports_dropped_connection(
    close_code: int,
    error_type: type[ConnectionClosed],
    server_comes_back: bool,
) -> None:
    drop = asyncio.Event()
    recorder = StatusRecorder()

    async with dropping_server(close_code, server_comes_back, drop) as url:
        client = AsyncRealtimeClient(
            url, auto_reconnect=True, max_retries=2, initial_backoff=0.01
        )
        channel = client.channel("room")
        try:
            await channel.subscribe(recorder)
            await recorder.wait_for(1)
            listen_task = client._listen_task
            assert listen_task is not None

            drop.set()
            await recorder.wait_for(2)

            assert recorder.received[1][0] == RealtimeSubscribeStates.CHANNEL_ERROR
            assert isinstance(recorder.received[1][1], error_type)

            if server_comes_back:
                await recorder.wait_for(3)
                assert recorder.statuses == [
                    RealtimeSubscribeStates.SUBSCRIBED,
                    RealtimeSubscribeStates.CHANNEL_ERROR,
                    RealtimeSubscribeStates.SUBSCRIBED,
                ]
                assert channel.state == ChannelStates.JOINED
            else:
                await asyncio.wait_for(
                    asyncio.gather(listen_task, return_exceptions=True), 5
                )
                assert recorder.statuses == [
                    RealtimeSubscribeStates.SUBSCRIBED,
                    RealtimeSubscribeStates.CHANNEL_ERROR,
                ]
                assert channel.state == ChannelStates.ERRORED
                assert not client.is_connected
        finally:
            drop.set()
            await shut_down(client, channel)


@pytest.mark.asyncio
@pytest.mark.parametrize(
    ("close_code", "error_type"),
    [(1011, ConnectionClosedError), (1000, ConnectionClosedOK)],
)
async def test_subscription_callback_reports_dropped_connection_without_auto_reconnect(
    close_code: int,
    error_type: type[ConnectionClosed],
) -> None:
    drop = asyncio.Event()
    recorder = StatusRecorder()

    async with dropping_server(close_code, True, drop) as url:
        client = AsyncRealtimeClient(url, auto_reconnect=False)
        channel = client.channel("room")
        try:
            await channel.subscribe(recorder)
            await recorder.wait_for(1)
            listen_task = client._listen_task
            assert listen_task is not None

            drop.set()
            await recorder.wait_for(2)
            await asyncio.wait_for(listen_task, 5)

            assert recorder.statuses == [
                RealtimeSubscribeStates.SUBSCRIBED,
                RealtimeSubscribeStates.CHANNEL_ERROR,
            ]
            assert isinstance(recorder.received[1][1], error_type)
            assert channel.state == ChannelStates.ERRORED
            assert not client.is_connected
        finally:
            drop.set()
            await shut_down(client, channel)
