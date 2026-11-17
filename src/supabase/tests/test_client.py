import base64
import json
import logging
import re
from concurrent.futures import ThreadPoolExecutor
from typing import override
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from httpx import AsyncClient as AsyncHttpxClient
from httpx import Client as SyncHttpxClient
from realtime import RealtimeClient
from supabase_auth import (
    AsyncMemoryStorage,
    AsyncSupabaseAuthClient,
    AuthRetryableError,
    SyncMemoryStorage,
    SyncSupabaseAuthClient,
)
from supabase_auth.constants import STORAGE_KEY
from supabase_auth.types import AuthChangeEvent, AuthStateChange
from supabase_utils.http.adapters.httpx import AsyncHttpxSession, HttpxSession
from supabase_utils.http.retry import RetryPolicy

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
from supabase import RetryPolicy as ExportedRetryPolicy

URL = "https://example.supabase.co"
KEY = "publishable-key"
NEW_KEYS = ["sb_publishable_abc123", "sb_secret_abc123", "sb_futuretype_abc123"]
LEGACY_KEY = "header.payload.signature"
SESSION_KEYS = ["sb_publishable_abc123", "sb_futuretype_abc123"]


def legacy_jwt(role: str, alg: str = "HS256") -> str:
    def encode(value: dict[str, str]) -> str:
        raw = json.dumps(value).encode()
        return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()

    return f"{encode({'alg': alg, 'typ': 'JWT'})}.{encode({'role': role})}.sig"


SERVICE_ROLE_JWT = legacy_jwt("service_role", alg="HS512")
SECRET_KEYS = ["sb_secret_abc123", SERVICE_ROLE_JWT]
PUBLIC_KEYS = [KEY, "sb_publishable_abc123", legacy_jwt("anon")]

INVALID_URLS = [
    "example.supabase.co",
    "ftp://example.supabase.co",
    "https://",
    "http://[::1",
    "https://example.supabase.co:99999",
]

MISSING_OR_NON_STRING_URL_AND_KEY: list[tuple[object, object, str]] = [
    ("", KEY, "supabase_url is required"),
    (None, KEY, "supabase_url is required"),
    (139, KEY, "supabase_url must be a string, not int"),
    (b"https://example.supabase.co", KEY, "supabase_url must be a string, not bytes"),
    ({}, KEY, "supabase_url must be a string, not dict"),
    ([], KEY, "supabase_url must be a string, not list"),
    (URL, "", "supabase_key is required"),
    (URL, None, "supabase_key is required"),
    (URL, 139, "supabase_key must be a string, not int"),
    (URL, b"publishable-key", "supabase_key must be a string, not bytes"),
    (URL, {}, "supabase_key must be a string, not dict"),
    (URL, [], "supabase_key must be a string, not list"),
    (None, 139, "supabase_url is required"),
    (139, None, "supabase_url must be a string, not int"),
]

INVALID_URL_AND_KEY = [
    *[(url, KEY, "Invalid URL") for url in INVALID_URLS],
    *MISSING_OR_NON_STRING_URL_AND_KEY,
]


@pytest.mark.parametrize(("url", "key", "message"), INVALID_URL_AND_KEY)
def test_sync_client_rejects_an_invalid_url_or_key(
    url: object, key: object, message: str
) -> None:
    with (
        SyncHttpxClient() as http_client,
        pytest.raises(SupabaseException, match=re.escape(message)),
    ):
        Client(
            url,  # pyrefly: ignore[bad-argument-type]
            key,  # pyrefly: ignore[bad-argument-type]
            HttpxSession(client=http_client),
        )


@pytest.mark.parametrize(("url", "key", "message"), INVALID_URL_AND_KEY)
async def test_async_client_rejects_an_invalid_url_or_key(
    url: object, key: object, message: str
) -> None:
    async with AsyncHttpxClient() as http_client:
        with pytest.raises(SupabaseException, match=re.escape(message)):
            AsyncClient(
                url,  # pyrefly: ignore[bad-argument-type]
                key,  # pyrefly: ignore[bad-argument-type]
                AsyncHttpxSession(client=http_client),
            )


