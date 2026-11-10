import base64
import json
import time
from typing import Any

from httpx import AsyncClient, MockTransport, Request, Response
from supabase_utils.http.adapters.httpx import AsyncHttpxSession
from supabase_utils.types import JSON

from supabase_auth import AsyncSupabaseAuthClient
from supabase_auth.types import AuthChangeEvent, AuthStateChange

USER: dict[str, JSON] = {
    "id": "11111111-1111-1111-1111-111111111111",
    "aud": "authenticated",
    "app_metadata": {},
    "user_metadata": {},
    "created_at": "2026-01-01T00:00:00Z",
    "email": "user@example.com",
}


def b64(value: dict[str, Any]) -> str:
    raw = json.dumps(value, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def token(exp: int) -> str:
    header = b64({"alg": "HS256", "typ": "JWT"})
    payload = b64({"exp": exp, "sub": USER["id"]})
    return f"{header}.{payload}.{b64({'sig': 1})}"


def mock_client(requests: list[Request] | None = None) -> AsyncSupabaseAuthClient:
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

    return AsyncSupabaseAuthClient(
        url="http://localhost",
        http_session=AsyncHttpxSession(
            client=AsyncClient(transport=MockTransport(handler))
        ),
        auto_refresh_token=False,
    )


def events(changes: list[AuthStateChange]) -> list[AuthChangeEvent]:
    return [change.event for change in changes]


async def test_set_session_with_unexpired_token_notifies_signed_in() -> None:
    client = mock_client()
    changes: list[AuthStateChange] = []
    client.on_auth_state_change(changes.append)

    await client.set_session(token(int(time.time()) + 3600), "refresh-token")

    assert events(changes) == [
        AuthChangeEvent.INITIAL_SESSION,
        AuthChangeEvent.SIGNED_IN,
    ]


async def test_set_session_with_expired_token_notifies_token_refreshed() -> None:
    client = mock_client()
    changes: list[AuthStateChange] = []
    client.on_auth_state_change(changes.append)

    await client.set_session(token(int(time.time()) - 3600), "refresh-token")

    assert events(changes) == [
        AuthChangeEvent.INITIAL_SESSION,
        AuthChangeEvent.TOKEN_REFRESHED,
    ]


async def test_set_session_stores_the_expiry_of_the_access_token() -> None:
    requests: list[Request] = []
    client = mock_client(requests)
    exp = int(time.time()) + 3600

    response = await client.set_session(token(exp), "refresh-token")

    assert response.session is not None
    assert response.session.expires_at == exp
    assert 3590 <= response.session.expires_in <= 3600

    session = await client.get_session()

    assert session is not None
    assert session.access_token == token(exp)
    assert [request.url.path for request in requests] == ["/user"]
