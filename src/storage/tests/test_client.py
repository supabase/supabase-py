from typing import Dict

import pytest

from storage3 import AsyncStorageClient, SyncStorageClient


@pytest.fixture
def valid_url() -> str:
    return "https://supabase.com/storage/v1"


@pytest.fixture
def valid_headers() -> Dict[str, str]:
    return {"Authorization": "Bearer test_token", "apikey": "test_api_key"}


def test_create_async_client(valid_url: str, valid_headers: Dict[str, str]) -> None:
    client = AsyncStorageClient(url=valid_url, headers=valid_headers)

    assert isinstance(client, AsyncStorageClient)
    assert all(
        client.default_headers[key] == value for key, value in valid_headers.items()
    )


def test_create_sync_client(valid_url: str, valid_headers: Dict[str, str]) -> None:
    client = SyncStorageClient(url=valid_url, headers=valid_headers)

    assert isinstance(client, SyncStorageClient)
    assert all(
        client.default_headers[key] == value for key, value in valid_headers.items()
    )
