import os
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient as AsyncHttpxClient
from supabase_auth import AsyncMemoryStorage, AsyncSupabaseAuthClient
from supabase_auth.types import AuthChangeEvent, AuthStateChange
from supabase_utils.http.adapters.httpx import AsyncHttpxSession

from supabase import (
    AsyncClient,
    AuthClientOptions,
)

from .conftest import AsyncClientCallable

url = os.environ["SUPABASE_TEST_URL"]
key = os.environ["SUPABASE_TEST_KEY"]


async def realtime_access_token(client: AsyncClient) -> str | None:
    token_callback = client.realtime.get_access_token
    assert token_callback is not None
    return await token_callback()


SESSION_EVENTS = [
    AuthChangeEvent.INITIAL_SESSION,
    AuthChangeEvent.SIGNED_IN,
    AuthChangeEvent.TOKEN_REFRESHED,
    AuthChangeEvent.USER_UPDATED,
    AuthChangeEvent.PASSWORD_RECOVERY,
    AuthChangeEvent.MFA_CHALLENGE_VERIFIED,
]


async def test_postgrest_client(create_async_client: AsyncClientCallable) -> None:
    async with create_async_client(url, key) as client:
        assert client.table("sample")
        assert client.postgrest.schema("new_schema")


async def test_rpc_client(create_async_client: AsyncClientCallable) -> None:
    async with create_async_client(url, key) as client:
        assert client.rpc("test_fn")


async def test_function_initialization(
    create_async_client: AsyncClientCallable,
) -> None:
    async with create_async_client(url, key) as client:
        assert client.functions.executor.session is client.http_session


async def test_uses_key_as_authorization_header_by_default(
    create_async_client: AsyncClientCallable,
) -> None:
    async with create_async_client(url, key) as client:
        assert client.headers.get("apiKey") == key
        assert client.headers.get("Authorization") == f"Bearer {key}"

        assert client.postgrest.default_headers.get("apiKey") == key
        assert client.postgrest.default_headers.get("Authorization") == f"Bearer {key}"

        assert client.auth.default_headers.get("apiKey") == key
        assert client.auth.default_headers.get("Authorization") == f"Bearer {key}"

        assert client.storage.default_headers.get("apiKey") == key
        assert client.storage.default_headers.get("Authorization") == f"Bearer {key}"


async def test_schema_update(create_async_client: AsyncClientCallable) -> None:
    async with create_async_client(url, key) as client:
        assert client.postgrest
        assert client.schema("new_schema")


async def test_sub_clients_are_built_once(
    create_async_client: AsyncClientCallable,
) -> None:
    async with create_async_client(url, key) as client:
        assert client.auth is client.auth
        assert client.postgrest is client.postgrest
        assert client.storage is client.storage
        assert client.functions is client.functions


@pytest.mark.parametrize("event", SESSION_EVENTS)
async def test_auth_events_with_a_session_use_its_access_token(
    create_async_client: AsyncClientCallable, event: AuthChangeEvent
) -> None:
    async with create_async_client(url, key) as client:
        postgrest = client.postgrest
        storage = client.storage
        functions = client.functions
        session = MagicMock(access_token="secretuserjwt")

        client.auth.session_manager.notify_all_subscribers(
            AuthStateChange(event, session)
        )

        authorization = "Bearer secretuserjwt"
        assert client.postgrest is postgrest
        assert client.storage is storage
        assert client.functions is functions
        assert client.headers.get("apiKey") == key
        assert client.headers.get("Authorization") == authorization
        assert client.postgrest.default_headers.get("Authorization") == authorization
        assert client.storage.default_headers.get("Authorization") == authorization
        assert client.functions.default_headers.get("Authorization") == authorization
        assert client.auth.default_headers.get("Authorization") == authorization
        assert await realtime_access_token(client) == "secretuserjwt"


async def test_auth_events_without_a_session_use_the_key(
    create_async_client: AsyncClientCallable,
) -> None:
    async with create_async_client(url, key) as client:
        client.auth.session_manager.notify_all_subscribers(
            AuthStateChange(
                AuthChangeEvent.SIGNED_IN, MagicMock(access_token="secretuserjwt")
            )
        )

        client.auth.session_manager.notify_all_subscribers(
            AuthStateChange(AuthChangeEvent.SIGNED_OUT)
        )

        authorization = f"Bearer {key}"
        assert client.headers.get("Authorization") == authorization
        assert client.postgrest.default_headers.get("Authorization") == authorization
        assert client.storage.default_headers.get("Authorization") == authorization
        assert client.functions.default_headers.get("Authorization") == authorization
        assert client.auth.default_headers.get("Authorization") == authorization
        assert await realtime_access_token(client) == key


