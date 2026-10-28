import asyncio
import json
from typing import Optional

import pytest
from websockets.asyncio.server import ServerConnection, serve

from realtime import AsyncRealtimeClient
from realtime.types import ChannelStates, RealtimeSubscribeStates


@pytest.mark.asyncio
@pytest.mark.parametrize("with_callback", [True, False])
@pytest.mark.parametrize(
    "event, expected_status, expected_state",
    [
        ("phx_error", RealtimeSubscribeStates.CHANNEL_ERROR, ChannelStates.ERRORED),
        ("phx_close", RealtimeSubscribeStates.CLOSED, ChannelStates.CLOSED),
        ("unsubscribe", RealtimeSubscribeStates.CLOSED, ChannelStates.CLOSED),
    ],
)
async def test_subscription_callback_receives_channel_status(
    event: str,
    expected_status: RealtimeSubscribeStates,
    expected_state: ChannelStates,
    with_callback: bool,
) -> None:
    joined = asyncio.Event()
    advance = asyncio.Event()
    processed = asyncio.Event()
    received: list[tuple[RealtimeSubscribeStates, Optional[Exception]]] = []

    def on_status(status: RealtimeSubscribeStates, error: Optional[Exception]) -> None:
        received.append((status, error))

    async def barrier(connection: ServerConnection, name: str) -> None:
        await connection.send(
            json.dumps(
                {
                    "event": "broadcast",
                    "topic": "realtime:barrier",
                    "ref": None,
                    "payload": {"event": name, "payload": {}},
                }
            )
        )

    async def handler(connection: ServerConnection) -> None:
        async for raw in connection:
            message = json.loads(raw)
            if message["event"] not in ("phx_join", "phx_leave"):
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
            if message["event"] == "phx_join":
                await barrier(connection, "joined")
                await advance.wait()
                if event == "unsubscribe":
                    continue

            await connection.send(
                json.dumps(
                    {
                        "event": "phx_close" if event == "unsubscribe" else event,
                        "topic": message["topic"],
                        "ref": message["ref"],
                        "join_ref": message["join_ref"],
                        "payload": {},
                    }
                )
            )
            await barrier(connection, "processed")

    async with serve(handler, "127.0.0.1", 0) as server:
        port = next(iter(server.sockets)).getsockname()[1]
        client = AsyncRealtimeClient(
            f"ws://127.0.0.1:{port}/realtime/v1", auto_reconnect=False
        )
        channel = client.channel("room")
        client.channel("barrier").on_broadcast(
            "joined", lambda payload: joined.set()
        ).on_broadcast("processed", lambda payload: processed.set())
        try:
            await channel.subscribe(on_status if with_callback else None)
            await asyncio.wait_for(joined.wait(), 2)
            if with_callback:
                assert received == [(RealtimeSubscribeStates.SUBSCRIBED, None)]
                with pytest.raises(Exception, match="subscribe multiple times"):
                    await channel.subscribe(lambda status, error: None)

            advance.set()
            if event == "unsubscribe":
                await channel.unsubscribe()
            await asyncio.wait_for(processed.wait(), 2)

            assert channel.state == expected_state
            if with_callback:
                assert [status for status, error in received] == [
                    RealtimeSubscribeStates.SUBSCRIBED,
                    expected_status,
                ]
                error = received[-1][1]
                if event == "phx_error":
                    assert isinstance(error, Exception)
                    assert str(error) == "{}"
                else:
                    assert error is None
            else:
                assert received == []
        finally:
            advance.set()
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
