from unittest.mock import AsyncMock, patch

import pytest

from realtime.client import (
    MaxRetriesExceeded,
    automatically_reconnect,
    exponential_delay,
)


def test_exponential_delay_caps_each_retry_at_sixty_seconds() -> None:
    delays = [exponential_delay(10, retry) for retry in range(1, 10)]
    assert delays == [2, 4, 8, 16, 32, 60, 60, 60, 60]
    assert exponential_delay(10, 10) is None


async def test_automatically_reconnect_caps_each_retry_delay_at_sixty_seconds() -> None:
    async def get_token() -> str:
        return "token"

    async def client_handler(client: object) -> None:
        return

    sleep = AsyncMock()

    with (
        patch("realtime.client.websockets.connect", side_effect=OSError),
        patch("realtime.client.asyncio.sleep", sleep),
        pytest.raises(MaxRetriesExceeded),
    ):
        await automatically_reconnect(
            "ws://localhost/realtime/v1", get_token, client_handler, max_retries=8
        )

    assert [call.args[0] for call in sleep.await_args_list] == [
        2,
        4,
        8,
        16,
        32,
        60,
        60,
    ]
