from collections.abc import Callable
from typing import Any

import pytest
from httpx import Client, MockTransport, Request, Response
from supabase_utils.http.adapters.httpx import HttpxSession
from supabase_utils.types import JSON

from supabase_auth import SyncSupabaseAuthClient
from supabase_auth.errors import AuthApiError
from supabase_auth.types import (
    AuthChangeEvent,
    AuthStateChange,
    Session,
    SignInWithPassword,
    SignInWithPasswordless,
    SignInWithSSO,
    SignUpWithPassword,
    VerifyOtp,
)

USER: dict[str, JSON] = {
    "id": "11111111-1111-1111-1111-111111111111",
    "aud": "authenticated",
    "app_metadata": {},
    "user_metadata": {},
    "created_at": "2026-01-01T00:00:00Z",
    "email": "user@example.com",
}

OLD_SESSION: dict[str, JSON] = {
    "access_token": "old-access-token",
    "refresh_token": "old-refresh-token",
    "expires_in": 3600,
    "token_type": "bearer",
    "user": USER,
}

NEW_SESSION: dict[str, JSON] = {
    **OLD_SESSION,
    "access_token": "new-access-token",
    "refresh_token": "new-refresh-token",
}

ERROR: dict[str, JSON] = {
    "code": 400,
    "error_code": "invalid_credentials",
    "msg": "Invalid login credentials",
}

SignInCall = Callable[[SyncSupabaseAuthClient], Any]


def sign_in_anonymously(client: SyncSupabaseAuthClient) -> Any:
    return client.sign_in_anonymously()


def sign_up(client: SyncSupabaseAuthClient) -> Any:
    return client.sign_up(
        SignUpWithPassword.email(email="user@example.com", password="secret")
    )


def sign_in_with_password(client: SyncSupabaseAuthClient) -> Any:
    return client.sign_in_with_password(
        SignInWithPassword.email(email="user@example.com", password="secret")
    )


def sign_in_with_id_token(client: SyncSupabaseAuthClient) -> Any:
    return client.sign_in_with_id_token("google", "id-token")


def sign_in_with_sso(client: SyncSupabaseAuthClient) -> Any:
    return client.sign_in_with_sso(SignInWithSSO.domain(domain="example.com"))


def sign_in_with_otp(client: SyncSupabaseAuthClient) -> Any:
    return client.sign_in_with_otp(
        SignInWithPasswordless.email(email="user@example.com")
    )


def sign_in_with_oauth(client: SyncSupabaseAuthClient) -> Any:
    return client.sign_in_with_oauth("github")


def verify_otp(client: SyncSupabaseAuthClient) -> Any:
    return client.verify_otp(
        VerifyOtp.email(email="user@example.com", token="123456", type="email")
    )


def client_with_old_session(
    handler: Callable[[Request], Response],
) -> tuple[SyncSupabaseAuthClient, list[AuthStateChange]]:
    client = SyncSupabaseAuthClient(
        url="https://example.supabase.co/auth/v1",
        http_session=HttpxSession(client=Client(transport=MockTransport(handler))),
        auto_refresh_token=False,
    )
    client.session_manager.save_session(Session.model_validate(OLD_SESSION))
    changes: list[AuthStateChange] = []
    client.on_auth_state_change(changes.append)
    return client, changes


def assert_old_session_kept(client: SyncSupabaseAuthClient) -> None:
    session = client.get_session()
    assert session is not None
    assert session.access_token == "old-access-token"


@pytest.mark.parametrize(
    "call",
    [
        sign_in_anonymously,
        sign_up,
        sign_in_with_password,
        sign_in_with_id_token,
        sign_in_with_sso,
        sign_in_with_otp,
        verify_otp,
    ],
)
def test_a_failed_request_keeps_the_existing_session(call: SignInCall) -> None:
    client, changes = client_with_old_session(lambda request: Response(400, json=ERROR))

    with pytest.raises(AuthApiError):
        call(client)

    assert_old_session_kept(client)
    assert [change.event for change in changes] == [AuthChangeEvent.INITIAL_SESSION]


@pytest.mark.parametrize(
    ("call", "body"),
    [
        (sign_up, USER),
        (verify_otp, USER),
        (sign_in_with_sso, {"url": "https://idp.example.com/sso"}),
        (sign_in_with_otp, {"message_id": "message-id"}),
        (sign_in_with_oauth, None),
    ],
)
def test_a_response_without_a_session_keeps_the_existing_session(
    call: SignInCall, body: JSON
) -> None:
    client, changes = client_with_old_session(lambda request: Response(200, json=body))

    call(client)

    assert_old_session_kept(client)
    assert [change.event for change in changes] == [AuthChangeEvent.INITIAL_SESSION]


@pytest.mark.parametrize(
    "call",
    [
        sign_in_anonymously,
        sign_up,
        sign_in_with_password,
        sign_in_with_id_token,
        verify_otp,
    ],
)
def test_a_returned_session_replaces_the_existing_session(
    call: SignInCall,
) -> None:
    client, changes = client_with_old_session(
        lambda request: Response(200, json=NEW_SESSION)
    )

    call(client)

    session = client.get_session()
    assert session is not None
    assert session.access_token == "new-access-token"
    assert [change.event for change in changes] == [
        AuthChangeEvent.INITIAL_SESSION,
        AuthChangeEvent.SIGNED_IN,
    ]
    assert changes[-1].session == session
