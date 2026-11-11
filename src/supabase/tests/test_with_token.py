from unittest.mock import MagicMock

import httpx
import pytest
from aiohttp import ClientSession
from httpx import AsyncClient as AsyncHttpxClient
from httpx import Client as SyncHttpxClient
from supabase_auth.types import AuthChangeEvent, AuthStateChange
from supabase_utils.http.adapters.aiohttp import AsyncAiohttpSession
from supabase_utils.http.adapters.httpx import AsyncHttpxSession, HttpxSession

import supabase.aiohttp
import supabase.httpx
from supabase import (
    AsyncClient,
    Client,
    FunctionsClientOptions,
    PostgrestClientOptions,
    RealtimeClientOptions,
    RetryPolicy,
    SupabaseException,
)

URL = "https://example.supabase.co"
KEY = "sb_publishable_abc123"
TOKEN = "header.payload.signature"


def recording_transport(requests: list[httpx.Request]) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=[])

    return httpx.MockTransport(handler)


def test_sync_with_token_sends_the_token_to_every_service() -> None:
    requests: list[httpx.Request] = []
    with SyncHttpxClient(transport=recording_transport(requests)) as http_client:
        client = Client(URL, KEY, HttpxSession(client=http_client))
        scoped = client.with_token(TOKEN)
        scoped.table("todos").select("*").execute()
        scoped.functions.invoke("hello")

    assert len(requests) == 2
    for request in requests:
        assert request.headers.get("apikey") == KEY
        assert request.headers.get("authorization") == f"Bearer {TOKEN}"
    assert scoped.headers["Authorization"] == f"Bearer {TOKEN}"
    assert scoped.storage.default_headers.get("Authorization") == f"Bearer {TOKEN}"


async def test_async_with_token_sends_the_token_to_every_service() -> None:
    requests: list[httpx.Request] = []
    async with AsyncHttpxClient(transport=recording_transport(requests)) as http_client:
        client = AsyncClient(URL, KEY, AsyncHttpxSession(client=http_client))
        scoped = client.with_token(TOKEN)
        await scoped.table("todos").select("*").execute()
        await scoped.functions.invoke("hello")

    assert len(requests) == 2
    for request in requests:
        assert request.headers.get("apikey") == KEY
        assert request.headers.get("authorization") == f"Bearer {TOKEN}"
    assert scoped.headers["Authorization"] == f"Bearer {TOKEN}"
    assert scoped.storage.default_headers.get("Authorization") == f"Bearer {TOKEN}"
    token_callback = scoped.realtime.get_access_token
    assert token_callback is not None
    assert await token_callback() == TOKEN


def test_sync_with_token_keeps_the_client_unchanged() -> None:
    with SyncHttpxClient() as http_client:
        client = Client(URL, KEY, HttpxSession(client=http_client))
        client.auth.session_manager.notify_all_subscribers(
            AuthStateChange(
                AuthChangeEvent.SIGNED_IN, MagicMock(access_token="userjwt")
            )
        )
        scoped = client.with_token(TOKEN)

    assert client.headers["Authorization"] == "Bearer userjwt"
    assert client.postgrest.default_headers.get("Authorization") == "Bearer userjwt"
    assert scoped.headers["Authorization"] == f"Bearer {TOKEN}"


async def test_async_with_token_keeps_the_client_unchanged() -> None:
    async with AsyncHttpxClient() as http_client:
        client = AsyncClient(URL, KEY, AsyncHttpxSession(client=http_client))
        client.auth.session_manager.notify_all_subscribers(
            AuthStateChange(
                AuthChangeEvent.SIGNED_IN, MagicMock(access_token="userjwt")
            )
        )
        scoped = client.with_token(TOKEN)

    assert client.headers["Authorization"] == "Bearer userjwt"
    assert client.postgrest.default_headers.get("Authorization") == "Bearer userjwt"
    assert scoped.headers["Authorization"] == f"Bearer {TOKEN}"


