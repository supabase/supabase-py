from typing import Dict

import pytest
from httpx import AsyncClient, Client, Timeout
from storage3 import AsyncStorageClient, SyncStorageClient
from storage3.constants import DEFAULT_TIMEOUT


@pytest.fixture
def valid_url() -> str:
    return "https://example.com/storage/v1/"


@pytest.fixture
def url_without_trailing_slash() -> str:
    return "https://example.com/storage/v1"


@pytest.fixture
def valid_headers() -> Dict[str, str]:
    return {"Authorization": "Bearer test_token", "apikey": "test_api_key"}


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


def test_create_async_client_warns_without_trailing_slash(
    url_without_trailing_slash, valid_headers
) -> None:
    with pytest.warns(
        UserWarning, match="Storage endpoint URL should have a trailing slash"
    ):
        client = AsyncStorageClient(
            url=url_without_trailing_slash, headers=valid_headers
        )

    assert str(client._base_url) == "https://example.com/storage/v1/"


def test_create_sync_client_warns_without_trailing_slash(
    url_without_trailing_slash, valid_headers
) -> None:
    with pytest.warns(
        UserWarning, match="Storage endpoint URL should have a trailing slash"
    ):
        client = SyncStorageClient(url=url_without_trailing_slash, headers=valid_headers)

    assert str(client._base_url) == "https://example.com/storage/v1/"


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
