from unittest.mock import AsyncMock, MagicMock, patch

import httpx
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
    RealtimeClientOptions,
    SupabaseException,
)

URL = "https://example.supabase.co"
KEY = "publishable-key"
NEW_KEYS = ["sb_publishable_abc123", "sb_secret_abc123", "sb_futuretype_abc123"]
LEGACY_KEY = "header.payload.signature"

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


async def test_async_client_passes_realtime_options_to_connections() -> None:
    options = AsyncClientOptions(
        realtime=RealtimeClientOptions(heartbeat_interval=30, heartbeat_timeout=10)
    )
    async with AsyncHttpxClient() as http_client:
        client = AsyncClient(URL, KEY, AsyncHttpxSession(client=http_client), options)

    connection = client.realtime

    assert connection.heartbeat_interval == 30
    assert connection.heartbeat_timeout == 10


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


def recording_transport(requests: list[httpx.Request]) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json={})

    return httpx.MockTransport(handler)


@pytest.mark.parametrize("key", NEW_KEYS)
def test_sync_functions_omit_a_new_format_key_as_bearer(key: str) -> None:
    requests: list[httpx.Request] = []
    with SyncHttpxClient(transport=recording_transport(requests)) as http_client:
        client = Client(URL, key, HttpxSession(client=http_client))
        client.functions.invoke("hello")

    assert requests[0].headers.get("apikey") == key
    assert "authorization" not in requests[0].headers
    assert client.postgrest.default_headers.get("Authorization") == f"Bearer {key}"
    assert client.storage.default_headers.get("Authorization") == f"Bearer {key}"


@pytest.mark.parametrize("key", NEW_KEYS)
async def test_async_functions_omit_a_new_format_key_as_bearer(key: str) -> None:
    requests: list[httpx.Request] = []
    async with AsyncHttpxClient(transport=recording_transport(requests)) as http_client:
        client = AsyncClient(URL, key, AsyncHttpxSession(client=http_client))
        await client.functions.invoke("hello")

    assert requests[0].headers.get("apikey") == key
    assert "authorization" not in requests[0].headers
    assert client.postgrest.default_headers.get("Authorization") == f"Bearer {key}"
    assert client.storage.default_headers.get("Authorization") == f"Bearer {key}"


def test_sync_functions_send_a_legacy_key_as_bearer() -> None:
    requests: list[httpx.Request] = []
    with SyncHttpxClient(transport=recording_transport(requests)) as http_client:
        client = Client(URL, LEGACY_KEY, HttpxSession(client=http_client))
        client.functions.invoke("hello")

    assert requests[0].headers.get("apikey") == LEGACY_KEY
    assert requests[0].headers.get("authorization") == f"Bearer {LEGACY_KEY}"


async def test_async_functions_send_a_legacy_key_as_bearer() -> None:
    requests: list[httpx.Request] = []
    async with AsyncHttpxClient(transport=recording_transport(requests)) as http_client:
        client = AsyncClient(URL, LEGACY_KEY, AsyncHttpxSession(client=http_client))
        await client.functions.invoke("hello")

    assert requests[0].headers.get("apikey") == LEGACY_KEY
    assert requests[0].headers.get("authorization") == f"Bearer {LEGACY_KEY}"


@pytest.mark.parametrize("key", NEW_KEYS)
def test_sync_functions_send_the_session_token_with_a_new_format_key(
    key: str,
) -> None:
    requests: list[httpx.Request] = []
    with SyncHttpxClient(transport=recording_transport(requests)) as http_client:
        client = Client(URL, key, HttpxSession(client=http_client))
        client.auth.session_manager.notify_all_subscribers(
            "SIGNED_IN", MagicMock(access_token="userjwt")
        )
        client.functions.invoke("hello")
        client.auth.session_manager.notify_all_subscribers("SIGNED_OUT", None)
        client.functions.invoke("hello")

    signed_in, signed_out = requests
    assert signed_in.headers.get("apikey") == key
    assert signed_in.headers.get("authorization") == "Bearer userjwt"
    assert signed_out.headers.get("apikey") == key
    assert "authorization" not in signed_out.headers
    assert client.postgrest.default_headers.get("Authorization") == f"Bearer {key}"


@pytest.mark.parametrize("key", NEW_KEYS)
async def test_async_functions_send_the_session_token_with_a_new_format_key(
    key: str,
) -> None:
    requests: list[httpx.Request] = []
    async with AsyncHttpxClient(transport=recording_transport(requests)) as http_client:
        client = AsyncClient(URL, key, AsyncHttpxSession(client=http_client))
        client.auth.session_manager.notify_all_subscribers(
            "SIGNED_IN", MagicMock(access_token="userjwt")
        )
        await client.functions.invoke("hello")
        client.auth.session_manager.notify_all_subscribers("SIGNED_OUT", None)
        await client.functions.invoke("hello")

    signed_in, signed_out = requests
    assert signed_in.headers.get("apikey") == key
    assert signed_in.headers.get("authorization") == "Bearer userjwt"
    assert signed_out.headers.get("apikey") == key
    assert "authorization" not in signed_out.headers
    assert client.postgrest.default_headers.get("Authorization") == f"Bearer {key}"


@pytest.mark.parametrize("key", NEW_KEYS)
def test_sync_functions_send_a_custom_authorization_header_with_a_new_format_key(
    key: str,
) -> None:
    options = ClientOptions(headers={"Authorization": "Bearer customjwt"})
    requests: list[httpx.Request] = []
    with SyncHttpxClient(transport=recording_transport(requests)) as http_client:
        client = Client(URL, key, HttpxSession(client=http_client), options)
        client.functions.invoke("hello")

    assert requests[0].headers.get("authorization") == "Bearer customjwt"


@pytest.mark.parametrize("key", NEW_KEYS)
async def test_async_functions_send_a_custom_authorization_header_with_a_new_format_key(
    key: str,
) -> None:
    options = AsyncClientOptions(headers={"Authorization": "Bearer customjwt"})
    requests: list[httpx.Request] = []
    async with AsyncHttpxClient(transport=recording_transport(requests)) as http_client:
        client = AsyncClient(URL, key, AsyncHttpxSession(client=http_client), options)
        await client.functions.invoke("hello")

    assert requests[0].headers.get("authorization") == "Bearer customjwt"