async def test_create_uses_the_stored_session_token() -> None:
    session = MagicMock(access_token="secretuserjwt")
    async with AsyncHttpxClient() as http_client:
        with patch.object(
            AsyncSupabaseAuthClient, "get_session", AsyncMock(return_value=session)
        ):
            client = await AsyncClient.create(
                url, key, AsyncHttpxSession(client=http_client)
            )

        authorization = "Bearer secretuserjwt"
        assert client.headers.get("Authorization") == authorization
        assert client.postgrest.default_headers.get("Authorization") == authorization
        assert client.auth.default_headers.get("Authorization") == authorization
        assert await realtime_access_token(client) == "secretuserjwt"


async def test_supports_setting_a_global_authorization_header(
    create_async_client: AsyncClientCallable,
) -> None:
    authorization = "Bearer secretuserjwt"

    async with create_async_client(
        url, key, headers={"Authorization": authorization}
    ) as client:
        assert client.headers.get("apiKey") == key
        assert client.headers.get("Authorization") == authorization

        assert client.postgrest.default_headers.get("apiKey") == key
        assert client.postgrest.default_headers.get("Authorization") == authorization

        assert client.auth.default_headers.get("apiKey") == key
        assert client.auth.default_headers.get("Authorization") == authorization

        assert client.storage.default_headers.get("apiKey") == key
        assert client.storage.default_headers.get("Authorization") == authorization

        assert await realtime_access_token(client) == "secretuserjwt"


async def test_realtime_uses_the_key_with_a_non_bearer_authorization_header(
    create_async_client: AsyncClientCallable,
) -> None:
    async with create_async_client(
        url, key, headers={"Authorization": "Basic dXNlcjpwYXNz"}
    ) as client:
        assert await realtime_access_token(client) == key


async def test_mutable_headers_issue(create_async_client: AsyncClientCallable) -> None:
    shared_headers = {"Authorization": "Bearer initial-token"}
    shared_auth = AuthClientOptions(session_storage=AsyncMemoryStorage())

    async with (
        create_async_client(
            url, key, headers=shared_headers, auth=shared_auth
        ) as client1,
        create_async_client(
            url, key, headers=shared_headers, auth=shared_auth
        ) as client2,
    ):
        client1._set_access_token("modified-token")
        assert client2.headers["Authorization"] == "Bearer initial-token"
        assert client1.headers["Authorization"] == "Bearer modified-token"
        assert shared_headers["Authorization"] == "Bearer initial-token"


async def test_global_authorization_header_issue(
    create_async_client: AsyncClientCallable,
) -> None:
    authorization = "Bearer secretuserjwt"
    async with create_async_client(
        url, key, headers={"Authorization": authorization}
    ) as client:
        assert client.headers.get("apiKey") == key


async def test_custom_headers(create_async_client: AsyncClientCallable) -> None:
    headers = {"x-app-name": "apple", "x-version": "1.0"}

    async with create_async_client(url, key, headers=headers) as client:
        assert client.headers.get("x-app-name") == "apple"
        assert client.headers.get("x-version") == "1.0"


async def test_custom_headers_immutable(
    create_async_client: AsyncClientCallable,
) -> None:
    headers = {"x-app-name": "apple", "x-version": "1.0"}
    async with create_async_client(url, key, headers=headers) as client:
        headers["x-app-name"] = "grapes"

        assert client.headers.get("x-app-name") == "apple"
        assert client.headers.get("x-version") == "1.0"


async def test_httpx_client_base_url_isolation(
    create_async_client: AsyncClientCallable,
) -> None:
    """Test that shared httpx_client doesn't cause base_url mutation between services.
    This test reproduces the issue where accessing PostgREST after Storage causes
    Storage requests to hit the wrong endpoint (404 errors).
    See: https://github.com/supabase/supabase-py/issues/1244
    """
    # Create client with shared httpx instance
    async with create_async_client(url, key) as client:
        # Access storage and capture its base_url
        storage = client.storage
        storage_base_url = str(storage.base_url).rstrip("/")
        assert storage_base_url.endswith("/storage/v1"), (
            f"Expected storage base_url to end with '/storage/v1', got {storage_base_url}"
        )

        # Access postgrest (this should NOT mutate storage's base_url)
        postgrest = client.postgrest
        postgrest_base_url = str(postgrest.base_url).rstrip("/")
        assert postgrest_base_url.endswith("/rest/v1"), (
            f"Expected postgrest base_url to end with '/rest/v1', got {postgrest_base_url}"
        )

        # Verify storage still has the correct base_url
        storage_base_url_after = str(storage.base_url).rstrip("/")
        assert storage_base_url_after.endswith("/storage/v1"), (
            f"Storage base_url was mutated! Expected '/storage/v1', got {storage_base_url_after}"
        )

        assert str(storage.base_url).rstrip("/").endswith("/storage/v1"), (
            "Storage base_url was mutated after accessing functions"
        )
        assert str(postgrest.base_url).rstrip("/").endswith("/rest/v1"), (
            "PostgREST base_url was mutated after accessing functions"
        )
