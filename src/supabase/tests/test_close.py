import asyncio

from aiohttp import ClientSession
from httpx import AsyncClient as AsyncHttpxClient
from httpx import Client as SyncHttpxClient
from supabase_auth.timer import _AsyncTimer, _SyncTimer
from supabase_auth.types import Session
from supabase_utils.http.adapters.aiohttp import AsyncAiohttpSession
from supabase_utils.http.adapters.httpx import AsyncHttpxSession, HttpxSession

import supabase.aiohttp
import supabase.httpx
from supabase import AsyncClient, Client

URL = "https://example.supabase.co"
KEY = "publishable-key"


def never_called() -> None:
    raise AssertionError


async def never_finishes() -> Session:
    await asyncio.Event().wait()
    raise AssertionError


async def never_awaited() -> None:
    raise AssertionError


def test_close_closes_the_http_client_it_created() -> None:
    client = supabase.httpx.create_client(URL, KEY)
    assert isinstance(client.http_session, HttpxSession)

    client.close()

    assert client.http_session.client.is_closed


def test_close_leaves_a_passed_in_http_client_open() -> None:
    with SyncHttpxClient() as http_client:
        with supabase.httpx.create_client(URL, KEY, http_client=http_client):
            pass

        assert not http_client.is_closed


def test_close_leaves_a_passed_in_http_session_open() -> None:
    with SyncHttpxClient() as http_client:
        with Client(URL, KEY, HttpxSession(client=http_client)):
            pass

        assert not http_client.is_closed


def test_close_stops_the_auto_refresh() -> None:
    client = supabase.httpx.create_client(URL, KEY)
    timer = _SyncTimer(60, never_called)
    timer.start()
    client.auth.session_manager.refresh_token_timer = timer

    client.close()

    assert not timer.is_alive()
    assert client.auth.session_manager.refresh_token_timer is None


def test_close_schedules_no_new_refresh() -> None:
    client = supabase.httpx.create_client(URL, KEY)
    session_manager = client.auth.session_manager

    client.close()
    session_manager._schedule_refresh(60, None)

    assert session_manager.refresh_token_timer is None


def test_close_can_be_called_twice() -> None:
    client = supabase.httpx.create_client(URL, KEY)

    client.close()
    client.close()

    assert isinstance(client.http_session, HttpxSession)
    assert client.http_session.client.is_closed


async def test_aclose_closes_the_httpx_client_it_created() -> None:
    client = supabase.httpx.create_async_client(URL, KEY)
    assert isinstance(client.http_session, AsyncHttpxSession)

    await client.aclose()

    assert client.http_session.client.is_closed


async def test_aclose_closes_the_aiohttp_session_it_created() -> None:
    client = supabase.aiohttp.create_async_client(URL, KEY)
    assert isinstance(client.http_session, AsyncAiohttpSession)

    await client.aclose()

    assert client.http_session.client.closed


async def test_aclose_leaves_a_passed_in_httpx_client_open() -> None:
    async with AsyncHttpxClient() as http_client:
        async with supabase.httpx.create_async_client(
            URL, KEY, http_client=http_client
        ):
            pass

        assert not http_client.is_closed


async def test_aclose_leaves_a_passed_in_aiohttp_session_open() -> None:
    async with ClientSession() as http_client:
        async with supabase.aiohttp.create_async_client(
            URL, KEY, http_client=http_client
        ):
            pass

        assert not http_client.closed


async def test_aclose_leaves_a_passed_in_http_session_open() -> None:
    async with AsyncHttpxClient() as http_client:
        async with AsyncClient(URL, KEY, AsyncHttpxSession(client=http_client)):
            pass

        assert not http_client.is_closed


async def test_aclose_stops_the_auto_refresh() -> None:
    client = supabase.httpx.create_async_client(URL, KEY)
    session_manager = client.auth.session_manager
    timer = _AsyncTimer(60, never_awaited)
    timer.start()
    session_manager.refresh_token_timer = timer
    refresh = asyncio.create_task(never_finishes())
    session_manager._refresh_task = refresh

    await client.aclose()

    assert not timer.is_alive()
    assert session_manager.refresh_token_timer is None
    assert session_manager._refresh_task is None
    await asyncio.gather(refresh, return_exceptions=True)
    assert refresh.cancelled()


async def test_aclose_schedules_no_new_refresh() -> None:
    client = supabase.httpx.create_async_client(URL, KEY)
    session_manager = client.auth.session_manager

    await client.aclose()
    session_manager._schedule_refresh(60, None)

    assert session_manager.refresh_token_timer is None


async def test_aclose_can_be_called_twice() -> None:
    client = supabase.httpx.create_async_client(URL, KEY)

    await client.aclose()
    await client.aclose()

    assert isinstance(client.http_session, AsyncHttpxSession)
    assert client.http_session.client.is_closed