@pytest.mark.parametrize(("url", "key", "message"), MISSING_OR_NON_STRING_URL_AND_KEY)
def test_factories_reject_an_invalid_url_or_key_before_creating_a_session(
    url: object, key: object, message: str
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
            pytest.raises(SupabaseException, match=re.escape(message)),
        ):
            factory(
                url,  # pyrefly: ignore[bad-argument-type]
                key,  # pyrefly: ignore[bad-argument-type]
            )
        aiohttp_session.assert_not_called()
        sync_httpx_client.assert_not_called()
        async_httpx_client.assert_not_called()


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
            realtime=RealtimeClientOptions(
                heartbeat_interval=30,
                heartbeat_timeout=10,
                timeout=4,
                max_queued_messages=50,
                disconnect_on_empty_channels_after=3,
                logger=logging.getLogger("my_app.realtime"),
            ),
        )

    assert client.realtime.heartbeat_interval == 30
    assert client.realtime.heartbeat_timeout == 10
    assert client.realtime.timeout == 4
    assert client.realtime.max_queued_messages == 50
    assert client.realtime.disconnect_on_empty_channels_after == 3
    assert client.realtime._logger.logger.name == "my_app.realtime"


async def test_async_client_reuses_one_realtime_client() -> None:
    async with AsyncHttpxClient() as http_client:
        client = AsyncClient(URL, KEY, AsyncHttpxSession(client=http_client))

    channel = client.realtime.channel("room")

    assert client.realtime is client.realtime
    assert client.realtime.get_channels() == [channel]


async def test_async_client_closes_realtime_on_exit() -> None:
    with patch.object(RealtimeClient, "aclose", AsyncMock()) as close:
        async with AsyncClient(
            URL, KEY, AsyncHttpxSession(client=AsyncHttpxClient())
        ) as client:
            client.realtime.channel("room")

    close.assert_awaited_once()


async def test_with_token_client_has_its_own_realtime_client() -> None:
    async with AsyncHttpxClient() as http_client:
        client = AsyncClient(URL, KEY, AsyncHttpxSession(client=http_client))
        channel = client.realtime.channel("room")

        with patch.object(RealtimeClient, "aclose", AsyncMock()) as close:
            async with client.with_token("user-jwt") as scoped:
                assert scoped.realtime is not client.realtime

        close.assert_awaited_once()
        assert client.realtime.get_channels() == [channel]


async def test_async_client_does_not_create_realtime_on_exit() -> None:
    async with AsyncClient(
        URL, KEY, AsyncHttpxSession(client=AsyncHttpxClient())
    ) as client:
        pass

    assert "realtime" not in client.__dict__


async def test_async_client_closes_the_http_session_when_realtime_close_fails() -> None:
    client = supabase.httpx.create_async_client(URL, KEY)
    assert isinstance(client.http_session, AsyncHttpxSession)
    client.realtime.channel("room")

    with (
        patch.object(
            RealtimeClient, "aclose", AsyncMock(side_effect=OSError("socket closed"))
        ),
        pytest.raises(OSError, match="socket closed"),
    ):
        await client.aclose()

    assert client.http_session.client.is_closed


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


@pytest.mark.parametrize("key", SESSION_KEYS)
def test_sync_functions_send_the_session_token_with_a_new_format_key(
    key: str,
) -> None:
    requests: list[httpx.Request] = []
    with SyncHttpxClient(transport=recording_transport(requests)) as http_client:
        client = Client(URL, key, HttpxSession(client=http_client))
        client.auth.session_manager.notify_all_subscribers(
            AuthStateChange(
                AuthChangeEvent.SIGNED_IN, MagicMock(access_token="userjwt")
            )
        )
        client.functions.invoke("hello")
        client.auth.session_manager.notify_all_subscribers(
            AuthStateChange(AuthChangeEvent.SIGNED_OUT)
        )
        client.functions.invoke("hello")

    signed_in, signed_out = requests
    assert signed_in.headers.get("apikey") == key
    assert signed_in.headers.get("authorization") == "Bearer userjwt"
    assert signed_out.headers.get("apikey") == key
    assert "authorization" not in signed_out.headers
    assert client.postgrest.default_headers.get("Authorization") == f"Bearer {key}"


