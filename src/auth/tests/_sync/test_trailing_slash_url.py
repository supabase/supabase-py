from urllib.parse import urlsplit

from httpx import Client
from supabase_utils.http.adapters.httpx import HttpxSession

from supabase_auth import SyncSupabaseAuthClient


def test_oauth_url_normalizes_trailing_slash() -> None:
    client = SyncSupabaseAuthClient(
        url="https://project.example/auth/v1/",
        http_session=HttpxSession(client=Client()),
        auto_refresh_token=False,
    )

    response = client.sign_in_with_oauth("github")

    assert urlsplit(response.url).path == "/auth/v1/authorize"
