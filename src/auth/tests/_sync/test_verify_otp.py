import json

import pytest
from httpx import Client, MockTransport, Request, Response
from pydantic import ValidationError
from supabase_auth import SyncGoTrueClient
from supabase_auth.errors import AuthApiError
from supabase_auth.types import Session, VerifyOtpParams

_USER = {
    "id": "11111111-1111-1111-1111-111111111111",
    "aud": "authenticated",
    "app_metadata": {},
    "user_metadata": {},
    "created_at": "2026-01-01T00:00:00Z",
    "email": "new@example.com",
}

_SESSION = {
    "access_token": "access-token",
    "refresh_token": "refresh-token",
    "expires_in": 3600,
    "token_type": "bearer",
    "user": _USER,
}


def _client() -> SyncGoTrueClient:
    transport = MockTransport(lambda request: Response(200, json=_SESSION))
    return SyncGoTrueClient(
        url="http://localhost",
        http_client=Client(transport=transport),
        auto_refresh_token=False,
    )


def test_verify_otp_recovery_notifies_password_recovery() -> None:
    client = _client()
    events: list[str] = []
    client.on_auth_state_change(lambda event, session: events.append(event))

    client.verify_otp({"token_hash": "hash", "type": "recovery"})

    assert events == ["PASSWORD_RECOVERY"]


def test_verify_otp_magiclink_notifies_signed_in() -> None:
    client = _client()
    events: list[str] = []
    client.on_auth_state_change(lambda event, session: events.append(event))

    client.verify_otp({"token_hash": "hash", "type": "magiclink"})

    assert events == ["SIGNED_IN"]


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
def test_verify_otp_preserves_user_and_session_responses(
    has_session: bool,
) -> None:
    body = _SESSION if has_session else _USER

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


def test_verify_otp_rejects_non_json_email_change_response() -> None:
    with Client(
        transport=MockTransport(lambda request: Response(200, text="not json"))
    ) as http_client:
        client = SyncGoTrueClient(
            url="https://example.supabase.co/auth/v1",
            http_client=http_client,
            auto_refresh_token=False,
            persist_session=False,
        )

        with pytest.raises(ValidationError):
            client.verify_otp({"token_hash": "token-hash", "type": "email_change"})


def _signed_in_client(response: Response) -> SyncGoTrueClient:
    client = SyncGoTrueClient(
        url="https://example.supabase.co/auth/v1",
        http_client=Client(transport=MockTransport(lambda request: response)),
        auto_refresh_token=False,
        persist_session=False,
    )
    client._save_session(Session.model_validate(_SESSION))
    return client


def test_verify_otp_failure_keeps_existing_session() -> None:
    client = _signed_in_client(
        Response(
            403,
            json={"code": 403, "error_code": "otp_expired", "msg": "Token has expired"},
        )
    )
    events: list[str] = []
    client.on_auth_state_change(lambda event, session: events.append(event))

    with pytest.raises(AuthApiError):
        client.verify_otp({"token_hash": "hash", "type": "email_change"})

    session = client.get_session()
    assert session is not None
    assert session.access_token == "access-token"
    assert events == []


@pytest.mark.parametrize(
    "body",
    [
        _USER,
        {"msg": "Confirmation link accepted", "code": "200"},
    ],
)
def test_verify_otp_without_session_keeps_existing_session(body: dict) -> None:
    client = _signed_in_client(Response(200, json=body))

    response = client.verify_otp({"token_hash": "hash", "type": "email_change"})

    assert response.session is None
    session = client.get_session()
    assert session is not None
    assert session.access_token == "access-token"
