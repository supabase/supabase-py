import os
from typing import Any
from unittest.mock import Mock, MagicMock

import pytest
from supabase_auth import SyncMemoryStorage
from httpx import Client as SyncHttpxClient
from httpx import HTTPTransport, Limits, Timeout

from supabase import (
    Client,
    ClientOptions,
    SyncSupabaseException,
    create_client,
)


@pytest.mark.xfail(
    reason="None of these values should be able to instantiate a client object"
)
@pytest.mark.parametrize("url", ["", None, "valeefgpoqwjgpj", 139, -1, {}, []])
@pytest.mark.parametrize("key", ["", None, "valeefgpoqwjgpj", 139, -1, {}, []])
def test_incorrect_values_dont_instantiate_client(url: Any, key: Any) -> None:
    """Ensure we can't instantiate client with invalid values."""
    try:
        _: Client = create_client(url, key)
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

    client = create_client(url, key)
    assert client.table("sample")
    assert client.postgrest.schema("new_schema")


def test_rpc_client() -> None:
    url = os.environ.get("SUPABASE_TEST_URL")
    key = os.environ.get("SUPABASE_TEST_KEY")

    client = create_client(url, key)
    assert client.rpc("test_fn")


def test_function_initialization() -> None:
    url = os.environ.get("SUPABASE_TEST_URL")
    key = os.environ.get("SUPABASE_TEST_KEY")

    client = create_client(url, key)
    assert client.functions


def test_uses_key_as_authorization_header_by_default() -> None:
    url = os.environ.get("SUPABASE_TEST_URL")
    key = os.environ.get("SUPABASE_TEST_KEY")

    client = create_client(url, key)

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

    client = create_client(url, key)
    assert client.postgrest
    assert client.schema("new_schema")


def test_updates_the_authorization_header_on_auth_events() -> None:
    url = os.environ.get("SUPABASE_TEST_URL")
    key = os.environ.get("SUPABASE_TEST_KEY")

    client = create_client(url, key)

    assert client.options.headers.get("apiKey") == key
    assert client.options.headers.get("Authorization") == f"Bearer {key}"

    mock_session = MagicMock(access_token="secretuserjwt")
    realtime_mock = Mock()
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

    options = ClientOptions(headers={"Authorization": authorization})

    client = create_client(url, key, options)

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

    shared_options = ClientOptions(
        storage=SyncMemoryStorage(), headers={"Authorization": "Bearer initial-token"}
    )

    client1 = create_client(url, key, shared_options)
    client2 = create_client(url, key, shared_options)

    client1.options.headers["Authorization"] = "Bearer modified-token"

    assert client2.options.headers["Authorization"] == "Bearer initial-token"
    assert client1.options.headers["Authorization"] == "Bearer modified-token"


def test_global_authorization_header_issue():
    url = os.environ.get("SUPABASE_TEST_URL")
    key = os.environ.get("SUPABASE_TEST_KEY")

    authorization = "Bearer secretuserjwt"
    options = ClientOptions(headers={"Authorization": authorization})

    client = create_client(url, key, options)

    assert client.options.headers.get("apiKey") == key


def test_httpx_client():
    url = os.environ.get("SUPABASE_TEST_URL")
    key = os.environ.get("SUPABASE_TEST_KEY")

    transport = HTTPTransport(
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
        options = ClientOptions(httpx_client=http_client)

        client = create_client(url, key, options)

        assert client.postgrest.session.headers.get("x-user-agent") == "my-app/0.0.1"
        assert client.auth._http_client.headers.get("x-user-agent") == "my-app/0.0.1"
        assert client.storage.session.headers.get("x-user-agent") == "my-app/0.0.1"
        assert client.functions._client.headers.get("x-user-agent") == "my-app/0.0.1"
        assert client.postgrest.session.timeout == Timeout(2.0)
        assert client.auth._http_client.timeout == Timeout(2.0)
        assert client.storage.session.timeout == Timeout(2.0)
        assert client.functions._client.timeout == Timeout(2.0)


def test_custom_headers():
    url = os.environ.get("SUPABASE_TEST_URL")
    key = os.environ.get("SUPABASE_TEST_KEY")

    options = ClientOptions(
        headers={
            "x-app-name": "apple",
            "x-version": "1.0",
        }
    )

    client = create_client(url, key, options)

    assert client.options.headers.get("x-app-name") == "apple"
    assert client.options.headers.get("x-version") == "1.0"


def test_custom_headers_immutable():
    url = os.environ.get("SUPABASE_TEST_URL")
    key = os.environ.get("SUPABASE_TEST_KEY")

    options = ClientOptions(
        headers={
            "x-app-name": "apple",
            "x-version": "1.0",
        }
    )

    client1 = create_client(url, key, options)
    client2 = create_client(url, key, options)

    client1.options.headers["x-app-name"] = "grapes"

    assert client1.options.headers.get("x-app-name") == "grapes"
    assert client1.options.headers.get("x-version") == "1.0"
    assert client2.options.headers.get("x-app-name") == "apple"


def test_httpx_client_base_url_isolation():
    """Test that shared httpx_client doesn't cause base_url mutation between services.
    This test reproduces the issue where accessing PostgREST after Storage causes
    Storage requests to hit the wrong endpoint (404 errors).
    See: https://github.com/supabase/supabase-py/issues/1244
    """
    url = os.environ.get("SUPABASE_TEST_URL")
    key = os.environ.get("SUPABASE_TEST_KEY")

    # Create client with shared httpx instance
    timeout = Timeout(10.0, read=60.0)
    httpx_client = SyncHttpxClient(timeout=timeout)
    options = ClientOptions(httpx_client=httpx_client)
    client = create_client(url, key, options)

    # Access storage and capture its base_url
    storage = client.storage
    storage_base_url = str(storage._base_url).rstrip("/")
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
    storage_base_url_after = str(storage._base_url).rstrip("/")
    assert storage_base_url_after.endswith("/storage/v1"), (
        f"Storage base_url was mutated! Expected '/storage/v1', got {storage_base_url_after}"
    )

    assert str(storage._base_url).rstrip("/").endswith("/storage/v1"), (
        "Storage base_url was mutated after accessing functions"
    )
    assert str(postgrest.base_url).rstrip("/").endswith("/rest/v1"), (
        "PostgREST base_url was mutated after accessing functions"
    )