def test_sync_with_token_keeps_the_token_when_the_client_signs_out() -> None:
    with SyncHttpxClient() as http_client:
        client = Client(URL, KEY, HttpxSession(client=http_client))
        scoped = client.with_token(TOKEN)
        client.auth.session_manager.notify_all_subscribers(
            AuthStateChange(AuthChangeEvent.SIGNED_OUT)
        )

    assert scoped.headers["Authorization"] == f"Bearer {TOKEN}"
    assert scoped.postgrest.default_headers.get("Authorization") == f"Bearer {TOKEN}"


async def test_async_with_token_keeps_the_token_when_the_client_signs_out() -> None:
    async with AsyncHttpxClient() as http_client:
        client = AsyncClient(URL, KEY, AsyncHttpxSession(client=http_client))
        scoped = client.with_token(TOKEN)
        client.auth.session_manager.notify_all_subscribers(
            AuthStateChange(AuthChangeEvent.SIGNED_OUT)
        )

    assert scoped.headers["Authorization"] == f"Bearer {TOKEN}"
    assert scoped.postgrest.default_headers.get("Authorization") == f"Bearer {TOKEN}"
    token_callback = scoped.realtime.get_access_token
    assert token_callback is not None
    assert await token_callback() == TOKEN


def test_sync_with_token_client_has_no_auth() -> None:
    with SyncHttpxClient() as http_client:
        client = Client(URL, KEY, HttpxSession(client=http_client))
        scoped = client.with_token(TOKEN)
        with pytest.raises(SupabaseException, match="with_token"):
            scoped.auth  # noqa: B018
        assert client.auth.default_headers.get("Authorization") == f"Bearer {KEY}"


async def test_async_with_token_client_has_no_auth() -> None:
    async with AsyncHttpxClient() as http_client:
        client = AsyncClient(URL, KEY, AsyncHttpxSession(client=http_client))
        scoped = client.with_token(TOKEN)
        with pytest.raises(SupabaseException, match="with_token"):
            scoped.auth  # noqa: B018
        assert client.auth.default_headers.get("Authorization") == f"Bearer {KEY}"


def test_sync_with_token_shares_the_session_and_options() -> None:
    with SyncHttpxClient() as http_client:
        client = Client(
            URL,
            KEY,
            HttpxSession(client=http_client),
            headers={"x-app": "1"},
            request_timeout=10,
            retry=RetryPolicy(max_retries=5),
            postgrest=PostgrestClientOptions(schema="private"),
            functions=FunctionsClientOptions(request_timeout=60),
        )
        scoped = client.with_token(TOKEN)

    assert scoped.headers["x-app"] == "1"
    assert scoped.headers["X-Client-Info"] == client.headers["X-Client-Info"]
    assert scoped.postgrest.default_headers.get("Accept-Profile") == "private"
    assert scoped.postgrest.executor.request_timeout == 10
    assert scoped.functions.executor.request_timeout == 60
    assert scoped.postgrest.executor.retry_policy == RetryPolicy(max_retries=5)


async def test_async_with_token_shares_the_session_and_options() -> None:
    realtime = RealtimeClientOptions(heartbeat_interval=5, heartbeat_timeout=5)
    async with AsyncHttpxClient() as http_client:
        client = AsyncClient(
            URL,
            KEY,
            AsyncHttpxSession(client=http_client),
            headers={"x-app": "1"},
            request_timeout=10,
            retry=RetryPolicy(max_retries=5),
            postgrest=PostgrestClientOptions(schema="private"),
            functions=FunctionsClientOptions(request_timeout=60),
            realtime=realtime,
        )
        scoped = client.with_token(TOKEN)

    assert scoped.headers["x-app"] == "1"
    assert scoped.headers["X-Client-Info"] == client.headers["X-Client-Info"]
    assert scoped.postgrest.default_headers.get("Accept-Profile") == "private"
    assert scoped.postgrest.executor.request_timeout == 10
    assert scoped.functions.executor.request_timeout == 60
    assert scoped.postgrest.executor.retry_policy == RetryPolicy(max_retries=5)
    assert scoped.realtime.heartbeat_interval == 5


