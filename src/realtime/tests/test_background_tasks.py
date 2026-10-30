import asyncio
from unittest.mock import AsyncMock, patch

import pytest

from realtime import AsyncRealtimeClient
from realtime.types import ChannelStates


@pytest.mark.asyncio
async def test_resubscribe_task_is_kept_until_it_finishes() -> None:
    socket = AsyncRealtimeClient("ws://127.0.0.1:54321/realtime/v1", "key")
    channel = socket.channel("background-tasks")
    channel.state = ChannelStates.JOINED

    with patch.object(channel, "_resubscribe", new=AsyncMock()) as resubscribe:
        channel.on_presence_sync(lambda: None)

        assert len(channel._background_tasks) == 1
        await asyncio.gather(*channel._background_tasks)
        await asyncio.sleep(0)

    resubscribe.assert_awaited_once()
    assert channel._background_tasks == set()
