from __future__ import annotations

import os
from typing import Any
from unittest.mock import MagicMock

import pytest
from gotrue import SyncMemoryStorage

from supabase import Client, ClientOptions, SupabaseException, create_client


@pytest.mark.xfail(
    reason="None of these values should be able to instantiate a client object"
)
@pytest.mark.parametrize("url", ["", None, "valeefgpoqwjgpj", 139, -1, {}, []])
@pytest.mark.parametrize("key", ["", None, "valeefgpoqwjgpj", 139, -1, {}, []])
def test_incorrect_values_dont_instantiate_client(url: Any, key: Any) -> None:
    """Ensure we can't instantiate client with invalid values."""
    try:
        _: Client = create_client(url, key)
    except SupabaseException as e:
        pass


def test_function_initialization() -> None:
    url = os.environ.get("SUPABASE_TEST_URL")
    key = os.environ.get("SUPABASE_TEST_KEY")

    client = create_client(url, key)
    assert client.functions


def test_postgrest_schema() -> None:
    url = os.environ.get("SUPABASE_TEST_URL")
    key = os.environ.get("SUPABASE_TEST_KEY")

    client = create_client(url, key)
    assert client.postgrest
    assert client.postgrest.schema("new_schema")


def test_rpc_client() -> None:
    url = os.environ.get("SUPABASE_TEST_URL")
    key = os.environ.get("SUPABASE_TEST_KEY")

    client = create_client(url, key)
    assert client.rpc("test_fn")


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


def test_updates_the_authorization_header_on_auth_events() -> None:
    url = os.environ.get("SUPABASE_TEST_URL")
    key = os.environ.get("SUPABASE_TEST_KEY")

    client = create_client(url, key)

    assert client.options.headers.get("apiKey") == key
    assert client.options.headers.get("Authorization") == f"Bearer {key}"

    mock_session = MagicMock(access_token="secretuserjwt")
    realtime_mock = MagicMock()
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
