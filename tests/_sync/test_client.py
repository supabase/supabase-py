import os
from typing import Any
from unittest.mock import MagicMock, SyncMock

import pytest
from gotrue import SyncMemoryStorage
from httpx import Limits
from httpx import SyncClient as SyncHttpxClient
from httpx import SyncHTTPTransport, Timeout

from supabase import (
    SyncClient,
    SyncClientOptions,
    SyncSupabaseException,
    create_async_client,
)


@pytest.mark.xfail(
    reason="None of these values should be able to instantiate a client object"
)
@pytest.mark.parametrize("url", ["", None, "valeefgpoqwjgpj", 139, -1, {}, []])
@pytest.mark.parametrize("key", ["", None, "valeefgpoqwjgpj", 139, -1, {}, []])
def test_incorrect_values_dont_instantiate_client(url: Any, key: Any) -> None:
    """Ensure we can't instantiate client with invalid values."""
    try:
        _: SyncClient = create_async_client(url, key)
    except SyncSupabaseException:
        pass


def test_supabase_exception() -> None:
    try:
        raise SyncSupabaseException("err")
    except SyncSupabaseException:
        pass


def test_postgrest_client() -> None:
    url = os.environ.get("SUPABASE_TEST_URL")
    key = os.environ.get("SUPABASE_TEST_KEY")

    client = create_async_client(url, key)
    assert client.table("sample")
    assert client.postgrest.schema("new_schema")


def test_rpc_client() -> None:
    url = os.environ.get("SUPABASE_TEST_URL")
    key = os.environ.get("SUPABASE_TEST_KEY")

    client = create_async_client(url, key)
    assert client.rpc("test_fn")


def test_function_initialization() -> None:
    url = os.environ.get("SUPABASE_TEST_URL")
    key = os.environ.get("SUPABASE_TEST_KEY")

    client = create_async_client(url, key)
    assert client.functions


def test_uses_key_as_authorization_header_by_default() -> None:
    url = os.environ.get("SUPABASE_TEST_URL")
    key = os.environ.get("SUPABASE_TEST_KEY")

    client = create_async_client(url, key)

    assert client.options.headers.get("apiKey") == key
    assert client.options.headers.get("Authorization") == f"Bearer {key}"

    assert client.postgrest.session.headers.get("apiKey") == key
    assert client.postgrest.session.headers.get("Authorization") == f"Bearer {key}"

    assert client.auth._headers.get("apiKey") == key
    assert client.auth._headers.get("Authorization") == f"Bearer {key}"

    assert client.storage.session.headers.get("apiKey") == key
    assert client.storage.session.headers.get("Authorization") == f"Bearer {key}"


def test_schema_update() -> None:
    url = os.environ.get("SUPABASE_TEST_URL")
    key = os.environ.get("SUPABASE_TEST_KEY")

    client = create_async_client(url, key)
    assert client.postgrest
    assert client.schema("new_schema")


def test_updates_the_authorization_header_on_auth_events() -> None:
    url = os.environ.get("SUPABASE_TEST_URL")
    key = os.environ.get("SUPABASE_TEST_KEY")

    client = create_async_client(url, key)

    assert client.options.headers.get("apiKey") == key
    assert client.options.headers.get("Authorization") == f"Bearer {key}"

    mock_session = MagicMock(access_token="secretuserjwt")
    realtime_mock = SyncMock()
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


def test_supports_setting_a_global_authorization_header() -> None:
    url = os.environ.get("SUPABASE_TEST_URL")
    key = os.environ.get("SUPABASE_TEST_KEY")

    authorization = "Bearer secretuserjwt"

    options = SyncClientOptions(headers={"Authorization": authorization})

    client = create_async_client(url, key, options)

    assert client.options.headers.get("apiKey") == key
    assert client.options.headers.get("Authorization") == authorization

    assert client.postgrest.session.headers.get("apiKey") == key
    assert client.postgrest.session.headers.get("Authorization") == authorization

    assert client.auth._headers.get("apiKey") == key
    assert client.auth._headers.get("Authorization") == authorization

    assert client.storage.session.headers.get("apiKey") == key
    assert client.storage.session.headers.get("Authorization") == authorization


def test_mutable_headers_issue():
    url = os.environ.get("SUPABASE_TEST_URL")
    key = os.environ.get("SUPABASE_TEST_KEY")

    shared_options = SyncClientOptions(
        storage=SyncMemoryStorage(), headers={"Authorization": "Bearer initial-token"}
    )

    client1 = create_async_client(url, key, shared_options)
    client2 = create_async_client(url, key, shared_options)

    client1.options.headers["Authorization"] = "Bearer modified-token"

    assert client2.options.headers["Authorization"] == "Bearer initial-token"
    assert client1.options.headers["Authorization"] == "Bearer modified-token"


def test_global_authorization_header_issue():
    url = os.environ.get("SUPABASE_TEST_URL")
    key = os.environ.get("SUPABASE_TEST_KEY")

    authorization = "Bearer secretuserjwt"
    options = SyncClientOptions(headers={"Authorization": authorization})

    client = create_async_client(url, key, options)

    assert client.options.headers.get("apiKey") == key


def test_httpx_client():
    url = os.environ.get("SUPABASE_TEST_URL")
    key = os.environ.get("SUPABASE_TEST_KEY")

    transport = SyncHTTPTransport(
        retries=10,
        verify=False,
        limits=Limits(
            max_connections=1,
        ),
    )

    headers = {"x-user-agent": "my-app/0.0.1"}
    with SyncHttpxClient(
        transport=transport, headers=headers, timeout=Timeout(2.0)
    ) as http_client:
        # Create a client with the custom httpx client
        options = SyncClientOptions(httpx_client=http_client)

        client = create_async_client(url, key, options)

        assert client.postgrest.session.headers.get("x-user-agent") == "my-app/0.0.1"
        assert client.auth._http_client.headers.get("x-user-agent") == "my-app/0.0.1"
        assert client.storage.session.headers.get("x-user-agent") == "my-app/0.0.1"
        assert client.functions._client.headers.get("x-user-agent") == "my-app/0.0.1"
        assert client.postgrest.session.timeout == Timeout(2.0)
        assert client.auth._http_client.timeout == Timeout(2.0)
        assert client.storage.session.timeout == Timeout(2.0)
        assert client.functions._client.timeout == Timeout(2.0)
