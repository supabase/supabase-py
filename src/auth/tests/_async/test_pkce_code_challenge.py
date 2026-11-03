import json
import time
from typing import Any, Callable

import pytest
from httpx import AsyncClient, MockTransport, Request, Response
from supabase_utils.http.adapters.httpx import AsyncHttpxSession

from supabase_auth import AsyncSupabaseAuthClient
from supabase_auth.errors import AuthError
from supabase_auth.helpers import generate_pkce_challenge
from supabase_auth.types import (
    AuthChangeEvent,
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
) -> AsyncSupabaseAuthClient:
    def handler(request: Request) -> Response:
        requests.append(request)
        return Response(200, json=payload)

    return AsyncSupabaseAuthClient(
        url="https://example.supabase.co/auth/v1",
        http_session=AsyncHttpxSession(
            client=AsyncClient(transport=MockTransport(handler))
        ),
        auto_refresh_token=False,
        flow_type=flow_type,
    )


def verifier_key(client: AsyncSupabaseAuthClient) -> str:
    return f"{client.session_manager.storage_key}-code-verifier"


def request_body(requests: list[Request]) -> dict[str, Any]:
    assert len(requests) == 1
    body: dict[str, Any] = json.loads(requests[0].content)
    return body


async def stored_verifier(client: AsyncSupabaseAuthClient) -> str | None:
    return await client.session_manager.storage.get_item(verifier_key(client))


async def assert_sends_challenge(
    payload: Any,
    call: Callable[[AsyncSupabaseAuthClient], Any],
) -> dict[str, Any]:
    requests: list[Request] = []
    client = mock_client(payload, requests)
    await call(client)
    stored = await stored_verifier(client)
    body = request_body(requests)
    assert stored
    assert "/" not in stored
    assert body["code_challenge"] == generate_pkce_challenge(stored)
    assert body["code_challenge_method"] == "s256"
    return body


async def test_email_sign_up_pkce_sends_code_challenge() -> None:
    await assert_sends_challenge(
        USER,
        lambda client: client.sign_up(
            SignUpWithPassword.email(email="a@example.com", password="password")
        ),
    )


async def test_email_sign_up_implicit_omits_code_challenge() -> None:
    requests: list[Request] = []
    client = mock_client(USER, requests, flow_type="implicit")
    await client.sign_up(
        SignUpWithPassword.email(email="a@example.com", password="password")
    )

    assert "code_challenge" not in request_body(requests)
    assert await stored_verifier(client) is None


async def test_phone_sign_up_pkce_omits_code_challenge() -> None:
    requests: list[Request] = []
    client = mock_client(USER, requests)
    await client.sign_up(
        SignUpWithPassword.phone(phone="+15555550100", password="password")
    )

    assert "code_challenge" not in request_body(requests)
    assert await stored_verifier(client) is None


async def test_email_otp_pkce_sends_code_challenge() -> None:
    await assert_sends_challenge(
        {},
        lambda client: client.sign_in_with_otp(
            SignInWithPasswordless.email(email="a@example.com")
        ),
    )


async def test_sso_pkce_sends_code_challenge() -> None:
    body = await assert_sends_challenge(
        {"url": "https://idp.example/sso"},
        lambda client: client.sign_in_with_sso(
            SignInWithSSO.domain(domain="example.com")
        ),
    )
    assert body["domain"] == "example.com"


async def test_reset_password_pkce_stores_recovery_verifier() -> None:
    requests: list[Request] = []
    client = mock_client({}, requests)
    await client.reset_password_for_email("a@example.com")

    stored = await stored_verifier(client)
    assert stored
    verifier, redirect_type = stored.split("/", 1)
    assert redirect_type == "PASSWORD_RECOVERY"
    body = request_body(requests)
    assert body["email"] == "a@example.com"
    assert body["code_challenge"] == generate_pkce_challenge(verifier)
    assert body["code_challenge_method"] == "s256"


