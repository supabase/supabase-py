import os
from typing import Any
from unittest.mock import AsyncMock, MagicMock

import pytest
from supabase_auth import AsyncMemoryStorage
from httpx import AsyncClient as AsyncHttpxClient
from httpx import AsyncHTTPTransport, Limits, Timeout

from supabase import (
    AsyncClient,
    AsyncClientOptions,
    AsyncSupabaseException,
    create_async_client,
)


@pytest.mark.xfail(
    reason="None of these values should be able to instantiate a client object"
)
@pytest.mark.parametrize("url", ["", None, "valeefgpoqwjgpj", 139, -1, {}, []])
@pytest.mark.parametrize("key", ["", None, "valeefgpoqwjgpj", 139, -1, {}, []])
async def test_incorrect_values_dont_instantiate_client(url: Any, key: Any) -> None:
    """Ensure we can't instantiate client with invalid values."""
    try:
        _: AsyncClient = await create_async_client(url, key)
    except AsyncSupabaseException:
        pass


async def test_supabase_exception() -> None:
    try:
        raise AsyncSupabaseException("err")
    except AsyncSupabaseException:
        pass


async def test_postgrest_client() -> None:
    url = os.environ.get("SUPABASE_TEST_URL")
    key = os.environ.get("SUPABASE_TEST_KEY")

    client = await create_async_client(url, key)
    assert client.table("sample")
    assert client.postgrest.schema("new_schema")


async def test_rpc_client() -> None:
    url = os.environ.get("SUPABASE_TEST_URL")
    key = os.environ.get("SUPABASE_TEST_KEY")

    client = await create_async_client(url, key)
    assert client.rpc("test_fn")


async def test_function_initialization() -> None:
    url = os.environ.get("SUPABASE_TEST_URL")
    key = os.environ.get("SUPABASE_TEST_KEY")

    client = await create_async_client(url, key)
    assert client.functions


async def test_uses_key_as_authorization_header_by_default() -> None:
    url = os.environ.get("SUPABASE_TEST_URL")
    key = os.environ.get("SUPABASE_TEST_KEY")

    client = await create_async_client(url, key)

    assert client.options.headers.get("apiKey") == key
    assert client.options.headers.get("Authorization") == f"Bearer {key}"

    assert client.postgrest.session.headers.get("apiKey") == key
    assert client.postgrest.session.headers.get("Authorization") == f"Bearer {key}"

    assert client.auth._headers.get("apiKey") == key
    assert client.auth._headers.get("Authorization") == f"Bearer {key}"

    assert client.storage.session.headers.get("apiKey") == key
    assert client.storage.session.headers.get("Authorization") == f"Bearer {key}"


async def test_schema_update() -> None:
    url = os.environ.get("SUPABASE_TEST_URL")
    key = os.environ.get("SUPABASE_TEST_KEY")

    client = await create_async_client(url, key)
    assert client.postgrest
    assert client.schema("new_schema")


async def test_updates_the_authorization_header_on_auth_events() -> None:
    url = os.environ.get("SUPABASE_TEST_URL")
    key = os.environ.get("SUPABASE_TEST_KEY")

    client = await create_async_client(url, key)

    assert client.options.headers.get("apiKey") == key
    assert client.options.headers.get("Authorization") == f"Bearer {key}"

    mock_session = MagicMock(access_token="secretuserjwt")
    realtime_mock = AsyncMock()
    client.realtime = realtime_mock

    client._listen_to_auth_events("SIGNED_IN", mock_session)

    updated_authorization = f"Bearer {mock_session.access_token}"

    assert client.options.headers.get("apiKey") == key
    assert client.options.headers.get("Authorization") == updated_authorization

    assert client.postgrest.session.headers.get("apiKey") == key
    assert (
        client.postgrest.session.headers.get("Authorization") == updated_authorization
    )

    assert client.auth._headers.get("apiKey") == key
    assert client.auth._headers.get("Authorization") == updated_authorization

    assert client.storage.session.headers.get("apiKey") == key
    assert client.storage.session.headers.get("Authorization") == updated_authorization


