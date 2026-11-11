import json
import time
from collections.abc import Callable
from typing import Any

import pytest
from httpx import AsyncClient, MockTransport, Request, Response
from supabase_utils.http.adapters.httpx import AsyncHttpxSession
from yarl import URL

from supabase_auth import AsyncSupabaseAuthClient
from supabase_auth.errors import AuthError, AuthPKCECodeVerifierMissingError
from supabase_auth.helpers import generate_pkce_challenge
from supabase_auth.types import (
    AuthChangeEvent,
    AuthFlowType,
    AuthStateChange,
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


def legacy_verifier_key(client: AsyncSupabaseAuthClient) -> str:
    return f"{client.session_manager.storage_key}-code-verifier"


def request_body(requests: list[Request]) -> dict[str, Any]:
    assert len(requests) == 1
    body: dict[str, Any] = json.loads(requests[0].content)
    return body


async def legacy_verifier(client: AsyncSupabaseAuthClient) -> str | None:
    return await client.session_manager.storage.get_item(legacy_verifier_key(client))


async def flow_verifier(client: AsyncSupabaseAuthClient, flow_id: str) -> str | None:
    return await client.session_manager.storage.get_item(
        f"{client.session_manager.storage_key}-flow-{flow_id}-code-verifier"
    )


def flow_index_key(client: AsyncSupabaseAuthClient) -> str:
    return f"{client.session_manager.storage_key}-flows-code-verifier"


async def pending_flows(client: AsyncSupabaseAuthClient) -> list[str]:
    raw = await client.session_manager.storage.get_item(flow_index_key(client))
    flows: list[str] = json.loads(raw) if raw else []
    return flows


async def stored_verifier(client: AsyncSupabaseAuthClient) -> str | None:
    flows = await pending_flows(client)
    return await flow_verifier(client, flows[-1]) if flows else None


async def start_oauth_flow(client: AsyncSupabaseAuthClient) -> str:
    response = await client.sign_in_with_oauth("github")
    assert response.flow_id
    return response.flow_id


async def store_session(client: AsyncSupabaseAuthClient) -> None:
    session = Session.model_validate(
        {**SESSION, "expires_at": round(time.time()) + 3600}
    )
    await client.session_manager.storage.set_item(
        client.session_manager.storage_key, session.model_dump_json()
    )


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
        legacy_verifier_key(client), "stored-verifier/PASSWORD_RECOVERY"
    )
    await client.exchange_code_for_session("auth-code")

    assert request_body(requests)["code_verifier"] == "stored-verifier"
    assert await legacy_verifier(client) is None


async def test_exchange_code_saves_session_and_signs_in() -> None:
    requests: list[Request] = []
    client = mock_client(SESSION, requests)
    changes: list[AuthStateChange] = []
    client.on_auth_state_change(changes.append)
    await client.exchange_code_for_session("auth-code", code_verifier="verifier")

    assert await client.session_manager.storage.get_item(
        client.session_manager.storage_key
    )
    assert [change.event for change in changes] == [
        AuthChangeEvent.INITIAL_SESSION,
        AuthChangeEvent.SIGNED_IN,
    ]


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
    await client.session_manager.storage.set_item(
        legacy_verifier_key(client), "verifier"
    )
    with pytest.raises(AuthError):
        await client.exchange_code_for_session("auth-code")

    assert await legacy_verifier(client) is None


async def test_sign_out_removes_stored_verifier() -> None:
    requests: list[Request] = []
    client = mock_client({}, requests)
    await client.session_manager.storage.set_item(
        legacy_verifier_key(client), "verifier"
    )
    await client.sign_out()

    assert await legacy_verifier(client) is None


async def test_raising_listener_does_not_stop_other_listeners() -> None:
    requests: list[Request] = []
    client = mock_client(SESSION, requests)
    changes: list[AuthStateChange] = []

    def failing(change: AuthStateChange) -> None:
        raise RuntimeError("listener failed")

    client.on_auth_state_change(failing)
    client.on_auth_state_change(changes.append)
    await client.exchange_code_for_session("auth-code", code_verifier="verifier")

    assert [change.event for change in changes] == [
        AuthChangeEvent.INITIAL_SESSION,
        AuthChangeEvent.SIGNED_IN,
    ]


