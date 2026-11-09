from unittest.mock import AsyncMock, patch

import pytest
from supabase_utils.http.errors import SupabaseTransportError
from supabase_utils.http.headers import Headers
from supabase_utils.http.request import Request
from yarl import URL

from realtime import MaxRetriesExceeded
from realtime.client import automatically_reconnect, exponential_delay


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


async def test_automatically_reconnect_retries_transport_errors_of_the_token_callback() -> (
    None
):
    request = Request(
        url=URL("https://example.com/auth/v1/token"),
        method="POST",
        headers=Headers.empty(),
        content=None,
        delay=None,
    )

    async def get_token() -> str:
        raise SupabaseTransportError(request)

    async def client_handler(client: object) -> None:
        return

    sleep = AsyncMock()

    with (
        patch("realtime.client.asyncio.sleep", sleep),
        pytest.raises(MaxRetriesExceeded) as error,
    ):
        await automatically_reconnect(
            "ws://localhost/realtime/v1", get_token, client_handler, max_retries=2
        )

    assert isinstance(error.value.__cause__, SupabaseTransportError)
    assert [call.args[0] for call in sleep.await_args_list] == [2]
