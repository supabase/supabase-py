import time
from collections.abc import Callable

import pytest
from httpx import Client, ConnectError, MockTransport, Request, Response
from supabase_utils.http.adapters.httpx import HttpxSession
from supabase_utils.http.errors import SupabaseTransportError
from supabase_utils.types import JSON

from supabase_auth import SyncMemoryStorage, SyncSupabaseAuthClient
from supabase_auth.errors import (
    AuthApiError,
    AuthRetryableError,
    AuthSessionMissingError,
)
from supabase_auth.types import (
    AuthChangeEvent,
    AuthStateChange,
    Session,
    SignOutReason,
    SignOutScope,
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

USER_INITIATED = AuthStateChange(
    AuthChangeEvent.SIGNED_OUT, sign_out_reason=SignOutReason.USER_INITIATED
)
SESSION_EXPIRED = AuthStateChange(
    AuthChangeEvent.SIGNED_OUT, sign_out_reason=SignOutReason.SESSION_EXPIRED
)


def stored_session(*, expired: bool = False) -> Session:
    return Session(
        access_token="old-access",
        refresh_token="old-refresh",
        token_type="bearer",
        expires_in=3600,
        expires_at=round(time.time()) + (-60 if expired else 3600),
        user=User.model_validate(USER),
    )


def no_content(request: Request) -> Response:
    return Response(204)


def refreshed(request: Request) -> Response:
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


def api_error(status: int, error_code: str) -> Handler:
    def handler(request: Request) -> Response:
        return Response(
            status, json={"code": status, "error_code": error_code, "msg": error_code}
        )

    return handler


def server_error(request: Request) -> Response:
    return Response(500, json={"code": 500, "msg": "unexpected failure"})


def connection_refused(request: Request) -> Response:
    raise ConnectError("connection refused", request=request)


class Endpoints:
    """Answers `/logout` with `logout` and `/token` with `token`, and
    records every request."""

    def __init__(
        self, logout: Handler = no_content, token: Handler = refreshed
    ) -> None:
        self.handlers = {"/logout": logout, "/token": token}
        self.requests: list[Request] = []

    def handle(self, request: Request) -> Response:
        self.requests.append(request)
        return self.handlers[request.url.path](request)

    @property
    def paths(self) -> list[str]:
        return [request.url.path for request in self.requests]

    def logout_token(self) -> str:
        logouts = [r for r in self.requests if r.url.path == "/logout"]
        return logouts[-1].headers["authorization"].removeprefix("Bearer ")


def signed_in_client(
    endpoints: Endpoints, session: Session | None
) -> tuple[SyncSupabaseAuthClient, list[AuthStateChange]]:
    client = SyncSupabaseAuthClient(
        url="http://auth.test",
        http_session=HttpxSession(
            client=Client(transport=MockTransport(endpoints.handle))
        ),
        auto_refresh_token=False,
    )
    manager = client.session_manager
    if session is not None:
        manager.storage.set_item(manager.storage_key, session.model_dump_json())
    manager.storage.set_item(client._code_verifier_storage_key, "verifier")
    changes: list[AuthStateChange] = []
    client.on_auth_state_change(changes.append)
    return client, changes


def stored_access_token(client: SyncSupabaseAuthClient) -> str | None:
    manager = client.session_manager
    raw = manager.storage.get_item(manager.storage_key)
    return Session.model_validate_json(raw).access_token if raw else None


def stored_verifier(client: SyncSupabaseAuthClient) -> str | None:
    return client.session_manager.storage.get_item(client._code_verifier_storage_key)


def after_initial(changes: list[AuthStateChange]) -> list[AuthStateChange]:
    assert changes[0].event is AuthChangeEvent.INITIAL_SESSION
    return changes[1:]


def test_an_invalid_scope_raises_without_a_request() -> None:
    endpoints = Endpoints()
    client, changes = signed_in_client(endpoints, stored_session())

    with pytest.raises(ValueError, match="everywhere"):
        client.sign_out("everywhere")  # pyrefly: ignore[bad-argument-type]

    assert endpoints.requests == []
    assert stored_access_token(client) == "old-access"
    assert after_initial(changes) == []


@pytest.mark.parametrize("scope", ["global", "local", "others"])
def test_the_scope_is_always_sent(scope: SignOutScope) -> None:
    endpoints = Endpoints()
    client, _changes = signed_in_client(endpoints, stored_session())

    client.sign_out(scope)

    assert endpoints.requests[0].url.params["scope"] == scope
    assert endpoints.logout_token() == "old-access"


@pytest.mark.parametrize("scope", ["global", "local"])
def test_without_a_session_clears_local_state_and_notifies(
    scope: SignOutScope,
) -> None:
    endpoints = Endpoints()
    client, changes = signed_in_client(endpoints, None)

    client.sign_out(scope)

    assert endpoints.requests == []
    assert stored_verifier(client) is None
    assert after_initial(changes) == [USER_INITIATED]


def test_others_without_a_session_raises() -> None:
    endpoints = Endpoints()
    client, changes = signed_in_client(endpoints, None)

    with pytest.raises(AuthSessionMissingError):
        client.sign_out("others")

    assert endpoints.requests == []
    assert stored_verifier(client) == "verifier"
    assert after_initial(changes) == []


@pytest.mark.parametrize("scope", ["global", "local"])
def test_a_successful_sign_out_removes_the_session(scope: SignOutScope) -> None:
    endpoints = Endpoints()
    client, changes = signed_in_client(endpoints, stored_session())

    client.sign_out(scope)

    assert stored_access_token(client) is None
    assert stored_verifier(client) is None
    assert after_initial(changes) == [USER_INITIATED]


def test_a_successful_sign_out_of_others_keeps_the_session() -> None:
    endpoints = Endpoints()
    client, changes = signed_in_client(endpoints, stored_session())

    client.sign_out("others")

    assert stored_access_token(client) == "old-access"
    assert stored_verifier(client) == "verifier"
    assert after_initial(changes) == []


@pytest.mark.parametrize(
    ("scope", "error_code"),
    [
        ("global", "user_not_found"),
        ("local", "user_not_found"),
        ("others", "user_not_found"),
        ("local", "session_not_found"),
    ],
)
def test_already_signed_out_is_a_success(scope: SignOutScope, error_code: str) -> None:
    endpoints = Endpoints(logout=api_error(403, error_code))
    client, _changes = signed_in_client(endpoints, stored_session())

    client.sign_out(scope)

    expected = "old-access" if scope == "others" else None
    assert stored_access_token(client) == expected


@pytest.mark.parametrize(
    ("logout", "error"),
    [
        (api_error(403, "session_not_found"), AuthApiError),
        (api_error(403, "bad_jwt"), AuthApiError),
        (api_error(401, "no_authorization"), AuthApiError),
        (server_error, AuthRetryableError),
        (connection_refused, SupabaseTransportError),
    ],
)
@pytest.mark.parametrize("scope", ["global", "others"])
def test_a_failed_sign_out_keeps_the_session(
    scope: SignOutScope, logout: Handler, error: type[Exception]
) -> None:
    endpoints = Endpoints(logout=logout)
    client, changes = signed_in_client(endpoints, stored_session())

    with pytest.raises(error):
        client.sign_out(scope)

    assert stored_access_token(client) == "old-access"
    assert stored_verifier(client) == "verifier"
    assert after_initial(changes) == []


@pytest.mark.parametrize(
    ("logout", "error"),
    [
        (api_error(403, "bad_jwt"), AuthApiError),
        (server_error, AuthRetryableError),
        (connection_refused, SupabaseTransportError),
    ],
)
def test_a_failed_local_sign_out_still_signs_the_device_out(
    logout: Handler, error: type[Exception]
) -> None:
    endpoints = Endpoints(logout=logout)
    client, changes = signed_in_client(endpoints, stored_session())

    with pytest.raises(error):
        client.sign_out("local")

    assert stored_access_token(client) is None
    assert stored_verifier(client) is None
    assert after_initial(changes) == [USER_INITIATED]


def test_local_signs_the_device_out_before_the_request() -> None:
    endpoints = Endpoints()
    client, changes = signed_in_client(endpoints, stored_session())
    stored_during_request: list[str | None] = []

    storage = client.session_manager.storage
    assert isinstance(storage, SyncMemoryStorage)

    def logout(request: Request) -> Response:
        stored_during_request.append(
            storage.storage.get(client.session_manager.storage_key)
        )
        return no_content(request)

    endpoints.handlers["/logout"] = logout

    client.sign_out("local")

    assert stored_during_request == [None]
    assert after_initial(changes) == [USER_INITIATED]


def test_local_refreshes_an_expired_token_in_memory_only() -> None:
    endpoints = Endpoints()
    client, changes = signed_in_client(endpoints, stored_session(expired=True))

    client.sign_out("local")

    assert endpoints.paths == ["/token", "/logout"]
    assert endpoints.logout_token() == "new-access"
    assert stored_access_token(client) is None
    assert after_initial(changes) == [USER_INITIATED]


@pytest.mark.parametrize(
    "error_code", ["refresh_token_not_found", "session_not_found", "session_expired"]
)
def test_local_with_a_session_that_is_gone_is_a_success(error_code: str) -> None:
    endpoints = Endpoints(token=api_error(400, error_code))
    client, changes = signed_in_client(endpoints, stored_session(expired=True))

    client.sign_out("local")

    assert endpoints.paths == ["/token"]
    assert stored_access_token(client) is None
    assert after_initial(changes) == [USER_INITIATED]


@pytest.mark.parametrize(
    ("token", "error"),
    [
        (api_error(400, "refresh_token_already_used"), AuthApiError),
        (server_error, AuthRetryableError),
        (connection_refused, SupabaseTransportError),
    ],
)
def test_local_with_a_failed_refresh_raises_signed_out(
    token: Handler, error: type[Exception]
) -> None:
    endpoints = Endpoints(token=token)
    client, changes = signed_in_client(endpoints, stored_session(expired=True))

    with pytest.raises(error):
        client.sign_out("local")

    assert endpoints.paths == ["/token"]
    assert stored_access_token(client) is None
    assert after_initial(changes) == [USER_INITIATED]


def test_global_stores_the_refreshed_session_before_the_request() -> None:
    endpoints = Endpoints(logout=server_error)
    client, changes = signed_in_client(endpoints, stored_session(expired=True))

    with pytest.raises(AuthRetryableError):
        client.sign_out("global")

    assert endpoints.paths == ["/token", "/logout"]
    assert endpoints.logout_token() == "new-access"
    assert stored_access_token(client) == "new-access"
    assert [change.event for change in after_initial(changes)] == [
        AuthChangeEvent.TOKEN_REFRESHED
    ]


@pytest.mark.parametrize(
    "error_code", ["refresh_token_not_found", "refresh_token_already_used"]
)
def test_global_with_a_rejected_refresh_signs_the_device_out(
    error_code: str,
) -> None:
    endpoints = Endpoints(token=api_error(400, error_code))
    client, changes = signed_in_client(endpoints, stored_session(expired=True))

    with pytest.raises(AuthApiError):
        client.sign_out("global")

    assert endpoints.paths == ["/token"]
    assert stored_access_token(client) is None
    assert stored_verifier(client) is None
    assert after_initial(changes) == [USER_INITIATED]


@pytest.mark.parametrize("scope", ["global", "others"])
@pytest.mark.parametrize(
    ("token", "error"),
    [
        (server_error, AuthRetryableError),
        (connection_refused, SupabaseTransportError),
    ],
)
def test_a_refresh_that_is_not_rejected_keeps_the_session(
    scope: SignOutScope, token: Handler, error: type[Exception]
) -> None:
    endpoints = Endpoints(token=token)
    client, changes = signed_in_client(endpoints, stored_session(expired=True))

    with pytest.raises(error):
        client.sign_out(scope)

    assert endpoints.paths == ["/token"]
    assert stored_access_token(client) == "old-access"
    assert after_initial(changes) == []


def test_others_with_a_rejected_refresh_reports_an_expired_session() -> None:
    endpoints = Endpoints(token=api_error(400, "refresh_token_not_found"))
    client, changes = signed_in_client(endpoints, stored_session(expired=True))

    with pytest.raises(AuthApiError):
        client.sign_out("others")

    assert endpoints.paths == ["/token"]
    assert stored_access_token(client) is None
    assert after_initial(changes) == [SESSION_EXPIRED]


def test_others_refreshes_an_expired_token_like_any_call() -> None:
    endpoints = Endpoints()
    client, changes = signed_in_client(endpoints, stored_session(expired=True))

    client.sign_out("others")

    assert endpoints.paths == ["/token", "/logout"]
    assert endpoints.logout_token() == "new-access"
    assert stored_access_token(client) == "new-access"
    assert [change.event for change in after_initial(changes)] == [
        AuthChangeEvent.TOKEN_REFRESHED
    ]