async def test_oauth_pkce_returns_flow_id_of_stored_verifier() -> None:
    requests: list[Request] = []
    client = mock_client({}, requests)
    response = await client.sign_in_with_oauth("github")

    assert response.flow_id
    verifier = await flow_verifier(client, response.flow_id)
    assert verifier
    assert await legacy_verifier(client) is None
    assert await pending_flows(client) == [response.flow_id]
    assert URL(response.url).query["code_challenge"] == generate_pkce_challenge(
        verifier
    )


async def test_oauth_implicit_returns_no_flow_id() -> None:
    requests: list[Request] = []
    client = mock_client({}, requests, flow_type="implicit")
    response = await client.sign_in_with_oauth("github")

    assert response.flow_id is None
    assert await pending_flows(client) == []


async def test_sso_pkce_returns_flow_id() -> None:
    requests: list[Request] = []
    client = mock_client({"url": "https://idp.example/sso"}, requests)
    response = await client.sign_in_with_sso(SignInWithSSO.domain(domain="example.com"))

    assert response.url == "https://idp.example/sso"
    assert response.flow_id
    verifier = await flow_verifier(client, response.flow_id)
    assert verifier
    assert request_body(requests)["code_challenge"] == generate_pkce_challenge(verifier)


async def test_link_identity_pkce_returns_flow_id() -> None:
    requests: list[Request] = []
    client = mock_client({"url": "https://github.com/login"}, requests)
    await store_session(client)
    response = await client.link_identity("github")

    assert response.flow_id
    verifier = await flow_verifier(client, response.flow_id)
    assert verifier
    assert requests[0].url.params["code_challenge"] == generate_pkce_challenge(verifier)


async def test_concurrent_flows_exchange_with_their_own_verifier() -> None:
    requests: list[Request] = []
    client = mock_client(SESSION, requests)
    first = await start_oauth_flow(client)
    second = await start_oauth_flow(client)
    first_verifier = await flow_verifier(client, first)
    second_verifier = await flow_verifier(client, second)

    await client.exchange_code_for_session("first-code", flow_id=first)

    assert request_body(requests)["code_verifier"] == first_verifier
    assert await flow_verifier(client, first) is None
    assert await pending_flows(client) == [second]
    assert await stored_verifier(client) == second_verifier

    requests.clear()
    await client.exchange_code_for_session("second-code")

    assert request_body(requests)["code_verifier"] == second_verifier
    assert await pending_flows(client) == []
    assert await stored_verifier(client) is None


async def test_exchange_without_flow_id_keeps_older_flows() -> None:
    requests: list[Request] = []
    client = mock_client(SESSION, requests)
    first = await start_oauth_flow(client)
    second = await start_oauth_flow(client)
    first_verifier = await flow_verifier(client, first)

    await client.exchange_code_for_session("second-code")

    assert await flow_verifier(client, second) is None
    assert await pending_flows(client) == [first]
    assert await flow_verifier(client, first) == first_verifier


async def test_exchange_with_flow_id_strips_recovery_suffix() -> None:
    requests: list[Request] = []
    client = mock_client(SESSION, requests)
    await client.reset_password_for_email("a@example.com")
    [flow_id] = await pending_flows(client)
    verifier = await flow_verifier(client, flow_id)
    assert verifier
    code_verifier, redirect_type = verifier.split("/", 1)
    assert redirect_type == "PASSWORD_RECOVERY"

    requests.clear()
    await client.exchange_code_for_session("auth-code", flow_id=flow_id)

    assert request_body(requests)["code_verifier"] == code_verifier


@pytest.mark.parametrize("flow_id", ["0123456789abcdef", "../../session", ""])
async def test_exchange_with_unknown_flow_id_raises_without_request(
    flow_id: str,
) -> None:
    requests: list[Request] = []
    client = mock_client(SESSION, requests)
    pending = await start_oauth_flow(client)

    with pytest.raises(AuthPKCECodeVerifierMissingError) as error:
        await client.exchange_code_for_session("auth-code", flow_id=flow_id)

    assert error.value.flow_id == flow_id
    assert requests == []
    assert await pending_flows(client) == [pending]
    assert await stored_verifier(client) == await flow_verifier(client, pending)


async def test_exchange_with_flow_id_and_code_verifier_raises() -> None:
    requests: list[Request] = []
    client = mock_client(SESSION, requests)

    with pytest.raises(ValueError, match="flow_id or code_verifier"):
        await client.exchange_code_for_session(
            "auth-code", flow_id="0123456789abcdef", code_verifier="verifier"
        )

    assert requests == []


