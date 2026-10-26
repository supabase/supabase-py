from urllib.parse import urlsplit

from httpx import AsyncClient
from supabase_utils.http.adapters.httpx import AsyncHttpxSession

from supabase_auth import AsyncSupabaseAuthClient


async def test_oauth_url_normalizes_trailing_slash() -> None:
    client = AsyncSupabaseAuthClient(
        url="https://project.example/auth/v1/",
        http_session=AsyncHttpxSession(client=AsyncClient()),
        auto_refresh_token=False,
    )

    response = await client.sign_in_with_oauth("github")

    assert urlsplit(response.url).path == "/auth/v1/authorize"