async def test_supports_setting_a_global_authorization_header() -> None:
    url = os.environ.get("SUPABASE_TEST_URL")
    key = os.environ.get("SUPABASE_TEST_KEY")

    authorization = "Bearer secretuserjwt"

    options = AsyncClientOptions(headers={"Authorization": authorization})

    client = await create_async_client(url, key, options)

    assert client.options.headers.get("apiKey") == key
    assert client.options.headers.get("Authorization") == authorization

    assert client.postgrest.session.headers.get("apiKey") == key
    assert client.postgrest.session.headers.get("Authorization") == authorization

    assert client.auth._headers.get("apiKey") == key
    assert client.auth._headers.get("Authorization") == authorization

    assert client.storage.session.headers.get("apiKey") == key
    assert client.storage.session.headers.get("Authorization") == authorization


async def test_mutable_headers_issue():
    url = os.environ.get("SUPABASE_TEST_URL")
    key = os.environ.get("SUPABASE_TEST_KEY")

    shared_options = AsyncClientOptions(
        storage=AsyncMemoryStorage(), headers={"Authorization": "Bearer initial-token"}
    )

    client1 = await create_async_client(url, key, shared_options)
    client2 = await create_async_client(url, key, shared_options)

    client1.options.headers["Authorization"] = "Bearer modified-token"

    assert client2.options.headers["Authorization"] == "Bearer initial-token"
    assert client1.options.headers["Authorization"] == "Bearer modified-token"


async def test_global_authorization_header_issue():
    url = os.environ.get("SUPABASE_TEST_URL")
    key = os.environ.get("SUPABASE_TEST_KEY")

    authorization = "Bearer secretuserjwt"
    options = AsyncClientOptions(headers={"Authorization": authorization})

    client = await create_async_client(url, key, options)

    assert client.options.headers.get("apiKey") == key


async def test_httpx_client():
    url = os.environ.get("SUPABASE_TEST_URL")
    key = os.environ.get("SUPABASE_TEST_KEY")

    transport = AsyncHTTPTransport(
        retries=10,
        verify=False,
        limits=Limits(
            max_connections=1,
        ),
    )

    headers = {"x-user-agent": "my-app/0.0.1"}
    async with AsyncHttpxClient(
        transport=transport, headers=headers, timeout=Timeout(2.0)
    ) as http_client:
        # Create a client with the custom httpx client
        options = AsyncClientOptions(httpx_client=http_client)

        client = await create_async_client(url, key, options)

        assert client.postgrest.session.headers.get("x-user-agent") == "my-app/0.0.1"
        assert client.auth._http_client.headers.get("x-user-agent") == "my-app/0.0.1"
        assert client.storage.session.headers.get("x-user-agent") == "my-app/0.0.1"
        assert client.functions._client.headers.get("x-user-agent") == "my-app/0.0.1"
        assert client.postgrest.session.timeout == Timeout(2.0)
        assert client.auth._http_client.timeout == Timeout(2.0)
        assert client.storage.session.timeout == Timeout(2.0)
        assert client.functions._client.timeout == Timeout(2.0)


async def test_custom_headers():
    url = os.environ.get("SUPABASE_TEST_URL")
    key = os.environ.get("SUPABASE_TEST_KEY")

    options = AsyncClientOptions(
        headers={
            "x-app-name": "apple",
            "x-version": "1.0",
        }
    )

    client = await create_async_client(url, key, options)

    assert client.options.headers.get("x-app-name") == "apple"
    assert client.options.headers.get("x-version") == "1.0"


async def test_custom_headers_immutable():
    url = os.environ.get("SUPABASE_TEST_URL")
    key = os.environ.get("SUPABASE_TEST_KEY")

    options = AsyncClientOptions(
        headers={
            "x-app-name": "apple",
            "x-version": "1.0",
        }
    )

    client1 = await create_async_client(url, key, options)
    client2 = await create_async_client(url, key, options)

    client1.options.headers["x-app-name"] = "grapes"

    assert client1.options.headers.get("x-app-name") == "grapes"
    assert client1.options.headers.get("x-version") == "1.0"
    assert client2.options.headers.get("x-app-name") == "apple"
