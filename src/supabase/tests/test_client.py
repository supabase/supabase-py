import pytest
from httpx import AsyncClient as AsyncHttpxClient
from httpx import Client as SyncHttpxClient
from supabase_utils.http.adapters.httpx import AsyncHttpxSession, HttpxSession

from supabase import AsyncClient, Client, SupabaseException

URL = "https://example.supabase.co"
KEY = "publishable-key"

INVALID_URLS = [
    "",
    "example.supabase.co",
    "ftp://example.supabase.co",
    "https://",
    "http://[::1",
    "https://example.supabase.co:99999",
]


@pytest.mark.parametrize("url", INVALID_URLS)
def test_sync_client_rejects_invalid_urls(url: str) -> None:
    with SyncHttpxClient() as http_client, pytest.raises(SupabaseException):
        Client(url, KEY, HttpxSession(client=http_client))


@pytest.mark.parametrize("url", INVALID_URLS)
async def test_async_client_rejects_invalid_urls(url: str) -> None:
    async with AsyncHttpxClient() as http_client:
        with pytest.raises(SupabaseException):
            AsyncClient(url, KEY, AsyncHttpxSession(client=http_client))


def test_sync_client_requires_a_key() -> None:
    with SyncHttpxClient() as http_client, pytest.raises(SupabaseException):
        Client(URL, "", HttpxSession(client=http_client))


async def test_async_client_requires_a_key() -> None:
    async with AsyncHttpxClient() as http_client:
        with pytest.raises(SupabaseException):
            AsyncClient(URL, "", AsyncHttpxSession(client=http_client))
