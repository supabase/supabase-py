from unittest.mock import AsyncMock, patch

import pytest

from realtime._async.channel import MAX_REJOIN_BACKOFF_SECONDS
from realtime._async.client import AsyncRealtimeClient


@pytest.mark.asyncio
async def test_connect_caps_each_retry_delay_at_sixty_seconds() -> None:
    client = AsyncRealtimeClient(
        "ws://localhost/realtime/v1", "token", max_retries=4, initial_backoff=40
    )
    sleep = AsyncMock()

    with (
        patch("realtime._async.client.connect", side_effect=ConnectionError),
        patch("realtime._async.client.asyncio.sleep", sleep),
        pytest.raises(ConnectionError),
    ):
        await client.connect()

    assert [call.args[0] for call in sleep.await_args_list] == [40, 60, 60]


@pytest.mark.asyncio
async def test_channel_rejoin_backoff_is_capped() -> None:
    client = AsyncRealtimeClient("ws://localhost/realtime/v1", "token")
    rejoin_backoff = client.channel("rejoin-cap").rejoin_timer.timer_calc

    # small retry counts still grow exponentially
    assert rejoin_backoff(1) == 2
    assert rejoin_backoff(3) == 8
    # large retry counts are clamped instead of growing without bound
    assert rejoin_backoff(20) == MAX_REJOIN_BACKOFF_SECONDS
    assert MAX_REJOIN_BACKOFF_SECONDS == 60
