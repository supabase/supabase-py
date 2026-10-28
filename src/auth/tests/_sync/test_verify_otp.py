import json

import pytest
from httpx import Client, MockTransport, Request, Response
from pydantic import ValidationError
from supabase_auth import SyncGoTrueClient
from supabase_auth.types import VerifyOtpParams

_USER = {
    "id": "11111111-1111-1111-1111-111111111111",
    "aud": "authenticated",
    "app_metadata": {},
    "user_metadata": {},
    "created_at": "2026-01-01T00:00:00Z",
    "email": "new@example.com",
}


@pytest.mark.parametrize(
    "body",
    [
        {
            "msg": "Confirmation link accepted. Please proceed to confirm link sent to the other email",
            "code": "200",
        },
        {"msg": "First email confirmed", "code": "200"},
    ],
)
def test_verify_otp_accepts_first_secure_email_confirmation(body: dict) -> None:
    def handler(request: Request) -> Response:
        assert request.method == "POST"
        assert request.url.path == "/auth/v1/verify"
        assert json.loads(request.content) == {
            "gotrue_meta_security": {"captcha_token": None},
            "token_hash": "email-change-token-hash",
            "type": "email_change",
        }
        return Response(200, json=body)

    with Client(transport=MockTransport(handler)) as http_client:
        client = SyncGoTrueClient(
            url="https://example.supabase.co/auth/v1",
            http_client=http_client,
            auto_refresh_token=False,
            persist_session=False,
        )
        events: list[str] = []
        client.on_auth_state_change(lambda event, session: events.append(event))

        response = client.verify_otp(
            {"token_hash": "email-change-token-hash", "type": "email_change"}
        )

        assert response.user is None
        assert response.session is None
        assert client.get_session() is None
        assert events == []


@pytest.mark.parametrize("has_session", [False, True])
def test_verify_otp_preserves_user_and_session_responses(has_session: bool) -> None:
    body = (
        {
            "access_token": "access-token",
            "refresh_token": "refresh-token",
            "expires_in": 3600,
            "expires_at": 4102444800,
            "token_type": "bearer",
            "user": _USER,
        }
        if has_session
        else _USER
    )

    with Client(
        transport=MockTransport(lambda request: Response(200, json=body))
    ) as http_client:
        client = SyncGoTrueClient(
            url="https://example.supabase.co/auth/v1",
            http_client=http_client,
            auto_refresh_token=False,
            persist_session=False,
        )
        events: list[str] = []
        client.on_auth_state_change(lambda event, session: events.append(event))

        response = client.verify_otp(
            {"token_hash": "email-change-token-hash", "type": "email_change"}
        )

        assert response.user is not None
        assert response.user.id == _USER["id"]
        assert response.user.email == "new@example.com"
        if has_session:
            assert response.session is not None
            assert response.session.access_token == "access-token"
            assert client.get_session() == response.session
            assert events == ["SIGNED_IN"]
        else:
            assert response.session is None
            assert client.get_session() is None
            assert events == []


@pytest.mark.parametrize(
    "params,body",
    [
        ({"token_hash": "token-hash", "type": "email_change"}, {}),
        (
            {"token_hash": "token-hash", "type": "email_change"},
            {"msg": "Unexpected response", "code": "201"},
        ),
        (
            {"token_hash": "token-hash", "type": "email"},
            {"msg": "Unexpected response", "code": "200"},
        ),
    ],
)
def test_verify_otp_rejects_unrelated_malformed_responses(
    params: VerifyOtpParams, body: dict
) -> None:
    with Client(
        transport=MockTransport(lambda request: Response(200, json=body))
    ) as http_client:
        client = SyncGoTrueClient(
            url="https://example.supabase.co/auth/v1",
            http_client=http_client,
            auto_refresh_token=False,
            persist_session=False,
        )

        with pytest.raises(ValidationError):
            client.verify_otp(params)
