import asyncio
import json
import socket
from unittest.mock import AsyncMock, patch

import pytest
from websockets.asyncio.server import serve

from realtime import AsyncRealtimeClient, RealtimeSubscribeStates


@pytest.mark.parametrize("concurrent", [False, True])
def test_initial_subscriptions_share_one_connection(concurrent: bool) -> None:
    with socket.socket() as listener:
        listener.bind(("127.0.0.1", 0))
        listener.setblocking(False)
        port = listener.getsockname()[1]
        client = AsyncRealtimeClient(f"ws://127.0.0.1:{port}", auto_reconnect=False)
        asyncio.run(subscribe_channels(client, concurrent, listener))


async def subscribe_channels(
    client: AsyncRealtimeClient, concurrent: bool, listener: socket.socket
) -> None:
    first_handshake = asyncio.Event()
    release_handshake = asyncio.Event()
    second_started = asyncio.Event()
    joins_received = asyncio.Event()
    joined = asyncio.Event()
    connections = []
    joins = []
    states = []
    tasks = []

    async def process_request(connection, request):
        first_handshake.set()
        if concurrent:
            await release_handshake.wait()

    async def handle(connection):
        connections.append(connection)
        async for data in connection:
            message = json.loads(data)
            if message["event"] == "phx_join":
                joins.append(message["topic"])
                if len(joins) == 2:
                    joins_received.set()
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

    def on_subscribe(state, error):
        states.append((state, error))
        if len(states) == 2:
            joined.set()

    async with serve(handle, sock=listener, process_request=process_request):
        channels = [client.channel("a"), client.channel("b")]
        try:
            if concurrent:
                tasks.append(asyncio.create_task(channels[0].subscribe(on_subscribe)))
                await asyncio.wait_for(first_handshake.wait(), 2)

                async def subscribe_second():
                    second_started.set()
                    await channels[1].subscribe(on_subscribe)

                tasks.append(asyncio.create_task(subscribe_second()))
                await asyncio.wait_for(second_started.wait(), 2)
                release_handshake.set()
                await asyncio.wait_for(asyncio.gather(*tasks), 2)
            else:
                await channels[0].subscribe(on_subscribe)
                await channels[1].subscribe(on_subscribe)

            await asyncio.wait_for(joins_received.wait(), 2)
            await client.close()
            open_connections = [c for c in connections if c.close_code is None]
            for connection in open_connections:
                pong = await connection.ping()
                await asyncio.wait_for(pong, 2)

            assert (len(connections), len(open_connections)) == (1, 0)
            assert sorted(joins) == ["realtime:a", "realtime:b"]
            await asyncio.wait_for(joined.wait(), 2)
            assert states == [(RealtimeSubscribeStates.SUBSCRIBED, None)] * 2
        finally:
            release_handshake.set()
            background_tasks = [client._listen_task, client._heartbeat_task]
            for channel in channels:
                background_tasks.append(channel.join_push.timeout_task)
                channel.join_push.destroy()
            for task in tasks:
                task.cancel()
            await client.close()
            await asyncio.gather(
                *[task for task in [*tasks, *background_tasks] if task is not None],
                return_exceptions=True,
            )
            for connection in connections:
                await connection.close()


@pytest.mark.asyncio
async def test_cancelling_waiter_does_not_cancel_connection() -> None:
    opening = asyncio.Event()
    release = asyncio.Event()
    waiting = asyncio.Event()
    transport = AsyncMock()
    client = AsyncRealtimeClient("ws://localhost", auto_reconnect=False)

    async def open_connection(url):
        opening.set()
        await release.wait()
        return transport

    async def connect_waiter():
        waiting.set()
        await client.connect()

    with (
        patch(
            "realtime._async.client.connect",
            new_callable=AsyncMock,
            side_effect=open_connection,
        ) as connect,
        patch.object(client, "_on_connect", new_callable=AsyncMock),
    ):
        owner = asyncio.create_task(client.connect())
        waiter = None
        try:
            await asyncio.wait_for(opening.wait(), 2)
            waiter = asyncio.create_task(connect_waiter())
            await asyncio.wait_for(waiting.wait(), 2)
            waiter.cancel()
            with pytest.raises(asyncio.CancelledError):
                await waiter
            assert not owner.done()
            release.set()
            await asyncio.wait_for(owner, 2)
            await asyncio.wait_for(client.connect(), 2)
            assert client.is_connected
            assert connect.await_count == 1
        finally:
            release.set()
            owner.cancel()
            if waiter is not None:
                waiter.cancel()
            await asyncio.gather(
                *[task for task in [owner, waiter] if task is not None],
                return_exceptions=True,
            )
            await client.close()


@pytest.mark.asyncio
async def test_failed_handshake_can_retry() -> None:
    client = AsyncRealtimeClient("ws://localhost", initial_backoff=0, max_retries=2)
    transport = AsyncMock()
    with (
        patch(
            "realtime._async.client.connect",
            new_callable=AsyncMock,
            side_effect=[OSError("handshake failed"), transport],
        ) as connect,
        patch.object(client, "_on_connect", new_callable=AsyncMock),
    ):
        try:
            await asyncio.wait_for(client.connect(), 2)
            assert client.is_connected
            assert connect.await_count == 2
        finally:
            await client.close()
