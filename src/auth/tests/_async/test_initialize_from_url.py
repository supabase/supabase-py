import httpx
import pytest
from supabase_auth import AsyncGoTrueClient
from supabase_auth.errors import AuthImplicitGrantRedirectError

_USER = {
    "id": "11111111-1111-1111-1111-111111111111",
    "aud": "authenticated",
    "app_metadata": {},
    "user_metadata": {},
    "created_at": "2026-01-01T00:00:00Z",
    "email": "user@example.com",
}

_TOKENS = "access_token=a&expires_in=3600&refresh_token=r&token_type=bearer"


def _client(authorizations: list[str]) -> AsyncGoTrueClient:
    def handler(request: httpx.Request) -> httpx.Response:
        authorizations.append(request.headers.get("Authorization", ""))
        return httpx.Response(200, json=_USER)

    return AsyncGoTrueClient(
        url="http://localhost",
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        auto_refresh_token=False,
    )


async def test_initialize_reads_tokens_from_fragment() -> None:
    authorizations: list[str] = []
    client = _client(authorizations)
    events: list[str] = []
    client.on_auth_state_change(lambda event, session: events.append(event))

    await client.initialize(url=f"https://app.example/callback#{_TOKENS}")

    session = await client.get_session()
    assert session is not None
    assert session.access_token == "a"
    assert session.refresh_token == "r"
    assert authorizations == ["Bearer a"]
    assert events == ["SIGNED_IN"]


async def test_initialize_from_url_reads_recovery_type_from_fragment() -> None:
    client = _client([])
    events: list[str] = []
    client.on_auth_state_change(lambda event, session: events.append(event))

    await client.initialize_from_url(
        f"https://app.example/callback#{_TOKENS}&type=recovery"
    )

    assert events == ["SIGNED_IN", "PASSWORD_RECOVERY"]


async def test_initialize_from_url_raises_fragment_error_redirect() -> None:
    authorizations: list[str] = []
    client = _client(authorizations)

    with pytest.raises(AuthImplicitGrantRedirectError) as error:
        await client.initialize_from_url(
            "https://app.example/callback"
            "#error=access_denied&error_code=otp_expired"
            "&error_description=Email+link+is+invalid+or+has+expired"
        )

    assert error.value.message == "Email link is invalid or has expired"
    assert error.value.details == {"code": "otp_expired", "error": "access_denied"}
    assert authorizations == []
    assert await client.get_session() is None


async def test_initialize_from_url_prefers_query_over_fragment() -> None:
    authorizations: list[str] = []
    client = _client(authorizations)

    await client.initialize_from_url(
        "https://app.example/callback?access_token=from-query"
        f"#{_TOKENS.replace('access_token=a', 'access_token=from-fragment')}"
    )

    session = await client.get_session()
    assert session is not None
    assert session.access_token == "from-query"
    assert authorizations == ["Bearer from-query"]


async def test_initialize_reads_tokens_from_query() -> None:
    client = _client([])
    events: list[str] = []
    client.on_auth_state_change(lambda event, session: events.append(event))

    await client.initialize(url=f"https://app.example/callback?{_TOKENS}")

    session = await client.get_session()
    assert session is not None
    assert session.access_token == "a"
    assert events == ["SIGNED_IN"]


async def test_initialize_does_not_treat_pkce_callback_as_implicit_grant() -> None:
    authorizations: list[str] = []
    client = _client(authorizations)
    events: list[str] = []
    client.on_auth_state_change(lambda event, session: events.append(event))

    await client.initialize(url="https://app.example/callback?code=abc")

    assert authorizations == []
    assert events == []
    assert await client.get_session() is None