@pytest.mark.parametrize("key", SESSION_KEYS)
async def test_async_functions_send_the_session_token_with_a_new_format_key(
    key: str,
) -> None:
    requests: list[httpx.Request] = []
    async with AsyncHttpxClient(transport=recording_transport(requests)) as http_client:
        client = AsyncClient(URL, key, AsyncHttpxSession(client=http_client))
        client.auth.session_manager.notify_all_subscribers(
            AuthStateChange(
                AuthChangeEvent.SIGNED_IN, MagicMock(access_token="userjwt")
            )
        )
        await client.functions.invoke("hello")
        client.auth.session_manager.notify_all_subscribers(
            AuthStateChange(AuthChangeEvent.SIGNED_OUT)
        )
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


def test_sync_client_passes_retry_policies_to_sub_clients() -> None:
    shared = RetryPolicy(max_retries=5)
    database = RetryPolicy(max_retries=1)
    uploads = RetryPolicy(retryable_methods={"GET", "HEAD", "POST", "PUT"})
    with SyncHttpxClient() as http_client:
        client = Client(
            URL,
            KEY,
            HttpxSession(client=http_client),
            retry=shared,
            postgrest=PostgrestClientOptions(retry=database),
            storage=StorageClientOptions(retry=uploads),
        )
        assert client.postgrest.executor.retry_policy is database
        assert client.storage.executor.retry_policy is uploads
        assert client.auth.executor.retry_policy is shared
        assert client.functions.executor.retry_policy is shared


async def test_async_client_passes_retry_policies_to_sub_clients() -> None:
    policy = RetryPolicy(max_retries=0)
    async with AsyncHttpxClient() as http_client:
        client = AsyncClient(
            URL,
            KEY,
            AsyncHttpxSession(client=http_client),
            functions=FunctionsClientOptions(retry=policy),
        )
        assert client.functions.executor.retry_policy is policy
        assert client.postgrest.executor.retry_policy == RetryPolicy()
        assert client.storage.executor.retry_policy == RetryPolicy()
        assert client.auth.executor.retry_policy == RetryPolicy()


def test_create_client_passes_the_retry_policy() -> None:
    policy = RetryPolicy(max_retries=2)
    with supabase.httpx.create_client(URL, KEY, retry=policy) as client:
        assert client.postgrest.executor.retry_policy is policy
        assert client.auth.executor.retry_policy is policy


async def test_create_async_clients_pass_the_retry_policy() -> None:
    policy = RetryPolicy(max_retries=2)
    async with supabase.httpx.create_async_client(URL, KEY, retry=policy) as client:
        assert client.storage.executor.retry_policy is policy
    async with supabase.aiohttp.create_async_client(URL, KEY, retry=policy) as client:
        assert client.functions.executor.retry_policy is policy


def test_retry_policy_is_exported_from_supabase() -> None:
    assert ExportedRetryPolicy is RetryPolicy
    assert "RetryPolicy" in supabase.__all__


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
                append_flow_id_to_redirects=True,
            ),
        )
        assert client.postgrest.default_headers.get("Accept-Profile") == "private"
        assert client.auth.session_manager.storage is session_storage
        assert client.auth.session_manager.storage_key == "custom-key"
        assert client.auth.session_manager.auto_refresh_token is False
        assert client.auth.flow_type == "implicit"
        assert client.auth.append_flow_id_to_redirects is True


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
                append_flow_id_to_redirects=True,
            ),
        )
        assert client.postgrest.default_headers.get("Accept-Profile") == "private"
        assert client.auth.session_manager.storage is session_storage
        assert client.auth.session_manager.storage_key == "custom-key"
        assert client.auth.session_manager.auto_refresh_token is False
        assert client.auth.flow_type == "implicit"
        assert client.auth.append_flow_id_to_redirects is True


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
            AuthStateChange(
                AuthChangeEvent.SIGNED_IN, MagicMock(access_token="userjwt")
            )
        )

    assert headers["Authorization"] == "Bearer userjwt"


def sign_in(client: Client | AsyncClient) -> None:
    client.auth.session_manager.notify_all_subscribers(
        AuthStateChange(AuthChangeEvent.SIGNED_IN, MagicMock(access_token="userjwt"))
    )


