from urllib.parse import parse_qs, urlparse

import pytest
from supabase_auth import AsyncGoTrueClient
from supabase_auth.errors import AuthSessionMissingError


async def test_sign_in_with_oauth_preserves_query_params() -> None:
    query_params = {"prompt": "consent"}
    async with AsyncGoTrueClient(url="https://example.com") as client:
        response = await client.sign_in_with_oauth(
            {
                "provider": "github",
                "options": {
                    "query_params": query_params,
                    "redirect_to": "https://example.com/callback",
                    "scopes": "read:user",
                },
            }
        )

    assert query_params == {"prompt": "consent"}
    assert parse_qs(urlparse(response.url).query) == {
        "prompt": ["consent"],
        "redirect_to": ["https://example.com/callback"],
        "scopes": ["read:user"],
        "provider": ["github"],
    }


async def test_link_identity_preserves_query_params() -> None:
    query_params = {"prompt": "consent"}
    async with AsyncGoTrueClient(url="https://example.com") as client:
        with pytest.raises(AuthSessionMissingError):
            await client.link_identity(
                {
                    "provider": "github",
                    "options": {
                        "query_params": query_params,
                        "redirect_to": "https://example.com/callback",
                        "scopes": "read:user",
                    },
                }
            )

    assert query_params == {"prompt": "consent"}