async def test_update_user_email_pkce_sends_code_challenge() -> None:
    requests: list[Request] = []
    client = mock_client(USER, requests)
    session = Session.model_validate(
        {**SESSION, "expires_at": round(time.time()) + 3600}
    )
    await client.session_manager.storage.set_item(
        client.session_manager.storage_key, session.model_dump_json()
    )
    await client.update_user(UserAttributes(email="new@example.com"))

    stored = await stored_verifier(client)
    body = request_body(requests)
    assert stored
    assert body["email"] == "new@example.com"
    assert body["code_challenge"] == generate_pkce_challenge(stored)
    assert body["code_challenge_method"] == "s256"


async def test_update_user_without_email_omits_code_challenge() -> None:
    requests: list[Request] = []
    client = mock_client(USER, requests)
    session = Session.model_validate(
        {**SESSION, "expires_at": round(time.time()) + 3600}
    )
    await client.session_manager.storage.set_item(
        client.session_manager.storage_key, session.model_dump_json()
    )
    await client.update_user(UserAttributes(data={"name": "test"}))

    assert "code_challenge" not in request_body(requests)
    assert await stored_verifier(client) is None


async def test_exchange_code_strips_recovery_suffix() -> None:
    requests: list[Request] = []
    client = mock_client(SESSION, requests)
    await client.exchange_code_for_session(
        "auth-code", code_verifier="verifier-value/PASSWORD_RECOVERY"
    )

    assert request_body(requests)["code_verifier"] == "verifier-value"


async def test_exchange_code_uses_and_removes_stored_verifier() -> None:
    requests: list[Request] = []
    client = mock_client(SESSION, requests)
    await client.session_manager.storage.set_item(
        verifier_key(client), "stored-verifier/PASSWORD_RECOVERY"
    )
    await client.exchange_code_for_session("auth-code")

    assert request_body(requests)["code_verifier"] == "stored-verifier"
    assert await stored_verifier(client) is None


async def test_exchange_code_saves_session_and_signs_in() -> None:
    requests: list[Request] = []
    client = mock_client(SESSION, requests)
    events: list[AuthChangeEvent] = []
    client.on_auth_state_change(lambda event, session: events.append(event))
    await client.exchange_code_for_session("auth-code", code_verifier="verifier")

    assert await client.session_manager.storage.get_item(
        client.session_manager.storage_key
    )
    assert events == ["SIGNED_IN"]


async def test_autoconfirmed_email_sign_up_removes_verifier() -> None:
    requests: list[Request] = []
    client = mock_client(SESSION, requests)
    await client.sign_up(
        SignUpWithPassword.email(email="a@example.com", password="password")
    )

    assert await stored_verifier(client) is None


async def test_failed_exchange_removes_stored_verifier() -> None:
    def handler(request: Request) -> Response:
        return Response(400, json={"code": "bad_code", "msg": "invalid code"})

    client = AsyncSupabaseAuthClient(
        url="https://example.supabase.co/auth/v1",
        http_session=AsyncHttpxSession(
            client=AsyncClient(transport=MockTransport(handler))
        ),
        auto_refresh_token=False,
        flow_type="pkce",
    )
    await client.session_manager.storage.set_item(verifier_key(client), "verifier")
    with pytest.raises(AuthError):
        await client.exchange_code_for_session("auth-code")

    assert await stored_verifier(client) is None


async def test_sign_out_removes_stored_verifier() -> None:
    requests: list[Request] = []
    client = mock_client({}, requests)
    await client.session_manager.storage.set_item(verifier_key(client), "verifier")
    await client.sign_out()

    assert await stored_verifier(client) is None


async def test_raising_listener_does_not_stop_other_listeners() -> None:
    requests: list[Request] = []
    client = mock_client(SESSION, requests)
    events: list[AuthChangeEvent] = []

    def failing(event: AuthChangeEvent, session: Session | None) -> None:
        raise RuntimeError("listener failed")

    client.on_auth_state_change(failing)
    client.on_auth_state_change(lambda event, session: events.append(event))
    await client.exchange_code_for_session("auth-code", code_verifier="verifier")

    assert events == ["SIGNED_IN"]