def authorization_headers(client: Client | AsyncClient) -> list[str | None]:
    return [
        client.headers["Authorization"],
        client.auth.default_headers.get("Authorization"),
        client.postgrest.default_headers.get("Authorization"),
        client.storage.default_headers.get("Authorization"),
    ]


@pytest.mark.parametrize("key", PUBLIC_KEYS)
def test_sync_client_sends_the_session_token_with_a_public_key(key: str) -> None:
    with SyncHttpxClient() as http_client:
        client = Client(URL, key, HttpxSession(client=http_client))
        sign_in(client)

    assert authorization_headers(client) == ["Bearer userjwt"] * 4


SECRET_KEY_FUNCTIONS_AUTHORIZATION = [
    ("sb_secret_abc123", None),
    (SERVICE_ROLE_JWT, f"Bearer {SERVICE_ROLE_JWT}"),
]


@pytest.mark.parametrize(
    ("key", "functions_authorization"), SECRET_KEY_FUNCTIONS_AUTHORIZATION
)
def test_sync_client_keeps_a_secret_key_after_a_sign_in(
    key: str, functions_authorization: str | None, caplog: pytest.LogCaptureFixture
) -> None:
    requests: list[httpx.Request] = []
    with SyncHttpxClient(transport=recording_transport(requests)) as http_client:
        client = Client(URL, key, HttpxSession(client=http_client))
        sign_in(client)
        sign_in(client)
        client.functions.invoke("hello")

    assert authorization_headers(client) == [f"Bearer {key}"] * 4
    assert requests[0].headers.get("authorization") == functions_authorization
    assert [record.levelname for record in caplog.records] == ["WARNING"]
    assert "service_role" in caplog.records[0].getMessage()


@pytest.mark.parametrize("key", PUBLIC_KEYS)
def test_sync_client_does_not_warn_on_a_sign_in_with_a_public_key(
    key: str, caplog: pytest.LogCaptureFixture
) -> None:
    with SyncHttpxClient() as http_client:
        client = Client(URL, key, HttpxSession(client=http_client))
        sign_in(client)

    assert caplog.records == []


@pytest.mark.parametrize(
    ("key", "functions_authorization"), SECRET_KEY_FUNCTIONS_AUTHORIZATION
)
async def test_async_client_keeps_a_secret_key_after_a_sign_in(
    key: str, functions_authorization: str | None
) -> None:
    requests: list[httpx.Request] = []
    async with AsyncHttpxClient(transport=recording_transport(requests)) as http_client:
        client = AsyncClient(URL, key, AsyncHttpxSession(client=http_client))
        sign_in(client)
        await client.functions.invoke("hello")
        with patch.object(
            AsyncSupabaseAuthClient,
            "get_session",
            AsyncMock(return_value=MagicMock(access_token="userjwt")),
        ):
            realtime_token = await client._realtime_access_token()

    assert authorization_headers(client) == [f"Bearer {key}"] * 4
    assert requests[0].headers.get("authorization") == functions_authorization
    assert realtime_token == key


@pytest.mark.parametrize("key", SECRET_KEYS)
def test_sync_create_keeps_a_secret_key_with_a_stored_session(key: str) -> None:
    session = MagicMock(access_token="storedjwt")
    with (
        SyncHttpxClient() as http_client,
        patch.object(
            SyncSupabaseAuthClient, "get_session", MagicMock(return_value=session)
        ),
    ):
        client = Client.create(URL, key, HttpxSession(client=http_client))

    assert authorization_headers(client) == [f"Bearer {key}"] * 4


@pytest.mark.parametrize("key", SECRET_KEYS)
async def test_async_create_keeps_a_secret_key_with_a_stored_session(key: str) -> None:
    session = MagicMock(access_token="storedjwt")
    async with AsyncHttpxClient() as http_client:
        with patch.object(
            AsyncSupabaseAuthClient, "get_session", AsyncMock(return_value=session)
        ):
            client = await AsyncClient.create(
                URL, key, AsyncHttpxSession(client=http_client)
            )

    assert authorization_headers(client) == [f"Bearer {key}"] * 4


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


def test_sync_client_shares_one_auth_client_between_threads() -> None:
    with SyncHttpxClient() as http_client:
        client = Client(URL, KEY, HttpxSession(client=http_client))
        with ThreadPoolExecutor(max_workers=8) as pool:
            futures = [pool.submit(lambda: client.auth) for _ in range(32)]
            auth_clients = [future.result() for future in futures]

    assert all(auth is auth_clients[0] for auth in auth_clients)