async def test_exchange_with_code_verifier_leaves_stored_flows() -> None:
    requests: list[Request] = []
    client = mock_client(SESSION, requests)
    pending = await start_oauth_flow(client)

    await client.exchange_code_for_session("auth-code", code_verifier="verifier")

    assert await pending_flows(client) == [pending]
    assert await stored_verifier(client) == await flow_verifier(client, pending)


async def test_sixth_flow_evicts_oldest() -> None:
    requests: list[Request] = []
    client = mock_client(SESSION, requests)
    flows = [await start_oauth_flow(client) for _ in range(6)]

    assert await pending_flows(client) == flows[1:]
    assert await flow_verifier(client, flows[0]) is None
    for flow_id in flows[1:]:
        assert await flow_verifier(client, flow_id)
    with pytest.raises(AuthPKCECodeVerifierMissingError):
        await client.exchange_code_for_session("auth-code", flow_id=flows[0])


async def test_flow_index_ignores_invalid_entries() -> None:
    requests: list[Request] = []
    client = mock_client({}, requests)
    await client.session_manager.storage.set_item(
        flow_index_key(client), json.dumps(["../session", 1, None])
    )
    flow_id = await start_oauth_flow(client)

    assert await pending_flows(client) == [flow_id]

    await client.session_manager.storage.set_item(flow_index_key(client), "{not json")
    second = await start_oauth_flow(client)

    assert await pending_flows(client) == [second]


async def test_failed_exchange_with_flow_id_removes_its_verifier() -> None:
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
    first = await start_oauth_flow(client)
    second = await start_oauth_flow(client)
    with pytest.raises(AuthError):
        await client.exchange_code_for_session("auth-code", flow_id=second)

    assert await flow_verifier(client, second) is None
    assert await pending_flows(client) == [first]
    assert await stored_verifier(client) == await flow_verifier(client, first)


async def test_sign_out_removes_all_flows() -> None:
    requests: list[Request] = []
    client = mock_client({}, requests)
    flows = [await start_oauth_flow(client) for _ in range(3)]
    await client.sign_out()

    assert await pending_flows(client) == []
    assert await stored_verifier(client) is None
    for flow_id in flows:
        assert await flow_verifier(client, flow_id) is None


async def test_autoconfirmed_sign_up_keeps_other_flows() -> None:
    requests: list[Request] = []
    client = mock_client(SESSION, requests)
    pending = await start_oauth_flow(client)
    await client.sign_up(
        SignUpWithPassword.email(email="a@example.com", password="password")
    )

    assert await pending_flows(client) == [pending]
    assert await flow_verifier(client, pending)


async def test_exchange_without_stored_verifier_raises_without_request() -> None:
    requests: list[Request] = []
    client = mock_client(SESSION, requests)

    with pytest.raises(AuthPKCECodeVerifierMissingError) as error:
        await client.exchange_code_for_session("auth-code")

    assert error.value.flow_id is None
    assert requests == []


async def test_exchange_without_flow_id_after_newer_flow_completed() -> None:
    requests: list[Request] = []
    client = mock_client(SESSION, requests)
    await client.reset_password_for_email("a@example.com")
    [reset_flow] = await pending_flows(client)
    reset_verifier = await flow_verifier(client, reset_flow)
    assert reset_verifier
    oauth_flow = await start_oauth_flow(client)
    await client.exchange_code_for_session("oauth-code", flow_id=oauth_flow)

    requests.clear()
    await client.exchange_code_for_session("reset-code")

    assert request_body(requests)["code_verifier"] == reset_verifier.split("/", 1)[0]
    assert await pending_flows(client) == []


async def test_exchange_without_flow_id_skips_flows_without_verifier() -> None:
    requests: list[Request] = []
    client = mock_client(SESSION, requests)
    first = await start_oauth_flow(client)
    first_verifier = await flow_verifier(client, first)
    await client.session_manager.storage.set_item(
        flow_index_key(client), json.dumps([first, "0123456789abcdef"])
    )

    await client.exchange_code_for_session("auth-code")

    assert request_body(requests)["code_verifier"] == first_verifier
    assert await pending_flows(client) == ["0123456789abcdef"]
