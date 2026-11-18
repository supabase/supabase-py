import json

import pytest
from httpx import Client, MockTransport, Request, Response
from supabase_utils.http.adapters.httpx import HttpxSession
from supabase_utils.types import JSON

from supabase_auth import SyncSupabaseAuthClient
from supabase_auth.errors import (
    AuthImplicitGrantRedirectError,
    AuthPKCECodeVerifierMissingError,
)
from supabase_auth.types import (
    AuthChangeEvent,
    AuthFlowType,
    AuthStateChange,
)

USER: dict[str, JSON] = {
    "id": "11111111-1111-1111-1111-111111111111",
    "aud": "authenticated",
    "app_metadata": {},
    "user_metadata": {},
    "created_at": "2026-01-01T00:00:00Z",
    "email": "user@example.com",
}

TOKENS = "access_token=a&expires_in=3600&refresh_token=r&token_type=bearer"

SESSION: dict[str, JSON] = {
    "access_token": "exchanged",
    "refresh_token": "r",
    "expires_in": 3600,
    "token_type": "bearer",
    "user": USER,
}


def mock_client(
    authorizations: list[str],
    token_requests: list[Request] | None = None,
    flow_type: AuthFlowType = "implicit",
) -> SyncSupabaseAuthClient:
    def handler(request: Request) -> Response:
        if request.url.path.endswith("/token"):
            assert token_requests is not None
            token_requests.append(request)
            return Response(200, json=SESSION)
        assert request.url.path.endswith("/user")
        authorizations.append(request.headers.get("Authorization", ""))
        return Response(200, json=USER)

    return SyncSupabaseAuthClient(
        url="https://example.supabase.co/auth/v1",
        http_session=HttpxSession(client=Client(transport=MockTransport(handler))),
        auto_refresh_token=False,
        flow_type=flow_type,
    )


def start_oauth_flow(client: SyncSupabaseAuthClient) -> str:
    response = client.sign_in_with_oauth("github")
    assert response.flow_id is not None
    return response.flow_id


def events(changes: list[AuthStateChange]) -> list[AuthChangeEvent]:
    return [change.event for change in changes]


def test_initialize_reads_tokens_from_fragment() -> None:
    authorizations: list[str] = []
    client = mock_client(authorizations)
    changes: list[AuthStateChange] = []
    client.on_auth_state_change(changes.append)

    client.initialize(url=f"https://app.example/callback#{TOKENS}")

    session = client.get_session()
    assert session is not None
    assert session.access_token == "a"
    assert session.refresh_token == "r"
    assert authorizations == ["Bearer a"]
    assert events(changes) == [
        AuthChangeEvent.INITIAL_SESSION,
        AuthChangeEvent.SIGNED_IN,
    ]


def test_initialize_from_url_reads_recovery_type_from_fragment() -> None:
    client = mock_client([])
    changes: list[AuthStateChange] = []
    client.on_auth_state_change(changes.append)

    client.initialize_from_url(f"https://app.example/callback#{TOKENS}&type=recovery")

    assert events(changes) == [
        AuthChangeEvent.INITIAL_SESSION,
        AuthChangeEvent.SIGNED_IN,
        AuthChangeEvent.PASSWORD_RECOVERY,
    ]


def test_initialize_from_url_raises_fragment_error_redirect() -> None:
    authorizations: list[str] = []
    client = mock_client(authorizations)

    with pytest.raises(AuthImplicitGrantRedirectError) as error:
        client.initialize_from_url(
            "https://app.example/callback"
            "#error=access_denied&error_code=otp_expired"
            "&error_description=Email+link+is+invalid+or+has+expired"
        )

    assert error.value.message == "Email link is invalid or has expired"
    assert error.value.detail_code == "otp_expired"
    assert error.value.detail_error == "access_denied"
    assert authorizations == []
    assert client.get_session() is None


def test_initialize_from_url_prefers_query_over_fragment() -> None:
    authorizations: list[str] = []
    client = mock_client(authorizations)

    client.initialize_from_url(
        "https://app.example/callback?access_token=from-query"
        f"#{TOKENS.replace('access_token=a', 'access_token=from-fragment')}"
    )

    session = client.get_session()
    assert session is not None
    assert session.access_token == "from-query"
    assert session.refresh_token == "r"
    assert authorizations == ["Bearer from-query"]


