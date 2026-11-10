import time
from collections.abc import Callable

import pytest
from httpx import AsyncClient, ConnectError, MockTransport, Request, Response
from supabase_utils.http.adapters.httpx import AsyncHttpxSession
from supabase_utils.http.errors import SupabaseTransportError
from supabase_utils.types import JSON

from supabase_auth import AsyncSupabaseAuthClient
from supabase_auth.errors import (
    AuthApiError,
    AuthError,
    AuthRetryableError,
    AuthUnknownError,
)
from supabase_auth.types import (
    AuthChangeEvent,
    AuthStateChange,
    Session,
    SignOutReason,
    User,
)

USER: dict[str, JSON] = {
    "id": "11111111-1111-1111-1111-111111111111",
    "aud": "authenticated",
    "app_metadata": {},
    "user_metadata": {},
    "created_at": "2026-01-01T00:00:00Z",
}

Handler = Callable[[Request], Response]


def refreshed_session(request: Request) -> Response:
    return Response(
        200,
        json={
            "access_token": "new-access",
            "refresh_token": "new-refresh",
            "token_type": "bearer",
            "expires_in": 3600,
            "user": USER,
        },
    )


def rejected(request: Request) -> Response:
    return Response(
        400,
        json={
            "code": 400,
            "error_code": "refresh_token_not_found",
            "msg": "Invalid Refresh Token: Refresh Token Not Found",
        },
    )


def rate_limited(request: Request) -> Response:
    return Response(
        429,
        json={"code": 429, "error_code": "over_request_rate_limit", "msg": "slow"},
    )


def server_error(request: Request) -> Response:
    return Response(500, json={"code": 500, "msg": "unexpected failure"})


def bad_gateway(request: Request) -> Response:
    return Response(502, json={"code": 502, "msg": "bad gateway"})


def html_not_found(request: Request) -> Response:
    return Response(404, text="<html>not found</html>")


def connection_refused(request: Request) -> Response:
    raise ConnectError("connection refused", request=request)


def expired_session() -> Session:
    return Session(
        access_token="old-access",
        refresh_token="old-refresh",
        token_type="bearer",
        expires_in=3600,
        expires_at=round(time.time()) - 60,
        user=User.model_validate(USER),
    )


def events(changes: list[AuthStateChange]) -> list[AuthChangeEvent]:
    return [change.event for change in changes]


async def client_with_expired_session(
    handler: Handler,
    requests: list[Request] | None = None,
    *,
    auto_refresh_token: bool = False,
) -> tuple[AsyncSupabaseAuthClient, list[AuthStateChange]]:
    def recording(request: Request) -> Response:
        if requests is not None:
            requests.append(request)
        return handler(request)

    client = AsyncSupabaseAuthClient(
        url="http://auth.test",
        http_session=AsyncHttpxSession(
            client=AsyncClient(transport=MockTransport(recording))
        ),
        auto_refresh_token=auto_refresh_token,
    )
    manager = client.session_manager
    await manager.storage.set_item(
        manager.storage_key, expired_session().model_dump_json()
    )
    changes: list[AuthStateChange] = []
    client.on_auth_state_change(changes.append)
    return client, changes


async def stored_access_token(client: AsyncSupabaseAuthClient) -> str | None:
    manager = client.session_manager
    raw = await manager.storage.get_item(manager.storage_key)
    return Session.model_validate_json(raw).access_token if raw else None


async def test_a_rejected_refresh_removes_the_session_notifies_and_raises() -> None:
    client, changes = await client_with_expired_session(rejected)

    with pytest.raises(AuthApiError) as error:
        await client.get_session()

    assert error.value.code == "refresh_token_not_found"
    assert await stored_access_token(client) is None
    assert changes[-1] == AuthStateChange(
        AuthChangeEvent.SIGNED_OUT,
        sign_out_reason=SignOutReason.SESSION_EXPIRED,
    )


