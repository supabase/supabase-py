import base64
import json
import time

import httpx
import pytest
from supabase_auth import AsyncGoTrueClient
from supabase_auth.errors import AuthInvalidJwtError, AuthSessionMissingError

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


def _client(requests: list[httpx.Request] | None = None) -> AsyncGoTrueClient:
    def handler(request: httpx.Request) -> httpx.Response:
        if requests is not None:
            requests.append(request)
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

    return AsyncGoTrueClient(
        url="http://localhost",
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        auto_refresh_token=False,
    )


async def test_set_session_with_unexpired_token_notifies_signed_in() -> None:
    client = _client()
    events: list[str] = []
    client.on_auth_state_change(lambda event, session: events.append(event))

    await client.set_session(_token(int(time.time()) + 3600), "refresh-token")

    assert events == ["SIGNED_IN"]


async def test_set_session_with_expired_token_notifies_token_refreshed() -> None:
    client = _client()
    events: list[str] = []
    client.on_auth_state_change(lambda event, session: events.append(event))

    await client.set_session(_token(int(time.time()) - 3600), "refresh-token")

    assert events == ["TOKEN_REFRESHED"]


@pytest.mark.parametrize(
    "access_token",
    [
        "opaque-token",
        "header.payload",
        "a.b.c.d",
        "a.b.c",
        "\u00e9.\u00e9.\u00e9",
        "abc.",
        "header..signature",
    ],
    ids=[
        "not-a-jwt",
        "two-segments",
        "four-segments",
        "undecodable-base64",
        "non-ascii",
        "trailing-dot",
        "empty-payload",
    ],
)
async def test_set_session_with_malformed_token_raises_invalid_jwt(
    access_token: str,
) -> None:
    requests: list[httpx.Request] = []
    client = _client(requests)

    with pytest.raises(AuthInvalidJwtError):
        await client.set_session(access_token, "refresh-token")

    assert requests == []


async def test_set_session_without_tokens_raises_session_missing() -> None:
    requests: list[httpx.Request] = []
    client = _client(requests)

    with pytest.raises(AuthSessionMissingError):
        await client.set_session("", "")

    assert requests == []
