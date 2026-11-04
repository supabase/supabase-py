from supabase_utils.http.adapters.httpx import AsyncHttpxSession, HttpxSession

from supabase.httpx import create_aclient, create_client

URL = "https://example.supabase.co"
KEY = "publishable-key"


def test_create_client_follows_redirects() -> None:
    with create_client(URL, KEY) as client:
        assert isinstance(client.http_session, HttpxSession)
        assert client.http_session.client.follow_redirects


async def test_create_aclient_follows_redirects() -> None:
    async with create_aclient(URL, KEY) as client:
        assert isinstance(client.http_session, AsyncHttpxSession)
        assert client.http_session.client.follow_redirects
