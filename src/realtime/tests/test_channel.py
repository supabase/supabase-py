import asyncio
from typing import Any, Optional, cast

import pytest

from realtime import AsyncRealtimeClient
from realtime.message import ReplyPostgresChanges
from realtime.types import RealtimeAcknowledgementStatus, RealtimeSubscribeStates


@pytest.mark.asyncio
async def test_subscribe_waits_for_ack_before_returning():
    socket = AsyncRealtimeClient("ws://localhost:54321/realtime/v1", "test-key")
    socket._ws_connection = cast(
        Any, object()
    )  # mark socket as connected without network traffic
    channel = socket.channel("test-channel")

    subscribed = asyncio.Event()

    def on_subscribe(state: RealtimeSubscribeStates, error: Optional[Exception]):
        if state == RealtimeSubscribeStates.SUBSCRIBED and error is None:
            subscribed.set()

    async def fake_rejoin():
        async def delayed_ack():
            await asyncio.sleep(0.05)
            channel.join_push.trigger(
                RealtimeAcknowledgementStatus.Ok,
                ReplyPostgresChanges(postgres_changes=[]),
            )

        asyncio.create_task(delayed_ack())

    channel._rejoin = fake_rejoin  # type: ignore[method-assign]

    subscribe_task = asyncio.create_task(channel.subscribe(on_subscribe))

    await asyncio.sleep(0.01)
    assert not subscribe_task.done()

    await asyncio.wait_for(subscribe_task, 1)
    assert subscribed.is_set()


@pytest.mark.asyncio
async def test_subscribe_propagates_callback_errors():
    socket = AsyncRealtimeClient("ws://localhost:54321/realtime/v1", "test-key")
    socket._ws_connection = cast(
        Any, object()
    )  # mark socket as connected without network traffic
    channel = socket.channel("test-channel")

    async def fake_rejoin():
        async def delayed_ack():
            await asyncio.sleep(0.01)
            channel.join_push.trigger(
                RealtimeAcknowledgementStatus.Ok,
                ReplyPostgresChanges(postgres_changes=[]),
            )

        asyncio.create_task(delayed_ack())

    channel._rejoin = fake_rejoin  # type: ignore[method-assign]

    def raising_callback(state: RealtimeSubscribeStates, error: Optional[Exception]):
        if state == RealtimeSubscribeStates.SUBSCRIBED and error is None:
            raise RuntimeError("subscribe callback failed")

    with pytest.raises(RuntimeError, match="subscribe callback failed"):
        await channel.subscribe(raising_callback)
