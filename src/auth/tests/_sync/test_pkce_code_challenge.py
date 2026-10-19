import json
import time
from typing import Any, Callable

from httpx import Client, MockTransport, Request, Response
from supabase_utils.http.adapters.httpx import HttpxSession

from supabase_auth import SyncSupabaseAuthClient
from supabase_auth.helpers import generate_pkce_challenge
from supabase_auth.types import (
    AuthFlowType,
    Session,
    SignInWithPasswordless,
    SignInWithSSO,
    SignUpWithPassword,
    UserAttributes,
)

USER = {
    "id": "11111111-1111-1111-1111-111111111111",
    "aud": "authenticated",
    "app_metadata": {},
    "user_metadata": {},
    "created_at": "2020-01-01T00:00:00Z",
}
SESSION = {
    "access_token": "access-token",
    "refresh_token": "refresh-token",
    "expires_in": 3600,
    "token_type": "bearer",
    "user": USER,
}


def mock_client(
    payload: Any,
    requests: list[Request],
    flow_type: AuthFlowType = "pkce",
) -> SyncSupabaseAuthClient:
    def handler(request: Request) -> Response:
        requests.append(request)
        return Response(200, json=payload)

    return SyncSupabaseAuthClient(
        url="https://example.supabase.co/auth/v1",
        http_session=HttpxSession(client=Client(transport=MockTransport(handler))),
        auto_refresh_token=False,
        flow_type=flow_type,
    )


def verifier_key(client: SyncSupabaseAuthClient) -> str:
    return f"{client.session_manager.storage_key}-code-verifier"


def request_body(requests: list[Request]) -> dict[str, Any]:
    assert len(requests) == 1
    body: dict[str, Any] = json.loads(requests[0].content)
    return body


def stored_verifier(client: SyncSupabaseAuthClient) -> str | None:
    return client.session_manager.storage.get_item(verifier_key(client))


def assert_sends_challenge(
    payload: Any,
    call: Callable[[SyncSupabaseAuthClient], Any],
) -> dict[str, Any]:
    requests: list[Request] = []
    client = mock_client(payload, requests)
    call(client)
    stored = stored_verifier(client)
    body = request_body(requests)
    assert stored
    assert "/" not in stored
    assert body["code_challenge"] == generate_pkce_challenge(stored)
    assert body["code_challenge_method"] == "s256"
    return body


def test_email_sign_up_pkce_sends_code_challenge() -> None:
    assert_sends_challenge(
        USER,
        lambda client: client.sign_up(
            SignUpWithPassword.email(email="a@example.com", password="password")
        ),
    )


def test_email_sign_up_implicit_omits_code_challenge() -> None:
    requests: list[Request] = []
    client = mock_client(USER, requests, flow_type="implicit")
    client.sign_up(SignUpWithPassword.email(email="a@example.com", password="password"))

    assert "code_challenge" not in request_body(requests)
    assert stored_verifier(client) is None


def test_phone_sign_up_pkce_omits_code_challenge() -> None:
    requests: list[Request] = []
    client = mock_client(USER, requests)
    client.sign_up(SignUpWithPassword.phone(phone="+15555550100", password="password"))

    assert "code_challenge" not in request_body(requests)
    assert stored_verifier(client) is None


def test_email_otp_pkce_sends_code_challenge() -> None:
    assert_sends_challenge(
        {},
        lambda client: client.sign_in_with_otp(
            SignInWithPasswordless.email(email="a@example.com")
        ),
    )


def test_sso_pkce_sends_code_challenge() -> None:
    body = assert_sends_challenge(
        {"url": "https://idp.example/sso"},
        lambda client: client.sign_in_with_sso(
            SignInWithSSO.domain(domain="example.com")
        ),
    )
    assert body["domain"] == "example.com"


def test_reset_password_pkce_stores_recovery_verifier() -> None:
    requests: list[Request] = []
    client = mock_client({}, requests)
    client.reset_password_for_email("a@example.com")

    stored = stored_verifier(client)
    assert stored
    verifier, redirect_type = stored.split("/", 1)
    assert redirect_type == "PASSWORD_RECOVERY"
    body = request_body(requests)
    assert body["email"] == "a@example.com"
    assert body["code_challenge"] == generate_pkce_challenge(verifier)
    assert body["code_challenge_method"] == "s256"


def test_update_user_email_pkce_sends_code_challenge() -> None:
    requests: list[Request] = []
    client = mock_client(USER, requests)
    session = Session.model_validate(
        {**SESSION, "expires_at": round(time.time()) + 3600}
    )
    client.session_manager.storage.set_item(
        client.session_manager.storage_key, session.model_dump_json()
    )
    client.update_user(UserAttributes(email="new@example.com"))

    stored = stored_verifier(client)
    body = request_body(requests)
    assert stored
    assert body["email"] == "new@example.com"
    assert body["code_challenge"] == generate_pkce_challenge(stored)
    assert body["code_challenge_method"] == "s256"


def test_update_user_without_email_omits_code_challenge() -> None:
    requests: list[Request] = []
    client = mock_client(USER, requests)
    session = Session.model_validate(
        {**SESSION, "expires_at": round(time.time()) + 3600}
    )
    client.session_manager.storage.set_item(
        client.session_manager.storage_key, session.model_dump_json()
    )
    client.update_user(UserAttributes(data={"name": "test"}))

    assert "code_challenge" not in request_body(requests)
    assert stored_verifier(client) is None


def test_exchange_code_strips_recovery_suffix() -> None:
    requests: list[Request] = []
    client = mock_client(SESSION, requests)
    client.exchange_code_for_session("verifier-value/PASSWORD_RECOVERY", "auth-code")

    assert request_body(requests)["code_verifier"] == "verifier-value"
