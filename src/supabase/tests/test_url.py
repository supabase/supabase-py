import re
from unittest.mock import patch

import pytest
from httpx import AsyncClient as AsyncHttpxClient
from httpx import Client as SyncHttpxClient
from supabase_utils.http.adapters.httpx import AsyncHttpxSession, HttpxSession
from yarl import URL

import supabase.aiohttp
import supabase.httpx
from supabase import AsyncClient, Client, SupabaseException

KEY = "sb_publishable_abc123"

LOOPBACK_URLS = [
    "http://localhost:54321",
    "http://LOCALHOST:54321",
    "http://127.0.0.1:54321",
    "http://127.12.0.1",
    "http://[::1]:54321",
    "http://[0:0:0:0:0:0:0:1]",
]

INSECURE_URLS = [
    "http://abc.supabase.co",
    "http://192.168.1.20:8000",
    "http://10.0.2.2:54321",
    "http://0.0.0.0:54321",
    "http://api.localhost",
    "http://localhost.example.com",
    "http://127.0.0.1.example.com",
    "http://0127.0.0.1",
    "http://127.000.0.1",
    "http://[::2]",
    "http://[::ffff:7f00:1]",
]


def sync_client(url: str, *, allow_insecure_http: bool = False) -> Client:
    return Client(
        url,
        KEY,
        HttpxSession(client=SyncHttpxClient()),
        allow_insecure_http=allow_insecure_http,
    )


def async_client(url: str, *, allow_insecure_http: bool = False) -> AsyncClient:
    return AsyncClient(
        url,
        KEY,
        AsyncHttpxSession(client=AsyncHttpxClient()),
        allow_insecure_http=allow_insecure_http,
    )


@pytest.mark.parametrize("url", LOOPBACK_URLS)
def test_sync_client_accepts_http_on_a_loopback_host(url: str) -> None:
    client = sync_client(url)

    assert client.rest_url.scheme == "http"


@pytest.mark.parametrize("url", LOOPBACK_URLS)
async def test_async_client_accepts_http_on_a_loopback_host(url: str) -> None:
    client = async_client(url)

    assert client.realtime_url.scheme == "ws"
    assert client.realtime.url == client.realtime_url


@pytest.mark.parametrize("url", INSECURE_URLS)
def test_sync_client_rejects_http_on_another_host(url: str) -> None:
    with pytest.raises(SupabaseException, match="must use https, since http"):
        sync_client(url)


@pytest.mark.parametrize("url", INSECURE_URLS)
async def test_async_client_rejects_http_on_another_host(url: str) -> None:
    with pytest.raises(SupabaseException, match="must use https, since http"):
        async_client(url)


@pytest.mark.parametrize("url", ["", "abc.supabase.co", "https://", "https:///rest"])
def test_rejects_a_url_without_a_host(url: str) -> None:
    with pytest.raises(SupabaseException):
        sync_client(url)


@pytest.mark.parametrize("url", ["ws://localhost:54321", "ftp://abc.supabase.co"])
def test_rejects_another_scheme(url: str) -> None:
    with pytest.raises(SupabaseException, match=re.escape("must use https or http")):
        sync_client(url, allow_insecure_http=True)


def test_sync_client_with_allow_insecure_http_accepts_any_host() -> None:
    client = sync_client("http://192.168.1.20:8000", allow_insecure_http=True)

    assert client.rest_url == URL("http://192.168.1.20:8000/rest/v1")
    assert client.with_token("token").rest_url == client.rest_url


async def test_async_client_passes_allow_insecure_http_on_to_realtime() -> None:
    client = async_client("http://192.168.1.20:8000", allow_insecure_http=True)

    assert client.realtime.url == URL("ws://192.168.1.20:8000/realtime/v1")
    assert client.with_token("token").realtime.url == client.realtime.url


def test_factories_reject_http_on_another_host_before_creating_a_session() -> None:
    factories = [
        supabase.httpx.create_client,
        supabase.httpx.create_async_client,
        supabase.aiohttp.create_async_client,
    ]
    for factory in factories:
        with (
            patch("supabase.aiohttp.ClientSession") as aiohttp_session,
            patch("supabase.httpx.SyncHttpxClient") as sync_httpx_client,
            patch("supabase.httpx.AsyncHttpxClient") as async_httpx_client,
            pytest.raises(SupabaseException, match="allow_insecure_http"),
        ):
            factory("http://192.168.1.20:8000", KEY)
        aiohttp_session.assert_not_called()
        sync_httpx_client.assert_not_called()
        async_httpx_client.assert_not_called()


def test_sync_factory_passes_allow_insecure_http_on() -> None:
    with supabase.httpx.create_client(
        "http://192.168.1.20:8000", KEY, allow_insecure_http=True
    ) as client:
        assert client.rest_url == URL("http://192.168.1.20:8000/rest/v1")


async def test_async_factories_pass_allow_insecure_http_on() -> None:
    for factory in [
        supabase.httpx.create_async_client,
        supabase.aiohttp.create_async_client,
    ]:
        async with factory(
            "http://192.168.1.20:8000", KEY, allow_insecure_http=True
        ) as client:
            assert client.realtime.url == URL("ws://192.168.1.20:8000/realtime/v1")
