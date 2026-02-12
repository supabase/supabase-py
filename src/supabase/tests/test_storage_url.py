import pytest

from supabase import create_client
from supabase._async.client import AsyncClient
from supabase._sync.client import Client as SyncClient


def test_storage_url_has_trailing_slash_sync() -> None:
    """Verify that storage_url always ends with a trailing slash (sync)."""
    url = "https://example.com"
    key = "somekey"
    client = create_client(url, key)
    assert str(client.storage_url).endswith("/"), "storage_url must end with a trailing slash"

    # Also verify direct instantiation
    client2 = SyncClient(url, key)
    assert str(client2.storage_url).endswith(
        "/"
    ), "Client.storage_url must end with a trailing slash"


@pytest.mark.asyncio
async def test_storage_url_has_trailing_slash_async() -> None:
    """Verify that storage_url always ends with a trailing slash (async)."""
    url = "https://example.com"
    key = "somekey"
    client = await AsyncClient.create(url, key)
    assert str(client.storage_url).endswith(
        "/"
    ), "AsyncClient.storage_url must end with a trailing slash"

    client2 = AsyncClient(url, key)
    assert str(client2.storage_url).endswith(
        "/"
    ), "AsyncClient(direct) storage_url must end with a trailing slash"


def test_storage_url_without_trailing_slash_in_base_sync() -> None:
    """Verify handling when base URL doesn't have slash (sync)."""
    url = "https://example.com"
    key = "somekey"
    client = SyncClient(url, key)
    assert str(client.storage_url) == "https://example.com/storage/v1/"


@pytest.mark.asyncio
async def test_storage_url_without_trailing_slash_in_base_async() -> None:
    """Verify handling when base URL doesn't have slash (async)."""
    url = "https://example.com"
    key = "somekey"
    client = await AsyncClient.create(url, key)
    assert str(client.storage_url) == "https://example.com/storage/v1/"
