import json
from typing import Any

import pytest
from httpx import AsyncClient, MockTransport, Request, Response
from pydantic import ValidationError
from supabase_utils.http.adapters.httpx import AsyncHttpxSession
from supabase_utils.types import JSON

from supabase_auth import AsyncSupabaseAuthClient
from supabase_auth.types import (
    AuthChangeEvent,
    AuthStateChange,
    VerifyOtp,
    VerifyOtpParams,
)

USER: dict[str, JSON] = {
    "id": "11111111-1111-1111-1111-111111111111",
    "aud": "authenticated",
    "app_metadata": {},
    "user_metadata": {},
    "created_at": "2026-01-01T00:00:00Z",
    "email": "new@example.com",
}

SESSION: dict[str, JSON] = {
    "access_token": "access-token",
    "refresh_token": "refresh-token",
    "expires_in": 3600,
    "token_type": "bearer",
    "user": USER,
}

PENDING_EMAIL_CHANGE: dict[str, JSON] = {
    "msg": "Confirmation link accepted. Please proceed to confirm link sent to the other email",
    "code": "200",
}

EMAIL_CHANGE = VerifyOtp.token_hash(
    token_hash="email-change-token-hash", type="email_change"
)


def mock_client(
    payload: JSON = SESSION, requests: list[Request] | None = None
) -> AsyncSupabaseAuthClient:
    def handler(request: Request) -> Response:
        if requests is not None:
            requests.append(request)
        assert request.url.path.endswith("/verify")
        return Response(200, json=payload)

    return AsyncSupabaseAuthClient(
        url="https://example.supabase.co/auth/v1",
        http_session=AsyncHttpxSession(
            client=AsyncClient(transport=MockTransport(handler))
        ),
        auto_refresh_token=False,
    )


def events(changes: list[AuthStateChange]) -> list[AuthChangeEvent]:
    return [change.event for change in changes]


@pytest.mark.parametrize(
    ("params", "event"),
    [
        pytest.param(
            VerifyOtp.email(email="a@example.com", token="123456", type="recovery"),
            AuthChangeEvent.PASSWORD_RECOVERY,
            id="email-recovery",
        ),
        pytest.param(
            VerifyOtp.token_hash(token_hash="token-hash", type="recovery"),
            AuthChangeEvent.PASSWORD_RECOVERY,
            id="token-hash-recovery",
        ),
        pytest.param(
            VerifyOtp.email(email="a@example.com", token="123456", type="magiclink"),
            AuthChangeEvent.SIGNED_IN,
            id="email-magiclink",
        ),
        pytest.param(
            VerifyOtp.token_hash(token_hash="token-hash", type="email"),
            AuthChangeEvent.SIGNED_IN,
            id="token-hash-email",
        ),
        pytest.param(
            VerifyOtp.mobile(phone="+15555550100", token="123456", type="sms"),
            AuthChangeEvent.SIGNED_IN,
            id="mobile-sms",
        ),
        pytest.param(EMAIL_CHANGE, AuthChangeEvent.SIGNED_IN, id="email-change"),
    ],
)
async def test_verify_otp_notifies_the_event_of_the_otp_type(
    params: VerifyOtpParams, event: AuthChangeEvent
) -> None:
    client = mock_client()
    changes: list[AuthStateChange] = []
    client.on_auth_state_change(changes.append)

    response = await client.verify_otp(params)

    assert events(changes) == [AuthChangeEvent.INITIAL_SESSION, event]
    assert changes[-1].session == response.session
    assert await client.get_session() == response.session


@pytest.mark.parametrize(
    "params",
    [
        pytest.param(
            VerifyOtp.token_hash(token_hash="token-hash", type="recovery"),
            id="recovery",
        ),
        pytest.param(EMAIL_CHANGE, id="email-change"),
    ],
)
async def test_verify_otp_without_a_session_notifies_nothing(
    params: VerifyOtpParams,
) -> None:
    client = mock_client(USER)
    changes: list[AuthStateChange] = []
    client.on_auth_state_change(changes.append)

    response = await client.verify_otp(params)

    assert response.user is not None
    assert response.user.email == "new@example.com"
    assert response.session is None
    assert await client.get_session() is None
    assert events(changes) == [AuthChangeEvent.INITIAL_SESSION]


@pytest.mark.parametrize(
    "body",
    [
        PENDING_EMAIL_CHANGE,
        {"msg": "First email confirmed", "code": "200"},
        {**PENDING_EMAIL_CHANGE, "code": 200},
    ],
)
async def test_verify_otp_accepts_a_pending_secure_email_change(
    body: dict[str, Any],
) -> None:
    requests: list[Request] = []
    client = mock_client(body, requests)
    changes: list[AuthStateChange] = []
    client.on_auth_state_change(changes.append)

    response = await client.verify_otp(EMAIL_CHANGE)

    assert response.user is None
    assert response.session is None
    assert await client.get_session() is None
    assert events(changes) == [AuthChangeEvent.INITIAL_SESSION]
    assert len(requests) == 1
    assert requests[0].method == "POST"
    assert requests[0].url.path == "/auth/v1/verify"
    assert json.loads(requests[0].content) == {
        "token_hash": "email-change-token-hash",
        "type": "email_change",
    }


@pytest.mark.parametrize(
    ("params", "body"),
    [
        (EMAIL_CHANGE, {}),
        (EMAIL_CHANGE, {"msg": "Unexpected response", "code": "201"}),
        (EMAIL_CHANGE, {"code": "200"}),
        (
            VerifyOtp.token_hash(token_hash="token-hash", type="magiclink"),
            PENDING_EMAIL_CHANGE,
        ),
        (
            VerifyOtp.mobile(phone="+15555550100", token="123456", type="sms"),
            PENDING_EMAIL_CHANGE,
        ),
    ],
)
async def test_verify_otp_rejects_other_bodies_without_a_user(
    params: VerifyOtpParams, body: dict[str, Any]
) -> None:
    client = mock_client(body)
    changes: list[AuthStateChange] = []
    client.on_auth_state_change(changes.append)

    with pytest.raises(ValidationError):
        await client.verify_otp(params)

    assert await client.get_session() is None
    assert events(changes) == [AuthChangeEvent.INITIAL_SESSION]
