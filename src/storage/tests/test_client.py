import re
from typing import Dict

import pytest
from httpx import AsyncClient, Client, Timeout
from storage3 import AsyncStorageClient, SyncStorageClient
from storage3.constants import DEFAULT_TIMEOUT


@pytest.fixture
def valid_url() -> str:
    return "https://example.com/storage/v1"


@pytest.fixture
def valid_headers() -> Dict[str, str]:
    return {"Authorization": "Bearer test_token", "apikey": "test_api_key"}


_X_CLIENT_INFO_PATTERN = re.compile(
    r"^supabase-py/storage3 v[\d.]+; platform=.+; platform-version=.+; runtime=python; runtime-version=[\d.]+$"
)


def test_async_x_client_info_structured_format(valid_url, valid_headers) -> None:
    client = AsyncStorageClient(url=valid_url, headers=valid_headers)
    x_client_info = client._client.headers.get("X-Client-Info")
    assert x_client_info is not None
    assert _X_CLIENT_INFO_PATTERN.match(
        x_client_info
    ), f"X-Client-Info format is wrong: {x_client_info}"


def test_sync_x_client_info_structured_format(valid_url, valid_headers) -> None:
    client = SyncStorageClient(url=valid_url, headers=valid_headers)
    x_client_info = client._client.headers.get("X-Client-Info")
    assert x_client_info is not None
    assert _X_CLIENT_INFO_PATTERN.match(
        x_client_info
    ), f"X-Client-Info format is wrong: {x_client_info}"


def test_create_async_client(valid_url, valid_headers) -> None:
    client = AsyncStorageClient(url=valid_url, headers=valid_headers)

    assert isinstance(client, AsyncStorageClient)
    assert all(
        client._client.headers[key] == value for key, value in valid_headers.items()
    )
    assert client._client.timeout == Timeout(DEFAULT_TIMEOUT)


def test_create_sync_client(valid_url, valid_headers) -> None:
    client = SyncStorageClient(url=valid_url, headers=valid_headers)

    assert isinstance(client, SyncStorageClient)
    assert all(
        client._client.headers[key] == value for key, value in valid_headers.items()
    )
    assert client._client.timeout == Timeout(DEFAULT_TIMEOUT)


def test_async_storage_client(valid_url, valid_headers) -> None:
    headers = {"x-user-agent": "my-app/0.0.1"}
    http_client = AsyncClient(headers=headers)
    client = AsyncStorageClient(
        url=valid_url, headers=valid_headers, http_client=http_client
    )

    assert isinstance(client, AsyncStorageClient)
    assert all(client._headers[key] == value for key, value in valid_headers.items())
    assert client._client.headers.get("x-user-agent") == "my-app/0.0.1"
    assert client._client.timeout == Timeout(5.0)


def test_sync_storage_client(valid_url, valid_headers) -> None:
    headers = {"x-user-agent": "my-app/0.0.1"}
    http_client = Client(headers=headers)
    client = SyncStorageClient(
        url=valid_url, headers=valid_headers, http_client=http_client
    )

    assert isinstance(client, SyncStorageClient)
    assert all(client._headers[key] == value for key, value in valid_headers.items())
    assert client._client.headers.get("x-user-agent") == "my-app/0.0.1"
    assert client._client.timeout == Timeout(5.0)


def test_async_storage_client_with_httpx(valid_url, valid_headers) -> None:
    client = AsyncStorageClient(url=valid_url, headers=valid_headers)

    assert isinstance(client, AsyncStorageClient)
    assert all(
        client._client.headers[key] == value for key, value in valid_headers.items()
    )
    assert client._client.timeout == Timeout(DEFAULT_TIMEOUT)


def test_sync_storage_client_with_httpx(valid_url, valid_headers) -> None:
    client = SyncStorageClient(url=valid_url, headers=valid_headers)

    assert isinstance(client, SyncStorageClient)
    assert all(
        client._client.headers[key] == value for key, value in valid_headers.items()
    )
    assert client._client.timeout == Timeout(DEFAULT_TIMEOUT)


def test_custom_timeout(valid_url, valid_headers) -> None:
    custom_timeout = 30

    async_client = AsyncStorageClient(
        url=valid_url, headers=valid_headers, timeout=custom_timeout
    )
    assert async_client._client.timeout == Timeout(custom_timeout)

    sync_client = SyncStorageClient(
        url=valid_url, headers=valid_headers, timeout=custom_timeout
    )
    assert sync_client._client.timeout == Timeout(custom_timeout)