def test_sync_with_token_rejects_an_empty_token() -> None:
    with SyncHttpxClient() as http_client:
        client = Client(URL, KEY, HttpxSession(client=http_client))
        with pytest.raises(ValueError, match="access_token"):
            client.with_token("")


async def test_async_with_token_rejects_an_empty_token() -> None:
    async with AsyncHttpxClient() as http_client:
        client = AsyncClient(URL, KEY, AsyncHttpxSession(client=http_client))
        with pytest.raises(ValueError, match="access_token"):
            client.with_token("")


def test_sync_leaving_a_with_token_client_keeps_the_session_open() -> None:
    with supabase.httpx.create_client(URL, KEY) as client:
        assert isinstance(client.http_session, HttpxSession)
        with client.with_token(TOKEN):
            pass
        assert not client.http_session.client.is_closed
    assert client.http_session.client.is_closed


async def test_async_leaving_a_with_token_client_keeps_the_session_open() -> None:
    async with supabase.httpx.create_async_client(URL, KEY) as client:
        assert isinstance(client.http_session, AsyncHttpxSession)
        async with client.with_token(TOKEN):
            pass
        assert not client.http_session.client.is_closed
    assert client.http_session.client.is_closed


def test_sync_leaving_a_service_of_a_with_token_client_keeps_the_session_open() -> None:
    with supabase.httpx.create_client(URL, KEY) as client:
        assert isinstance(client.http_session, HttpxSession)
        scoped = client.with_token(TOKEN)
        with scoped.postgrest, scoped.storage:
            pass
        assert not client.http_session.client.is_closed


async def test_async_leaving_a_service_of_a_with_token_client_keeps_the_session_open() -> (
    None
):
    async with supabase.httpx.create_async_client(URL, KEY) as client:
        assert isinstance(client.http_session, AsyncHttpxSession)
        scoped = client.with_token(TOKEN)
        async with scoped.postgrest, scoped.storage:
            pass
        assert not client.http_session.client.is_closed


def test_sync_factory_keeps_a_given_http_client_open() -> None:
    with SyncHttpxClient() as http_client:
        with (
            supabase.httpx.create_client(URL, KEY, http_client=http_client) as client,
            client.postgrest,
        ):
            pass
        assert not http_client.is_closed


async def test_async_httpx_factory_keeps_a_given_http_client_open() -> None:
    async with AsyncHttpxClient() as http_client:
        async with supabase.httpx.create_async_client(
            URL, KEY, http_client=http_client
        ):
            pass
        assert not http_client.is_closed


async def test_aiohttp_factory_keeps_a_given_http_client_open() -> None:
    async with ClientSession() as http_client:
        async with supabase.aiohttp.create_async_client(
            URL, KEY, http_client=http_client
        ):
            pass
        assert not http_client.closed


async def test_aiohttp_factory_closes_the_http_client_it_creates() -> None:
    async with supabase.aiohttp.create_async_client(URL, KEY) as client:
        assert isinstance(client.http_session, AsyncAiohttpSession)
    assert client.http_session.client.closed


def test_sync_closing_a_with_token_client_keeps_the_session_open() -> None:
    with supabase.httpx.create_client(URL, KEY) as client:
        assert isinstance(client.http_session, HttpxSession)
        client.with_token(TOKEN).close()
        assert not client.http_session.client.is_closed


async def test_async_closing_a_with_token_client_keeps_the_session_open() -> None:
    async with supabase.httpx.create_async_client(URL, KEY) as client:
        assert isinstance(client.http_session, AsyncHttpxSession)
        await client.with_token(TOKEN).aclose()
        assert not client.http_session.client.is_closed
