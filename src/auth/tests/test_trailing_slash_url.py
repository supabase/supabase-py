from urllib.parse import urlsplit

import pytest
from supabase_auth import AsyncGoTrueClient, SyncGoTrueClient


def test_sync_oauth_url_normalizes_trailing_slash() -> None:
    client = SyncGoTrueClient(
        url="https://project.example/auth/v1/", auto_refresh_token=False
    )

    response = client.sign_in_with_oauth({"provider": "github"})

    assert urlsplit(response.url).path == "/auth/v1/authorize"


@pytest.mark.asyncio
async def test_async_oauth_url_normalizes_trailing_slash() -> None:
    client = AsyncGoTrueClient(
        url="https://project.example/auth/v1/", auto_refresh_token=False
    )

    response = await client.sign_in_with_oauth({"provider": "github"})

    assert urlsplit(response.url).path == "/auth/v1/authorize"
