import base64
import json
import time

import httpx
from supabase_auth import SyncGoTrueClient

_USER = {
    "id": "11111111-1111-1111-1111-111111111111",
    "aud": "authenticated",
    "app_metadata": {},
    "user_metadata": {},
    "created_at": "2026-01-01T00:00:00Z",
    "email": "user@example.com",
}


def _b64(value: dict) -> str:
    raw = json.dumps(value, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _token(exp: int) -> str:
    header = _b64({"alg": "HS256", "typ": "JWT"})
    payload = _b64({"exp": exp, "sub": _USER["id"]})
    return f"{header}.{payload}.{_b64({'sig': 1})}"


def _client() -> SyncGoTrueClient:
    def handler(request: httpx.Request) -> httpx.Response:
        if request.url.path.endswith("/token"):
            body = {
                "access_token": "refreshed-access",
                "refresh_token": "refreshed-refresh",
                "expires_in": 3600,
                "token_type": "bearer",
                "user": _USER,
            }
            return httpx.Response(200, json=body)
        return httpx.Response(200, json=_USER)

    return SyncGoTrueClient(
        url="http://localhost",
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        auto_refresh_token=False,
    )


def test_set_session_with_unexpired_token_notifies_signed_in() -> None:
    client = _client()
    events: list[str] = []
    client.on_auth_state_change(lambda event, session: events.append(event))

    client.set_session(_token(int(time.time()) + 3600), "refresh-token")

    assert events == ["SIGNED_IN"]


def test_set_session_with_expired_token_notifies_token_refreshed() -> None:
    client = _client()
    events: list[str] = []
    client.on_auth_state_change(lambda event, session: events.append(event))

    client.set_session(_token(int(time.time()) - 3600), "refresh-token")

    assert events == ["TOKEN_REFRESHED"]
