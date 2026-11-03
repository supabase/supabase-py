from collections.abc import Callable
from typing import Any

import pytest
from httpx import AsyncClient, MockTransport, Request, Response
from supabase_auth import AsyncGoTrueClient
from supabase_auth.errors import AuthApiError
from supabase_auth.types import Session

_USER = {
    "id": "11111111-1111-1111-1111-111111111111",
    "aud": "authenticated",
    "app_metadata": {},
    "user_metadata": {},
    "created_at": "2026-01-01T00:00:00Z",
    "email": "user@example.com",
}

_OLD_SESSION = {
    "access_token": "old-access-token",
    "refresh_token": "old-refresh-token",
    "expires_in": 3600,
    "token_type": "bearer",
    "user": _USER,
}

_NEW_SESSION = {
    **_OLD_SESSION,
    "access_token": "new-access-token",
    "refresh_token": "new-refresh-token",
}

_ERROR = {"code": "invalid_credentials", "msg": "Invalid login credentials"}

SignInCall = Callable[[AsyncGoTrueClient], Any]


async def _sign_in_anonymously(client: AsyncGoTrueClient) -> Any:
    return await client.sign_in_anonymously()


async def _sign_up(client: AsyncGoTrueClient) -> Any:
    return await client.sign_up({"email": "user@example.com", "password": "secret"})


async def _sign_in_with_password(client: AsyncGoTrueClient) -> Any:
    return await client.sign_in_with_password(
        {"email": "user@example.com", "password": "secret"}
    )


async def _sign_in_with_id_token(client: AsyncGoTrueClient) -> Any:
    return await client.sign_in_with_id_token(
        {"provider": "google", "token": "id-token"}
    )


async def _sign_in_with_sso(client: AsyncGoTrueClient) -> Any:
    return await client.sign_in_with_sso({"domain": "example.com"})


async def _sign_in_with_otp(client: AsyncGoTrueClient) -> Any:
    return await client.sign_in_with_otp({"email": "user@example.com"})


async def _sign_in_with_oauth(client: AsyncGoTrueClient) -> Any:
    return await client.sign_in_with_oauth({"provider": "github"})


async def _client(
    handler: Callable[[Request], Response],
) -> tuple[AsyncGoTrueClient, list[str]]:
    client = AsyncGoTrueClient(
        url="https://example.supabase.co/auth/v1",
        http_client=AsyncClient(transport=MockTransport(handler)),
        auto_refresh_token=False,
    )
    await client._save_session(Session.model_validate(_OLD_SESSION))
    events: list[str] = []
    client.on_auth_state_change(lambda event, session: events.append(event))
    return client, events


async def _assert_old_session_kept(client: AsyncGoTrueClient) -> None:
    session = await client.get_session()
    assert session is not None
    assert session.access_token == "old-access-token"


@pytest.mark.parametrize(
    "call",
    [
        _sign_in_anonymously,
        _sign_up,
        _sign_in_with_password,
        _sign_in_with_id_token,
        _sign_in_with_sso,
        _sign_in_with_otp,
    ],
)
async def test_failed_request_keeps_existing_session(call: SignInCall) -> None:
    client, events = await _client(lambda request: Response(400, json=_ERROR))

    with pytest.raises(AuthApiError):
        await call(client)

    await _assert_old_session_kept(client)
    assert events == []


@pytest.mark.parametrize(
    "call,body",
    [
        (_sign_up, _USER),
        (_sign_in_with_sso, {"url": "https://idp.example.com/sso"}),
        (_sign_in_with_otp, {"message_id": "message-id"}),
        (_sign_in_with_oauth, None),
    ],
)
async def test_session_less_response_keeps_existing_session(
    call: SignInCall, body: dict | None
) -> None:
    def handler(request: Request) -> Response:
        assert body is not None, "sign_in_with_oauth must not send a request"
        return Response(200, json=body)

    client, events = await _client(handler)

    await call(client)

    await _assert_old_session_kept(client)
    assert events == []


@pytest.mark.parametrize(
    "call",
    [
        _sign_in_anonymously,
        _sign_up,
        _sign_in_with_password,
        _sign_in_with_id_token,
    ],
)
async def test_returned_session_replaces_existing_session(call: SignInCall) -> None:
    client, events = await _client(lambda request: Response(200, json=_NEW_SESSION))

    response = await call(client)

    assert response.session is not None
    assert response.session.access_token == "new-access-token"
    session = await client.get_session()
    assert session is not None
    assert session.access_token == "new-access-token"
    assert events == ["SIGNED_IN"]
