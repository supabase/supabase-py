import os
from unittest.mock import MagicMock

from supabase_auth import SyncMemoryStorage

from supabase import (
    ClientOptions,
)

from .conftest import SyncClientCallable

url = os.environ["SUPABASE_TEST_URL"]
key = os.environ["SUPABASE_TEST_KEY"]


def test_postgrest_client(create_client: SyncClientCallable) -> None:
    with create_client(url, key) as client:
        assert client.table("sample")
        assert client.postgrest.schema("new_schema")


def test_rpc_client(create_client: SyncClientCallable) -> None:
    with create_client(url, key) as client:
        assert client.rpc("test_fn")


def test_function_initialization(create_client: SyncClientCallable) -> None:
    with create_client(url, key) as client:
        assert client.functions


def test_uses_key_as_authorization_header_by_default(
    create_client: SyncClientCallable,
) -> None:
    with create_client(url, key) as client:
        assert client.options.headers.get("apiKey") == key
        assert client.options.headers.get("Authorization") == f"Bearer {key}"

        assert client.postgrest.default_headers.get("apiKey") == key
        assert client.postgrest.default_headers.get("Authorization") == f"Bearer {key}"

        assert client.auth.default_headers.get("apiKey") == key
        assert client.auth.default_headers.get("Authorization") == f"Bearer {key}"

        assert client.storage.default_headers.get("apiKey") == key
        assert client.storage.default_headers.get("Authorization") == f"Bearer {key}"


def test_schema_update(create_client: SyncClientCallable) -> None:
    with create_client(url, key) as client:
        assert client.postgrest
        assert client.schema("new_schema")


def test_updates_the_authorization_header_on_auth_events(
    create_client: SyncClientCallable,
) -> None:
    with create_client(url, key) as client:
        assert client.options.headers.get("apiKey") == key
        assert client.options.headers.get("Authorization") == f"Bearer {key}"

        mock_session = MagicMock(access_token="secretuserjwt")

        client._listen_to_auth_events("SIGNED_IN", mock_session)

        updated_authorization = f"Bearer {mock_session.access_token}"

        assert client.options.headers.get("apiKey") == key
        assert client.options.headers.get("Authorization") == updated_authorization

        assert client.postgrest.default_headers.get("apiKey") == key
        assert (
            client.postgrest.default_headers.get("Authorization")
            == updated_authorization
        )

        assert client.auth.default_headers.get("apiKey") == key
        assert client.auth.default_headers.get("Authorization") == updated_authorization

        assert client.storage.default_headers.get("apiKey") == key
        assert (
            client.storage.default_headers.get("Authorization") == updated_authorization
        )


def test_supports_setting_a_global_authorization_header(
    create_client: SyncClientCallable,
) -> None:
    authorization = "Bearer secretuserjwt"

    options = ClientOptions(headers={"Authorization": authorization})

    with create_client(url, key, options) as client:
        assert client.options.headers.get("apiKey") == key
        assert client.options.headers.get("Authorization") == authorization

        assert client.postgrest.default_headers.get("apiKey") == key
        assert client.postgrest.default_headers.get("Authorization") == authorization

        assert client.auth.default_headers.get("apiKey") == key
        assert client.auth.default_headers.get("Authorization") == authorization

        assert client.storage.default_headers.get("apiKey") == key
        assert client.storage.default_headers.get("Authorization") == authorization


def test_mutable_headers_issue(create_client: SyncClientCallable) -> None:
    shared_options = ClientOptions(
        storage=SyncMemoryStorage(), headers={"Authorization": "Bearer initial-token"}
    )

    with (
        create_client(url, key, shared_options) as client1,
        create_client(url, key, shared_options) as client2,
    ):
        client1.options.headers["Authorization"] = "Bearer modified-token"
        assert client2.options.headers["Authorization"] == "Bearer initial-token"
        assert client1.options.headers["Authorization"] == "Bearer modified-token"


def test_global_authorization_header_issue(create_client: SyncClientCallable) -> None:
    authorization = "Bearer secretuserjwt"
    options = ClientOptions(headers={"Authorization": authorization})

    with create_client(url, key, options) as client:
        assert client.options.headers.get("apiKey") == key


def test_custom_headers(create_client: SyncClientCallable) -> None:
    options = ClientOptions(
        headers={
            "x-app-name": "apple",
            "x-version": "1.0",
        }
    )

    with create_client(url, key, options) as client:
        assert client.options.headers.get("x-app-name") == "apple"
        assert client.options.headers.get("x-version") == "1.0"


def test_custom_headers_immutable(create_client: SyncClientCallable) -> None:
    options = ClientOptions(
        headers={
            "x-app-name": "apple",
            "x-version": "1.0",
        }
    )

    with (
        create_client(url, key, options) as client1,
        create_client(url, key, options) as client2,
    ):
        client1.options.headers["x-app-name"] = "grapes"

        assert client1.options.headers.get("x-app-name") == "grapes"
        assert client1.options.headers.get("x-version") == "1.0"
        assert client2.options.headers.get("x-app-name") == "apple"


def test_httpx_client_base_url_isolation(create_client: SyncClientCallable) -> None:
    """Test that shared httpx_client doesn't cause base_url mutation between services.
    This test reproduces the issue where accessing PostgREST after Storage causes
    Storage requests to hit the wrong endpoint (404 errors).
    See: https://github.com/supabase/supabase-py/issues/1244
    """
    # Create client with shared httpx instance
    options = ClientOptions()
    with create_client(url, key, options) as client:
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
