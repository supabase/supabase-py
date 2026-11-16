import pytest
from httpx import Client, MockTransport, Request, Response
from supabase_utils.http.adapters.httpx import HttpxSession
from supabase_utils.types import JSON

from supabase_auth import SyncSupabaseAuthClient
from supabase_auth.types import (
    AuthChangeEvent,
    AuthStateChange,
    VerifyOtp,
    VerifyOtpParams,
)

SESSION: dict[str, JSON] = {
    "access_token": "access-token",
    "refresh_token": "refresh-token",
    "expires_in": 3600,
    "token_type": "bearer",
    "user": {
        "id": "11111111-1111-1111-1111-111111111111",
        "aud": "authenticated",
        "app_metadata": {},
        "user_metadata": {},
        "created_at": "2026-01-01T00:00:00Z",
    },
}


def mock_client(payload: JSON = SESSION) -> SyncSupabaseAuthClient:
    def handler(request: Request) -> Response:
        assert request.url.path.endswith("/verify")
        return Response(200, json=payload)

    return SyncSupabaseAuthClient(
        url="https://example.supabase.co/auth/v1",
        http_session=HttpxSession(client=Client(transport=MockTransport(handler))),
        auto_refresh_token=False,
    )


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
    ],
)
def test_verify_otp_notifies_the_event_of_the_otp_type(
    params: VerifyOtpParams, event: AuthChangeEvent
) -> None:
    client = mock_client()
    changes: list[AuthStateChange] = []
    client.on_auth_state_change(changes.append)

    response = client.verify_otp(params)

    assert [change.event for change in changes] == [
        AuthChangeEvent.INITIAL_SESSION,
        event,
    ]
    assert changes[-1].session == response.session
    assert client.get_session() == response.session


def test_verify_otp_without_a_session_notifies_nothing() -> None:
    client = mock_client(SESSION["user"])
    changes: list[AuthStateChange] = []
    client.on_auth_state_change(changes.append)

    response = client.verify_otp(
        VerifyOtp.token_hash(token_hash="token-hash", type="recovery")
    )

    assert response.session is None
    assert client.get_session() is None
    assert [change.event for change in changes] == [AuthChangeEvent.INITIAL_SESSION]