def expired_session_json() -> str:
    return json.dumps(
        {
            "access_token": "storedjwt",
            "refresh_token": "storedrefresh",
            "token_type": "bearer",
            "expires_in": 3600,
            "expires_at": 1,
            "user": {
                "id": "11111111-1111-1111-1111-111111111111",
                "aud": "authenticated",
                "app_metadata": {},
                "user_metadata": {},
                "created_at": "2026-01-01T00:00:00Z",
            },
        }
    )


def token_endpoint(status_code: int) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code,
            json={"error_code": "refresh_token_not_found", "msg": "rejected"},
        )

    return httpx.MockTransport(handler)


class FailingSyncStorage(SyncMemoryStorage):
    @override
    def get_item(self, key: str) -> str | None:
        raise OSError("storage is unreachable")


class FailingAsyncStorage(AsyncMemoryStorage):
    @override
    async def get_item(self, key: str) -> str | None:
        raise OSError("storage is unreachable")


NO_RETRY = RetryPolicy(max_retries=0)


def test_sync_create_starts_without_a_session_when_its_refresh_is_rejected() -> None:
    storage = SyncMemoryStorage()
    storage.set_item(STORAGE_KEY, expired_session_json())
    with SyncHttpxClient(transport=token_endpoint(400)) as http_client:
        client = Client.create(
            URL,
            KEY,
            HttpxSession(client=http_client),
            auth=AuthClientOptions(session_storage=storage),
        )

    assert authorization_headers(client) == [f"Bearer {KEY}"] * 4
    assert storage.storage == {}


async def test_async_create_starts_without_a_session_when_its_refresh_is_rejected() -> (
    None
):
    storage = AsyncMemoryStorage()
    await storage.set_item(STORAGE_KEY, expired_session_json())
    async with AsyncHttpxClient(transport=token_endpoint(400)) as http_client:
        client = await AsyncClient.create(
            URL,
            KEY,
            AsyncHttpxSession(client=http_client),
            auth=AuthClientOptions(session_storage=storage),
        )
        await client.aclose()

    assert authorization_headers(client) == [f"Bearer {KEY}"] * 4
    assert storage.storage == {}


def test_sync_create_raises_a_refresh_failure_worth_retrying() -> None:
    storage = SyncMemoryStorage()
    storage.set_item(STORAGE_KEY, expired_session_json())
    with (
        SyncHttpxClient(transport=token_endpoint(503)) as http_client,
        pytest.raises(AuthRetryableError),
    ):
        Client.create(
            URL,
            KEY,
            HttpxSession(client=http_client),
            retry=NO_RETRY,
            auth=AuthClientOptions(session_storage=storage),
        )

    assert STORAGE_KEY in storage.storage


async def test_async_create_raises_a_refresh_failure_worth_retrying() -> None:
    storage = AsyncMemoryStorage()
    await storage.set_item(STORAGE_KEY, expired_session_json())
    async with AsyncHttpxClient(transport=token_endpoint(503)) as http_client:
        with pytest.raises(AuthRetryableError):
            await AsyncClient.create(
                URL,
                KEY,
                AsyncHttpxSession(client=http_client),
                retry=NO_RETRY,
                auth=AuthClientOptions(session_storage=storage),
            )

    assert STORAGE_KEY in storage.storage


def test_sync_create_raises_a_session_storage_failure() -> None:
    with (
        SyncHttpxClient() as http_client,
        pytest.raises(OSError, match="storage is unreachable"),
    ):
        Client.create(
            URL,
            KEY,
            HttpxSession(client=http_client),
            auth=AuthClientOptions(session_storage=FailingSyncStorage()),
        )


async def test_async_create_raises_a_session_storage_failure() -> None:
    async with AsyncHttpxClient() as http_client:
        with pytest.raises(OSError, match="storage is unreachable"):
            await AsyncClient.create(
                URL,
                KEY,
                AsyncHttpxSession(client=http_client),
                auth=AuthClientOptions(session_storage=FailingAsyncStorage()),
            )
