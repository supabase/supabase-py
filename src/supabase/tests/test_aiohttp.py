import pytest
from aiohttp import ClientSession, ClientTimeout
from supabase_utils.http.adapters.aiohttp import AsyncAiohttpSession

from supabase import FunctionsClientOptions
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


async def test_request_timeout_overrides_the_default_timeout(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    timeouts: list[ClientTimeout] = []

    async def request(*_args: object, **kwargs: ClientTimeout) -> None:
        timeouts.append(kwargs["timeout"])
        raise RuntimeError("sent")

    async with create_async_client(
        URL, KEY, functions=FunctionsClientOptions(request_timeout=10)
    ) as client:
        assert isinstance(client.http_session, AsyncAiohttpSession)
        monkeypatch.setattr(client.http_session.client, "request", request)
        with pytest.raises(RuntimeError, match="sent"):
            await client.functions.invoke("hello")

    assert timeouts == [
        ClientTimeout(total=None, connect=10, sock_connect=10, sock_read=10)
    ]
