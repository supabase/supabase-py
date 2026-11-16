from aiohttp import ClientSession, ClientTimeout
from supabase_utils.http.adapters.aiohttp import AsyncAiohttpSession

from supabase.aiohttp import create_async_client

URL = "https://example.supabase.co"
KEY = "publishable-key"


async def test_create_async_client_times_out_after_60_seconds() -> None:
    async with create_async_client(URL, KEY) as client:
        assert isinstance(client.http_session, AsyncAiohttpSession)
        assert client.http_session.client.timeout == ClientTimeout(
            total=None, connect=60, sock_connect=60, sock_read=60
        )


async def test_create_async_client_keeps_the_timeout_of_a_passed_in_session() -> None:
    timeout = ClientTimeout(total=3)
    async with (
        ClientSession(timeout=timeout) as http_client,
        create_async_client(URL, KEY, http_client=http_client) as client,
    ):
        assert isinstance(client.http_session, AsyncAiohttpSession)
        assert client.http_session.client.timeout is timeout


async def test_request_timeout_overrides_the_default_timeout() -> None:
    async with create_async_client(URL, KEY) as client:
        assert isinstance(client.http_session, AsyncAiohttpSession)
        assert client.http_session._timeout(10) == ClientTimeout(
            total=None, connect=10, sock_connect=10, sock_read=10
        )
