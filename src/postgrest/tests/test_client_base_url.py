import pytest
from httpx import AsyncClient, Client
from supabase_utils.http.adapters.httpx import AsyncHttpxSession, HttpxSession

from postgrest import AsyncPostgrestClient, SyncPostgrestClient


@pytest.mark.parametrize(
    "url", ["ftp://example.com", "file:///tmp/db", "example.com", "", "http://"]
)
def test_sync_client_rejects_a_non_http_base_url(url: str) -> None:
    with (
        Client() as http,
        pytest.raises(ValueError, match="base_url must be a valid HTTP URL"),
    ):
        SyncPostgrestClient(url, http_session=HttpxSession(client=http))


@pytest.mark.parametrize(
    "url", ["ftp://example.com", "file:///tmp/db", "example.com", "", "http://"]
)
async def test_async_client_rejects_a_non_http_base_url(url: str) -> None:
    async with AsyncClient() as http:
        with pytest.raises(ValueError, match="base_url must be a valid HTTP URL"):
            AsyncPostgrestClient(url, http_session=AsyncHttpxSession(client=http))


@pytest.mark.parametrize("url", ["http://example.com", "https://example.com/rest/v1"])
def test_client_accepts_an_http_base_url(url: str) -> None:
    with Client() as http:
        client = SyncPostgrestClient(url, http_session=HttpxSession(client=http))

    assert str(client.base_url) == url
