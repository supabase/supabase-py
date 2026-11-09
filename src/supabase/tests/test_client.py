from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from httpx import AsyncClient as AsyncHttpxClient
from httpx import Client as SyncHttpxClient
from supabase_auth import (
    AsyncMemoryStorage,
    AsyncSupabaseAuthClient,
    SyncMemoryStorage,
    SyncSupabaseAuthClient,
)
from supabase_auth.constants import STORAGE_KEY
from supabase_utils.http.adapters.httpx import AsyncHttpxSession, HttpxSession

import supabase.aiohttp
import supabase.httpx
from supabase import (
    AsyncClient,
    AuthClientOptions,
    Client,
    FunctionsClientOptions,
    PostgrestClientOptions,
    RealtimeClientOptions,
    StorageClientOptions,
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
    with SyncHttpxClient() as http_client:
        client = Client(
            URL,
            KEY,
            HttpxSession(client=http_client),
            headers={"authorization": "Bearer userjwt"},
        )

    assert "authorization" not in client.headers
    assert client.headers["Authorization"] == "Bearer userjwt"
    assert client.postgrest.default_headers.get("Authorization") == "Bearer userjwt"


async def test_async_client_keeps_a_lowercase_authorization_header() -> None:
    async with AsyncHttpxClient() as http_client:
        client = AsyncClient(
            URL,
            KEY,
            AsyncHttpxSession(client=http_client),
            headers={"authorization": "Bearer userjwt"},
        )

    assert "authorization" not in client.headers
    assert client.headers["Authorization"] == "Bearer userjwt"
    assert client.postgrest.default_headers.get("Authorization") == "Bearer userjwt"


async def test_async_client_passes_realtime_options_to_connections() -> None:
    async with AsyncHttpxClient() as http_client:
        client = AsyncClient(
            URL,
            KEY,
            AsyncHttpxSession(client=http_client),
            realtime=RealtimeClientOptions(heartbeat_interval=30, heartbeat_timeout=10),
        )

    connection = client.realtime

    assert connection.heartbeat_interval == 30
    assert connection.heartbeat_timeout == 10


def test_sync_create_does_not_replace_a_lowercase_authorization_header() -> None:
    session = MagicMock(access_token="storedjwt")
    with (
        SyncHttpxClient() as http_client,
        patch.object(
            SyncSupabaseAuthClient, "get_session", MagicMock(return_value=session)
        ),
    ):
        client = Client.create(
            URL,
            KEY,
            HttpxSession(client=http_client),
            headers={"authorization": "Bearer userjwt"},
        )

    assert client.postgrest.default_headers.get("Authorization") == "Bearer userjwt"


async def test_async_create_does_not_replace_a_lowercase_authorization_header() -> None:
    session = MagicMock(access_token="storedjwt")
    async with AsyncHttpxClient() as http_client:
        with patch.object(
            AsyncSupabaseAuthClient, "get_session", AsyncMock(return_value=session)
        ):
            client = await AsyncClient.create(
                URL,
                KEY,
                AsyncHttpxSession(client=http_client),
                headers={"authorization": "Bearer userjwt"},
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
    requests: list[httpx.Request] = []
    with SyncHttpxClient(transport=recording_transport(requests)) as http_client:
        client = Client(
            URL,
            key,
            HttpxSession(client=http_client),
            headers={"Authorization": "Bearer customjwt"},
        )
        client.functions.invoke("hello")

    assert requests[0].headers.get("authorization") == "Bearer customjwt"


@pytest.mark.parametrize("key", NEW_KEYS)
async def test_async_functions_send_a_custom_authorization_header_with_a_new_format_key(
    key: str,
) -> None:
    requests: list[httpx.Request] = []
    async with AsyncHttpxClient(transport=recording_transport(requests)) as http_client:
        client = AsyncClient(
            URL,
            key,
            AsyncHttpxSession(client=http_client),
            headers={"Authorization": "Bearer customjwt"},
        )
        await client.functions.invoke("hello")

    assert requests[0].headers.get("authorization") == "Bearer customjwt"


def test_sync_client_passes_request_timeouts_to_sub_clients() -> None:
    with SyncHttpxClient() as http_client:
        client = Client(
            URL,
            KEY,
            HttpxSession(client=http_client),
            request_timeout=10,
            postgrest=PostgrestClientOptions(request_timeout=3),
            storage=StorageClientOptions(request_timeout=120),
        )
        assert client.postgrest.executor.request_timeout == 3
        assert client.storage.executor.request_timeout == 120
        assert client.auth.executor.request_timeout == 10
        assert client.functions.executor.request_timeout == 10


async def test_async_client_passes_request_timeouts_to_sub_clients() -> None:
    async with AsyncHttpxClient() as http_client:
        client = AsyncClient(
            URL,
            KEY,
            AsyncHttpxSession(client=http_client),
            functions=FunctionsClientOptions(request_timeout=60),
        )
        assert client.functions.executor.request_timeout == 60
        assert client.postgrest.executor.request_timeout is None
        assert client.storage.executor.request_timeout is None
        assert client.auth.executor.request_timeout is None


@pytest.mark.parametrize("request_timeout", [0, -1, float("nan"), float("inf")])
def test_sync_client_rejects_an_invalid_request_timeout(
    request_timeout: float,
) -> None:
    with (
        SyncHttpxClient() as http_client,
        pytest.raises(ValueError, match="positive number of seconds"),
    ):
        Client(
            URL,
            KEY,
            HttpxSession(client=http_client),
            request_timeout=request_timeout,
        )


@pytest.mark.parametrize("request_timeout", [0, -1, float("nan"), float("inf")])
async def test_async_client_rejects_an_invalid_request_timeout(
    request_timeout: float,
) -> None:
    async with AsyncHttpxClient() as http_client:
        with pytest.raises(ValueError, match="positive number of seconds"):
            AsyncClient(
                URL,
                KEY,
                AsyncHttpxSession(client=http_client),
                request_timeout=request_timeout,
            )


def test_sync_client_passes_service_options_to_sub_clients() -> None:
    session_storage = SyncMemoryStorage()
    with SyncHttpxClient() as http_client:
        client = Client(
            URL,
            KEY,
            HttpxSession(client=http_client),
            postgrest=PostgrestClientOptions(schema="private"),
            auth=AuthClientOptions(
                auto_refresh_token=False,
                session_storage=session_storage,
                storage_key="custom-key",
                flow_type="implicit",
            ),
        )
        assert client.postgrest.default_headers.get("Accept-Profile") == "private"
        assert client.auth.session_manager.storage is session_storage
        assert client.auth.session_manager.storage_key == "custom-key"
        assert client.auth.session_manager.auto_refresh_token is False
        assert client.auth.flow_type == "implicit"


async def test_async_client_passes_service_options_to_sub_clients() -> None:
    session_storage = AsyncMemoryStorage()
    async with AsyncHttpxClient() as http_client:
        client = AsyncClient(
            URL,
            KEY,
            AsyncHttpxSession(client=http_client),
            postgrest=PostgrestClientOptions(schema="private"),
            auth=AuthClientOptions(
                auto_refresh_token=False,
                session_storage=session_storage,
                storage_key="custom-key",
                flow_type="implicit",
            ),
        )
        assert client.postgrest.default_headers.get("Accept-Profile") == "private"
        assert client.auth.session_manager.storage is session_storage
        assert client.auth.session_manager.storage_key == "custom-key"
        assert client.auth.session_manager.auto_refresh_token is False
        assert client.auth.flow_type == "implicit"


def test_sync_client_uses_service_defaults() -> None:
    with SyncHttpxClient() as http_client:
        client = Client(URL, KEY, HttpxSession(client=http_client))
        assert client.postgrest.default_headers.get("Accept-Profile") == "public"
        assert isinstance(client.auth.session_manager.storage, SyncMemoryStorage)
        assert client.auth.session_manager.storage_key == STORAGE_KEY
        assert client.auth.session_manager.auto_refresh_token is True
        assert client.auth.flow_type == "pkce"


def test_client_sends_default_headers_with_custom_headers() -> None:
    with SyncHttpxClient() as http_client:
        client = Client(
            URL, KEY, HttpxSession(client=http_client), headers={"x-app": "1"}
        )

    assert client.headers["x-app"] == "1"
    assert client.headers["X-Client-Info"].startswith("supabase-py/")
    assert (
        client.postgrest.default_headers.get("X-Client-Info")
        == (client.headers["X-Client-Info"])
    )


def test_custom_headers_override_default_headers_regardless_of_case() -> None:
    with SyncHttpxClient() as http_client:
        client = Client(
            URL,
            KEY,
            HttpxSession(client=http_client),
            headers={"x-client-info": "my-app"},
        )

    assert "X-Client-Info" not in client.headers
    assert client.headers["x-client-info"] == "my-app"
    assert client.postgrest.default_headers.get("X-Client-Info") == "my-app"


def test_client_headers_are_read_only() -> None:
    with SyncHttpxClient() as http_client:
        client = Client(URL, KEY, HttpxSession(client=http_client))

    with pytest.raises(TypeError):
        client.headers["x-app"] = "1"  # pyrefly: ignore[unsupported-operation]


def test_client_headers_follow_the_session() -> None:
    with SyncHttpxClient() as http_client:
        client = Client(URL, KEY, HttpxSession(client=http_client))
        headers = client.headers

        client.auth.session_manager.notify_all_subscribers(
            "SIGNED_IN", MagicMock(access_token="userjwt")
        )

    assert headers["Authorization"] == "Bearer userjwt"


@pytest.mark.parametrize("request_timeout", [0, -1, float("nan"), float("inf")])
def test_factories_reject_an_invalid_request_timeout_before_creating_a_session(
    request_timeout: float,
) -> None:
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
            pytest.raises(ValueError, match="positive number of seconds"),
        ):
            factory(URL, KEY, request_timeout=request_timeout)
        aiohttp_session.assert_not_called()
        sync_httpx_client.assert_not_called()
        async_httpx_client.assert_not_called()