@pytest.mark.parametrize(
    ("handler", "error"),
    [
        (rate_limited, AuthRetryableError),
        (server_error, AuthRetryableError),
        (bad_gateway, AuthRetryableError),
        (html_not_found, AuthUnknownError),
        (connection_refused, SupabaseTransportError),
    ],
)
async def test_a_refresh_that_is_not_rejected_keeps_the_session(
    handler: Handler, error: type[Exception]
) -> None:
    client, changes = await client_with_expired_session(handler)

    with pytest.raises(error):
        await client.get_session()

    assert await stored_access_token(client) == "old-access"
    assert events(changes) == [AuthChangeEvent.INITIAL_SESSION]


async def test_a_rate_limited_refresh_keeps_the_error_code() -> None:
    client, _changes = await client_with_expired_session(rate_limited)

    with pytest.raises(AuthRetryableError) as error:
        await client.get_session()

    assert error.value.status_code == 429
    assert error.value.code == "over_request_rate_limit"


async def test_refresh_session_of_an_expired_session_sends_one_request() -> None:
    requests: list[Request] = []
    client, changes = await client_with_expired_session(refreshed_session, requests)

    response = await client.refresh_session()

    assert response.session is not None
    assert response.session.access_token == "new-access"
    assert [request.url.path for request in requests] == ["/token"]
    assert events(changes) == [
        AuthChangeEvent.INITIAL_SESSION,
        AuthChangeEvent.TOKEN_REFRESHED,
    ]


async def test_an_unreadable_stored_session_is_removed_as_missing() -> None:
    client, _changes = await client_with_expired_session(refreshed_session)
    manager = client.session_manager
    await manager.storage.set_item(manager.storage_key, "not a session")
    changes: list[AuthStateChange] = []
    client.on_auth_state_change(changes.append)

    assert await client.get_session() is None

    assert await manager.storage.get_item(manager.storage_key) is None
    assert changes[-1] == AuthStateChange(
        AuthChangeEvent.SIGNED_OUT,
        sign_out_reason=SignOutReason.SESSION_MISSING,
    )


async def test_initialize_from_storage_signs_out_on_a_rejected_refresh() -> None:
    client, changes = await client_with_expired_session(
        rejected, auto_refresh_token=True
    )

    await client.initialize_from_storage()

    assert await stored_access_token(client) is None
    assert changes[-1] == AuthStateChange(
        AuthChangeEvent.SIGNED_OUT,
        sign_out_reason=SignOutReason.SESSION_EXPIRED,
    )
    assert client.session_manager.refresh_token_timer is None


async def test_initialize_from_storage_retries_a_failed_refresh_later() -> None:
    client, changes = await client_with_expired_session(
        bad_gateway, auto_refresh_token=True
    )

    await client.initialize_from_storage()

    assert await stored_access_token(client) == "old-access"
    assert events(changes) == [AuthChangeEvent.INITIAL_SESSION]
    timer = client.session_manager.refresh_token_timer
    assert timer is not None
    timer.cancel()


async def test_initialize_from_storage_keeps_an_expired_session_without_auto_refresh() -> (
    None
):
    requests: list[Request] = []
    client, changes = await client_with_expired_session(refreshed_session, requests)

    await client.initialize_from_storage()

    assert requests == []
    assert await stored_access_token(client) == "old-access"
    assert events(changes) == [AuthChangeEvent.INITIAL_SESSION]

    session = await client.get_session()

    assert session is not None
    assert session.access_token == "new-access"


async def test_initialize_from_storage_removes_a_session_without_refresh_token() -> (
    None
):
    client, changes = await client_with_expired_session(refreshed_session)
    manager = client.session_manager
    session = expired_session()
    session.refresh_token = ""
    await manager.storage.set_item(manager.storage_key, session.model_dump_json())

    await client.initialize_from_storage()

    assert await manager.storage.get_item(manager.storage_key) is None
    assert changes[-1] == AuthStateChange(
        AuthChangeEvent.SIGNED_OUT,
        sign_out_reason=SignOutReason.SESSION_MISSING,
    )


async def test_a_rejected_refresh_is_an_auth_error() -> None:
    client, _changes = await client_with_expired_session(rejected)

    with pytest.raises(AuthError):
        await client.get_session()
