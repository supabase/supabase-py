import pytest
from httpx import AsyncClient, MockTransport, Request, Response
from supabase_utils.http.adapters.httpx import AsyncHttpxSession
from supabase_utils.types import JSON

from supabase_auth import AsyncSupabaseAuthClient
from supabase_auth.errors import AuthImplicitGrantRedirectError
from supabase_auth.types import AuthChangeEvent, AuthStateChange

USER: dict[str, JSON] = {
    "id": "11111111-1111-1111-1111-111111111111",
    "aud": "authenticated",
    "app_metadata": {},
    "user_metadata": {},
    "created_at": "2026-01-01T00:00:00Z",
    "email": "user@example.com",
}

TOKENS = "access_token=a&expires_in=3600&refresh_token=r&token_type=bearer"


def mock_client(authorizations: list[str]) -> AsyncSupabaseAuthClient:
    def handler(request: Request) -> Response:
        assert request.url.path.endswith("/user")
        authorizations.append(request.headers.get("Authorization", ""))
        return Response(200, json=USER)

    return AsyncSupabaseAuthClient(
        url="https://example.supabase.co/auth/v1",
        http_session=AsyncHttpxSession(
            client=AsyncClient(transport=MockTransport(handler))
        ),
        auto_refresh_token=False,
    )


def events(changes: list[AuthStateChange]) -> list[AuthChangeEvent]:
    return [change.event for change in changes]


async def test_initialize_reads_tokens_from_fragment() -> None:
    authorizations: list[str] = []
    client = mock_client(authorizations)
    changes: list[AuthStateChange] = []
    client.on_auth_state_change(changes.append)

    await client.initialize(url=f"https://app.example/callback#{TOKENS}")

    session = await client.get_session()
    assert session is not None
    assert session.access_token == "a"
    assert session.refresh_token == "r"
    assert authorizations == ["Bearer a"]
    assert events(changes) == [
        AuthChangeEvent.INITIAL_SESSION,
        AuthChangeEvent.SIGNED_IN,
    ]


async def test_initialize_from_url_reads_recovery_type_from_fragment() -> None:
    client = mock_client([])
    changes: list[AuthStateChange] = []
    client.on_auth_state_change(changes.append)

    await client.initialize_from_url(
        f"https://app.example/callback#{TOKENS}&type=recovery"
    )

    assert events(changes) == [
        AuthChangeEvent.INITIAL_SESSION,
        AuthChangeEvent.SIGNED_IN,
        AuthChangeEvent.PASSWORD_RECOVERY,
    ]


async def test_initialize_from_url_raises_fragment_error_redirect() -> None:
    authorizations: list[str] = []
    client = mock_client(authorizations)

    with pytest.raises(AuthImplicitGrantRedirectError) as error:
        await client.initialize_from_url(
            "https://app.example/callback"
            "#error=access_denied&error_code=otp_expired"
            "&error_description=Email+link+is+invalid+or+has+expired"
        )

    assert error.value.message == "Email link is invalid or has expired"
    assert error.value.detail_code == "otp_expired"
    assert error.value.detail_error == "access_denied"
    assert authorizations == []
    assert await client.get_session() is None


async def test_initialize_from_url_prefers_query_over_fragment() -> None:
    authorizations: list[str] = []
    client = mock_client(authorizations)

    await client.initialize_from_url(
        "https://app.example/callback?access_token=from-query"
        f"#{TOKENS.replace('access_token=a', 'access_token=from-fragment')}"
    )

    session = await client.get_session()
    assert session is not None
    assert session.access_token == "from-query"
    assert session.refresh_token == "r"
    assert authorizations == ["Bearer from-query"]


async def test_initialize_reads_tokens_from_query() -> None:
    client = mock_client([])
    changes: list[AuthStateChange] = []
    client.on_auth_state_change(changes.append)

    await client.initialize(url=f"https://app.example/callback?{TOKENS}")

    session = await client.get_session()
    assert session is not None
    assert session.access_token == "a"
    assert events(changes) == [
        AuthChangeEvent.INITIAL_SESSION,
        AuthChangeEvent.SIGNED_IN,
    ]


async def test_initialize_does_not_treat_pkce_callback_as_implicit_grant() -> None:
    authorizations: list[str] = []
    client = mock_client(authorizations)
    changes: list[AuthStateChange] = []
    client.on_auth_state_change(changes.append)

    await client.initialize(url="https://app.example/callback?code=abc")

    assert authorizations == []
    assert events(changes) == [AuthChangeEvent.INITIAL_SESSION]
    assert await client.get_session() is None
