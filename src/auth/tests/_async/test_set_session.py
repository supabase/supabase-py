import base64
import json
import time
from typing import Any

from httpx import AsyncClient, MockTransport, Request, Response
from supabase_utils.http.adapters.httpx import AsyncHttpxSession

from supabase_auth import AsyncSupabaseAuthClient
from supabase_auth.types import AuthChangeEvent

USER = {
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


def mock_client() -> AsyncSupabaseAuthClient:
    def handler(request: Request) -> Response:
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


async def test_set_session_with_unexpired_token_notifies_signed_in() -> None:
    client = mock_client()
    events: list[AuthChangeEvent] = []
    client.on_auth_state_change(lambda event, session: events.append(event))

    await client.set_session(token(int(time.time()) + 3600), "refresh-token")

    assert events == ["SIGNED_IN"]


async def test_set_session_with_expired_token_notifies_token_refreshed() -> None:
    client = mock_client()
    events: list[AuthChangeEvent] = []
    client.on_auth_state_change(lambda event, session: events.append(event))

    await client.set_session(token(int(time.time()) - 3600), "refresh-token")

    assert events == ["TOKEN_REFRESHED"]
