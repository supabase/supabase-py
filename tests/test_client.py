from __future__ import annotations

import os
from typing import Any
from unittest.mock import MagicMock

import pytest

from supabase import Client, create_client
from supabase.lib.client_options import ClientOptions


@pytest.mark.xfail(
    reason="None of these values should be able to instantiate a client object"
)
@pytest.mark.parametrize("url", ["", None, "valeefgpoqwjgpj", 139, -1, {}, []])
@pytest.mark.parametrize("key", ["", None, "valeefgpoqwjgpj", 139, -1, {}, []])
def test_incorrect_values_dont_instantiate_client(url: Any, key: Any) -> None:
    """Ensure we can't instantiate client with invalid values."""
    _: Client = create_client(url, key)


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

    authorization = f"Bearer secretuserjwt"

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
