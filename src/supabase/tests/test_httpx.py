import httpx
from httpx import AsyncClient as AsyncHttpxClient
from httpx import Client as SyncHttpxClient
from supabase_utils.http.adapters.httpx import AsyncHttpxSession, HttpxSession

from supabase import FunctionsClientOptions
from supabase.httpx import create_async_client, create_client

URL = "https://example.supabase.co"
KEY = "publishable-key"


def test_create_client_follows_redirects() -> None:
    with create_client(URL, KEY) as client:
        assert isinstance(client.http_session, HttpxSession)
        assert client.http_session.client.follow_redirects


async def test_create_async_client_follows_redirects() -> None:
    async with create_async_client(URL, KEY) as client:
        assert isinstance(client.http_session, AsyncHttpxSession)
        assert client.http_session.client.follow_redirects


def test_create_client_times_out_after_60_seconds() -> None:
    with create_client(URL, KEY) as client:
        assert isinstance(client.http_session, HttpxSession)
        assert client.http_session.client.timeout == httpx.Timeout(60)


async def test_create_async_client_times_out_after_60_seconds() -> None:
    async with create_async_client(URL, KEY) as client:
        assert isinstance(client.http_session, AsyncHttpxSession)
        assert client.http_session.client.timeout == httpx.Timeout(60)


def test_create_client_keeps_the_timeout_of_a_passed_in_client() -> None:
    with (
        SyncHttpxClient(timeout=3) as http_client,
        create_client(URL, KEY, http_client=http_client) as client,
    ):
        assert isinstance(client.http_session, HttpxSession)
        assert client.http_session.client.timeout == httpx.Timeout(3)


async def test_create_async_client_keeps_the_timeout_of_a_passed_in_client() -> None:
    async with (
        AsyncHttpxClient(timeout=3) as http_client,
        create_async_client(URL, KEY, http_client=http_client) as client,
    ):
        assert isinstance(client.http_session, AsyncHttpxSession)
        assert client.http_session.client.timeout == httpx.Timeout(3)


def test_request_timeouts_override_the_default_timeout() -> None:
    timeouts: list[object] = []

    def handler(request: httpx.Request) -> httpx.Response:
        timeouts.append(request.extensions["timeout"])
        return httpx.Response(200, json=[])

    with create_client(
        URL,
        KEY,
        request_timeout=10,
        functions=FunctionsClientOptions(request_timeout=120),
    ) as client:
        assert isinstance(client.http_session, HttpxSession)
        client.http_session.client._transport = httpx.MockTransport(handler)
        client.table("countries").select("*").execute()
        client.functions.invoke("hello")

    assert timeouts == [httpx.Timeout(10).as_dict(), httpx.Timeout(120).as_dict()]
