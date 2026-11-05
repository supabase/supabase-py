from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient as AsyncHttpxClient
from httpx import Client as SyncHttpxClient
from supabase_auth import AsyncSupabaseAuthClient, SyncSupabaseAuthClient
from supabase_utils.http.adapters.httpx import AsyncHttpxSession, HttpxSession

from supabase import (
    AsyncClient,
    AsyncClientOptions,
    Client,
    ClientOptions,
    SupabaseException,
)

URL = "https://example.supabase.co"
KEY = "publishable-key"

INVALID_URLS = [
    "",
    "example.supabase.co",
    "ftp://example.supabase.co",
    "https://",
    "http://[::1",
    "https://example.supabase.co:99999",
]


@pytest.mark.parametrize("url", INVALID_URLS)
def test_sync_client_rejects_invalid_urls(url: str) -> None:
    with SyncHttpxClient() as http_client, pytest.raises(SupabaseException):
        Client(url, KEY, HttpxSession(client=http_client))


@pytest.mark.parametrize("url", INVALID_URLS)
async def test_async_client_rejects_invalid_urls(url: str) -> None:
    async with AsyncHttpxClient() as http_client:
        with pytest.raises(SupabaseException):
            AsyncClient(url, KEY, AsyncHttpxSession(client=http_client))


def test_sync_client_requires_a_key() -> None:
    with SyncHttpxClient() as http_client, pytest.raises(SupabaseException):
        Client(URL, "", HttpxSession(client=http_client))


async def test_async_client_requires_a_key() -> None:
    async with AsyncHttpxClient() as http_client:
        with pytest.raises(SupabaseException):
            AsyncClient(URL, "", AsyncHttpxSession(client=http_client))


def test_sync_client_keeps_a_lowercase_authorization_header() -> None:
    options = ClientOptions(headers={"authorization": "Bearer userjwt"})
    with SyncHttpxClient() as http_client:
        client = Client(URL, KEY, HttpxSession(client=http_client), options)

    assert "authorization" not in client.options.headers
    assert client.options.headers["Authorization"] == "Bearer userjwt"
    assert client.postgrest.default_headers.get("Authorization") == "Bearer userjwt"


async def test_async_client_keeps_a_lowercase_authorization_header() -> None:
    options = AsyncClientOptions(headers={"authorization": "Bearer userjwt"})
    async with AsyncHttpxClient() as http_client:
        client = AsyncClient(URL, KEY, AsyncHttpxSession(client=http_client), options)

    assert "authorization" not in client.options.headers
    assert client.options.headers["Authorization"] == "Bearer userjwt"
    assert client.postgrest.default_headers.get("Authorization") == "Bearer userjwt"


def test_sync_create_does_not_replace_a_lowercase_authorization_header() -> None:
    options = ClientOptions(headers={"authorization": "Bearer userjwt"})
    session = MagicMock(access_token="storedjwt")
    with (
        SyncHttpxClient() as http_client,
        patch.object(
            SyncSupabaseAuthClient, "get_session", MagicMock(return_value=session)
        ),
    ):
        client = Client.create(URL, KEY, HttpxSession(client=http_client), options)

    assert client.postgrest.default_headers.get("Authorization") == "Bearer userjwt"


async def test_async_create_does_not_replace_a_lowercase_authorization_header() -> None:
    options = AsyncClientOptions(headers={"authorization": "Bearer userjwt"})
    session = MagicMock(access_token="storedjwt")
    async with AsyncHttpxClient() as http_client:
        with patch.object(
            AsyncSupabaseAuthClient, "get_session", AsyncMock(return_value=session)
        ):
            client = await AsyncClient.create(
                URL, KEY, AsyncHttpxSession(client=http_client), options
            )

    assert client.postgrest.default_headers.get("Authorization") == "Bearer userjwt"
