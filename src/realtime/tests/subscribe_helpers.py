import asyncio
from collections.abc import Callable, Coroutine
from typing import Any

from realtime import AsyncRealtimeChannel
from realtime.message import ReplyPostgresChanges
from realtime.types import RealtimeAcknowledgementStatus, RealtimeSubscribeStates

SubscribeCallback = Callable[[RealtimeSubscribeStates, Exception | None], None]


async def start_join(
    channel: AsyncRealtimeChannel,
    join: Coroutine[Any, Any, AsyncRealtimeChannel],
) -> asyncio.Task[AsyncRealtimeChannel]:
    """Run a join until the join message is sent and return the still pending task."""
    task = asyncio.create_task(join)
    await asyncio.sleep(0)
    assert channel.join_push.sent
    return task


async def start_subscribe(
    channel: AsyncRealtimeChannel, callback: SubscribeCallback | None = None
) -> asyncio.Task[AsyncRealtimeChannel]:
    return await start_join(channel, channel.subscribe(callback))


async def subscribe_with_ok_reply(
    channel: AsyncRealtimeChannel, callback: SubscribeCallback | None = None
) -> AsyncRealtimeChannel:
    task = await start_subscribe(channel, callback)
    channel.join_push.trigger(
        RealtimeAcknowledgementStatus.Ok, ReplyPostgresChanges(postgres_changes=[])
    )
    return await task
