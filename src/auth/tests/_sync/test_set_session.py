import time

import pytest
from httpx import Client, MockTransport, Request, Response
from supabase_utils.http.adapters.httpx import HttpxSession
from supabase_utils.types import JSON

from supabase_auth import SyncSupabaseAuthClient
from supabase_auth.errors import AuthInvalidJwtError
from supabase_auth.types import AuthChangeEvent, AuthStateChange

from .conftest import base64url_segment

USER: dict[str, JSON] = {
    "id": "11111111-1111-1111-1111-111111111111",
    "aud": "authenticated",
    "app_metadata": {},
    "user_metadata": {},
    "created_at": "2026-01-01T00:00:00Z",
    "email": "user@example.com",
}


def token(exp: int) -> str:
    header = base64url_segment({"alg": "HS256", "typ": "JWT"})
    payload = base64url_segment({"exp": exp, "sub": USER["id"]})
    return f"{header}.{payload}.{base64url_segment({'sig': 1})}"


def mock_client(requests: list[Request] | None = None) -> SyncSupabaseAuthClient:
    def handler(request: Request) -> Response:
        if requests is not None:
            requests.append(request)
        if request.url.path.endswith("/token"):
            body = {
                "access_token": "refreshed-access",
                "refresh_token": "refreshed-refresh",
                "expires_in": 3600,
                "token_type": "bearer",
                "user": USER,
            }
            return Response(200, json=body)
        return Response(200, json=USER)

    return SyncSupabaseAuthClient(
        url="http://localhost",
        http_session=HttpxSession(client=Client(transport=MockTransport(handler))),
        auto_refresh_token=False,
    )


def events(changes: list[AuthStateChange]) -> list[AuthChangeEvent]:
    return [change.event for change in changes]


def test_set_session_with_unexpired_token_notifies_signed_in() -> None:
    client = mock_client()
    changes: list[AuthStateChange] = []
    client.on_auth_state_change(changes.append)

    client.set_session(token(int(time.time()) + 3600), "refresh-token")

    assert events(changes) == [
        AuthChangeEvent.INITIAL_SESSION,
        AuthChangeEvent.SIGNED_IN,
    ]


def test_set_session_with_expired_token_notifies_token_refreshed() -> None:
    client = mock_client()
    changes: list[AuthStateChange] = []
    client.on_auth_state_change(changes.append)

    client.set_session(token(int(time.time()) - 3600), "refresh-token")

    assert events(changes) == [
        AuthChangeEvent.INITIAL_SESSION,
        AuthChangeEvent.TOKEN_REFRESHED,
    ]


def test_set_session_stores_the_expiry_of_the_access_token() -> None:
    requests: list[Request] = []
    client = mock_client(requests)
    exp = int(time.time()) + 3600

    response = client.set_session(token(exp), "refresh-token")

    assert response.session is not None
    assert response.session.expires_at == exp
    assert 3590 <= response.session.expires_in <= 3600

    session = client.get_session()

    assert session is not None
    assert session.access_token == token(exp)
    assert [request.url.path for request in requests] == ["/user"]


@pytest.mark.parametrize(
    "access_token",
    [
        f"{base64url_segment({'typ': 'JWT'})}.{base64url_segment({'exp': 1})}.sig",
        f"{base64url_segment({'alg': 'HS256'})}.{base64url_segment(b'not json')}.sig",
        "\u00e9.\u00e9.\u00e9",
    ],
    ids=["alg-missing", "payload-not-json", "non-ascii"],
)
def test_set_session_raises_auth_error_for_malformed_jwt(
    access_token: str,
) -> None:
    requests: list[Request] = []
    client = mock_client(requests)

    with pytest.raises(AuthInvalidJwtError, match=r"Invalid JWT structure"):
        client.set_session(access_token, "refresh-token")

    assert requests == []