def test_initialize_reads_tokens_from_query() -> None:
    client = mock_client([])
    changes: list[AuthStateChange] = []
    client.on_auth_state_change(changes.append)

    client.initialize(url=f"https://app.example/callback?{TOKENS}")

    session = client.get_session()
    assert session is not None
    assert session.access_token == "a"
    assert events(changes) == [
        AuthChangeEvent.INITIAL_SESSION,
        AuthChangeEvent.SIGNED_IN,
    ]


def test_initialize_does_not_treat_pkce_callback_as_implicit_grant() -> None:
    authorizations: list[str] = []
    client = mock_client(authorizations)
    changes: list[AuthStateChange] = []
    client.on_auth_state_change(changes.append)

    client.initialize(url="https://app.example/callback?code=abc")

    assert authorizations == []
    assert events(changes) == [AuthChangeEvent.INITIAL_SESSION]
    assert client.get_session() is None


@pytest.mark.parametrize(
    ("query", "message", "error", "code"),
    [
        ("error=access_denied", "access_denied", "access_denied", None),
        ("error_code=otp_expired", "otp_expired", None, "otp_expired"),
        (
            "error=server_error&error_description=Unable+to+exchange+code",
            "Unable to exchange code",
            "server_error",
            None,
        ),
    ],
)
def test_initialize_raises_incomplete_error_redirect(
    query: str, message: str, error: str | None, code: str | None
) -> None:
    client = mock_client([])

    with pytest.raises(AuthImplicitGrantRedirectError) as raised:
        client.initialize(url=f"https://app.example/callback?{query}")

    assert raised.value.message == message
    assert raised.value.detail_error == error
    assert raised.value.detail_code == code
    assert client.get_session() is None


def test_initialize_exchanges_pkce_code_of_flow() -> None:
    token_requests: list[Request] = []
    client = mock_client([], token_requests, flow_type="pkce")
    changes: list[AuthStateChange] = []
    client.on_auth_state_change(changes.append)
    flow_id = start_oauth_flow(client)
    start_oauth_flow(client)

    client.initialize(url=f"https://app.example/callback?code=abc&sb_flow_id={flow_id}")

    session = client.get_session()
    assert session is not None
    assert session.access_token == "exchanged"
    assert len(token_requests) == 1
    assert token_requests[0].url.params["grant_type"] == "pkce"
    assert json.loads(token_requests[0].content)["auth_code"] == "abc"
    assert events(changes) == [
        AuthChangeEvent.INITIAL_SESSION,
        AuthChangeEvent.SIGNED_IN,
    ]
    with pytest.raises(AuthPKCECodeVerifierMissingError):
        client.exchange_code_for_session("abc", flow_id=flow_id)


def test_initialize_from_url_raises_without_pkce_code_verifier() -> None:
    token_requests: list[Request] = []
    client = mock_client([], token_requests, flow_type="pkce")

    with pytest.raises(AuthPKCECodeVerifierMissingError):
        client.initialize_from_url("https://app.example/callback?code=abc")

    assert token_requests == []
    assert client.get_session() is None


def test_initialize_from_url_raises_pkce_error_before_exchange() -> None:
    token_requests: list[Request] = []
    client = mock_client([], token_requests, flow_type="pkce")
    start_oauth_flow(client)

    with pytest.raises(AuthImplicitGrantRedirectError) as raised:
        client.initialize_from_url(
            "https://app.example/callback?code=abc&error=access_denied"
            "&error_description=User+denied+access"
        )

    assert raised.value.message == "User denied access"
    assert token_requests == []


def test_initialize_ignores_url_without_callback_parameters() -> None:
    client = mock_client([], flow_type="pkce")
    changes: list[AuthStateChange] = []
    client.on_auth_state_change(changes.append)

    client.initialize(url="https://app.example/home?page=2")

    assert events(changes) == [AuthChangeEvent.INITIAL_SESSION]
    assert client.get_session() is None
