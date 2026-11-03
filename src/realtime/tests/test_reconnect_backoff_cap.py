from unittest.mock import AsyncMock, patch

import pytest

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
