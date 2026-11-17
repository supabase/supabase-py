from collections.abc import Callable

import pytest
from httpx import Client, MockTransport, Request, Response
from supabase_utils.http.adapters.httpx import HttpxSession

from supabase_auth import SyncSupabaseAuthAdmin
from supabase_auth.errors import AuthApiError, AuthRetryableError
from supabase_auth.types import SignOutScope

Handler = Callable[[Request], Response]


def no_content(request: Request) -> Response:
    return Response(204)


def api_error(status: int, error_code: str) -> Handler:
    def handler(request: Request) -> Response:
        return Response(
            status, json={"code": status, "error_code": error_code, "msg": error_code}
        )

    return handler


def server_error(request: Request) -> Response:
    return Response(500, json={"code": 500, "msg": "unexpected failure"})


def admin_client(logout: Handler) -> tuple[SyncSupabaseAuthAdmin, list[Request]]:
    requests: list[Request] = []

    def handler(request: Request) -> Response:
        requests.append(request)
        return logout(request)

    client = SyncSupabaseAuthAdmin(
        url="https://example.supabase.co/auth/v1",
        default_headers={"Authorization": "Bearer service-role-key"},
        http_session=HttpxSession(client=Client(transport=MockTransport(handler))),
    )
    return client, requests


def test_sign_out_revokes_every_session_by_default() -> None:
    client, requests = admin_client(no_content)

    client.sign_out("user-access-token")

    [request] = requests
    assert request.method == "POST"
    assert request.url.path == "/auth/v1/logout"
    assert request.url.params["scope"] == "global"
    assert request.headers["authorization"] == "Bearer user-access-token"


@pytest.mark.parametrize("scope", ["global", "local", "others"])
def test_sign_out_sends_the_scope(scope: SignOutScope) -> None:
    client, requests = admin_client(no_content)

    client.sign_out("user-access-token", scope)

    assert requests[0].url.params["scope"] == scope


def test_an_invalid_scope_raises_without_a_request() -> None:
    client, requests = admin_client(no_content)

    with pytest.raises(ValueError, match="everywhere"):
        client.sign_out(
            "user-access-token",
            "everywhere",  # pyrefly: ignore[bad-argument-type]
        )

    assert requests == []


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
    client, _requests = admin_client(api_error(403, error_code))

    client.sign_out("user-access-token", scope)


@pytest.mark.parametrize(
    ("logout", "error"),
    [
        (api_error(403, "session_not_found"), AuthApiError),
        (api_error(403, "bad_jwt"), AuthApiError),
        (api_error(401, "no_authorization"), AuthApiError),
        (server_error, AuthRetryableError),
    ],
)
def test_a_failed_sign_out_raises(logout: Handler, error: type[Exception]) -> None:
    client, _requests = admin_client(logout)

    with pytest.raises(error):
        client.sign_out("user-access-token")
