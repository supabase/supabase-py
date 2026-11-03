import base64
import json
import time
from collections.abc import Callable
from typing import Any
from urllib.parse import parse_qs, urlparse

import pytest
from httpx import Client, MockTransport, Request, Response
from supabase_auth import SyncGoTrueAdminAPI, SyncGoTrueClient
from supabase_auth.errors import (
    AuthApiError,
    AuthImplicitGrantRedirectError,
    AuthInvalidCredentialsError,
    AuthInvalidJwtError,
    AuthSessionMissingError,
    AuthWeakPasswordError,
)
from supabase_auth.types import PageParams, Session, UserIdentity

STORAGE_KEY = "supabase.auth.token"

USER: dict[str, Any] = {
    "id": "11111111-1111-1111-1111-111111111111",
    "aud": "authenticated",
    "app_metadata": {},
    "user_metadata": {},
    "created_at": "2026-01-01T00:00:00Z",
    "email": "user@example.com",
}

FACTOR_TIMESTAMPS = {
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-01T00:00:00Z",
}


def _b64(value: dict) -> str:
    raw = json.dumps(value, separators=(",", ":")).encode()
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _token(exp: int, **claims: Any) -> str:
    header = _b64({"alg": "HS256", "typ": "JWT"})
    payload = _b64({"exp": exp, "sub": USER["id"], **claims})
    return f"{header}.{payload}.{_b64({'sig': 1})}"


def _session_body(
    access_token: str = "new-access", user: dict[str, Any] | None = None
) -> dict[str, Any]:
    return {
        "access_token": access_token,
        "refresh_token": "new-refresh",
        "expires_in": 3600,
        "expires_at": int(time.time()) + 3600,
        "token_type": "bearer",
        "user": user or USER,
    }


Route = Callable[[Request], Response] | dict[str, Any] | list[Any]


class Server:
    def __init__(self, routes: dict[tuple[str, str], Route] | None = None) -> None:
        self.routes: dict[tuple[str, str], Route] = {
            ("GET", "/user"): USER,
            ("POST", "/token"): _session_body(),
            **(routes or {}),
        }
        self.requests: list[Request] = []

    def __call__(self, request: Request) -> Response:
        self.requests.append(request)
        route = self.routes.get((request.method, request.url.path))
        if route is None:
            return Response(404, json={"msg": f"no route for {request.url.path}"})
        if callable(route):
            return route(request)
        return Response(200, json=route)

    def find(self, method: str, path: str) -> Request:
        for request in self.requests:
            if request.method == method and request.url.path == path:
                return request
        raise AssertionError(f"{method} {path} was not requested")

    def body(self, method: str, path: str) -> Any:
        return json.loads(self.find(method, path).content)


def _client(server: Server, **kwargs: Any) -> SyncGoTrueClient:
    return SyncGoTrueClient(
        url="http://localhost",
        http_client=Client(transport=MockTransport(server)),
        auto_refresh_token=False,
        **kwargs,
    )


def _record_events(client: SyncGoTrueClient) -> list[str]:
    events: list[str] = []
    client.on_auth_state_change(lambda event, session: events.append(event))
    return events


def _signed_in(client: SyncGoTrueClient) -> str:
    access_token = _token(int(time.time()) + 3600)
    client.set_session(access_token, "refresh-token")
    return access_token


def _stored_session(expires_at: int) -> str:
    return Session.model_validate(
        {
            "access_token": _token(expires_at),
            "refresh_token": "stored-refresh",
            "expires_in": 3600,
            "expires_at": expires_at,
            "token_type": "bearer",
            "user": USER,
        }
    ).model_dump_json()


IMPLICIT_GRANT_URL = (
    "https://app.example/callback?access_token=access&expires_in=3600"
    "&refresh_token=refresh&token_type=bearer&provider_token=provider"
)


def test_initialize_from_url_saves_session_and_notifies() -> None:
    server = Server()
    client = _client(server)
    events = _record_events(client)

    client.initialize(url=IMPLICIT_GRANT_URL)

    session = client.get_session()
    assert session is not None
    assert session.access_token == "access"
    assert session.refresh_token == "refresh"
    assert session.provider_token == "provider"
    assert server.find("GET", "/user").headers["Authorization"] == "Bearer access"
    assert events == ["SIGNED_IN"]


def test_initialize_from_recovery_url_notifies_password_recovery() -> None:
    client = _client(Server())
    events = _record_events(client)

    client.initialize(url=f"{IMPLICIT_GRANT_URL}&type=recovery")

    assert events == ["SIGNED_IN", "PASSWORD_RECOVERY"]


def test_initialize_from_error_url_raises_with_details() -> None:
    client = _client(Server())
    url = (
        "https://app.example/callback?error=access_denied"
        "&error_code=otp_expired&error_description=Link+expired"
    )

    with pytest.raises(AuthImplicitGrantRedirectError) as exc_info:
        client.initialize_from_url(url)

    assert exc_info.value.message == "Link expired"
    assert exc_info.value.details == {"code": "otp_expired", "error": "access_denied"}
    assert client.get_session() is None


@pytest.mark.parametrize(
    ("query", "message"),
    [
        ("error_description=x&error=e", "No error_code detected."),
        ("error_description=x&error_code=c", "No error detected."),
        (
            "access_token=a&refresh_token=r&token_type=bearer",
            "No expires_in detected.",
        ),
        ("access_token=a&expires_in=1&token_type=bearer", "No refresh_token detected."),
        ("access_token=a&expires_in=1&refresh_token=r", "No token_type detected."),
    ],
)
def test_initialize_from_url_rejects_incomplete_redirects(
    query: str, message: str
) -> None:
    client = _client(Server())

    with pytest.raises(AuthImplicitGrantRedirectError, match=message):
        client.initialize_from_url(f"https://app.example/callback?{query}")


def test_initialize_without_url_restores_stored_session() -> None:
    client = _client(Server())
    client._storage.set_item(STORAGE_KEY, _stored_session(int(time.time()) + 3600))
    events = _record_events(client)

    client.initialize()

    session = client.get_session()
    assert session is not None
    assert session.refresh_token == "stored-refresh"
    assert events == ["SIGNED_IN"]


def test_initialize_without_url_drops_unparseable_session() -> None:
    client = _client(Server())
    client._storage.set_item(STORAGE_KEY, "not json")

    client.initialize()

    assert client._storage.get_item(STORAGE_KEY) is None


def test_initialize_refreshes_session_that_is_about_to_expire() -> None:
    server = Server()
    client = SyncGoTrueClient(
        url="http://localhost",
        http_client=Client(transport=MockTransport(server)),
    )
    client._storage.set_item(STORAGE_KEY, _stored_session(int(time.time()) + 1))
    events = _record_events(client)

    client.initialize()

    assert server.body("POST", "/token") == {"refresh_token": "stored-refresh"}
    assert events == ["TOKEN_REFRESHED"]
    client._remove_session()


def test_initialize_removes_session_when_refresh_is_rejected() -> None:
    server = Server(
        {
            ("POST", "/token"): lambda request: Response(
                400, json={"code": 400, "msg": "Invalid Refresh Token"}
            )
        }
    )
    client = SyncGoTrueClient(
        url="http://localhost",
        http_client=Client(transport=MockTransport(server)),
    )
    client._storage.set_item(STORAGE_KEY, _stored_session(int(time.time()) + 1))

    client.initialize()

    assert client._storage.get_item(STORAGE_KEY) is None


def test_sign_in_with_password_requires_email_or_phone() -> None:
    client = _client(Server())

    with pytest.raises(AuthInvalidCredentialsError):
        client.sign_in_with_password({"password": "secret"})  # type: ignore[arg-type]


def test_sign_in_with_id_token_saves_session() -> None:
    server = Server()
    client = _client(server)
    events = _record_events(client)

    response = client.sign_in_with_id_token(
        {"provider": "google", "token": "id-token", "nonce": "nonce"}
    )

    request = server.find("POST", "/token")
    assert request.url.params["grant_type"] == "id_token"
    body = json.loads(request.content)
    assert body["provider"] == "google"
    assert body["id_token"] == "id-token"
    assert body["nonce"] == "nonce"
    assert response.session is not None
    assert events == ["SIGNED_IN"]


def test_sign_in_with_sso_by_provider_id() -> None:
    server = Server({("POST", "/sso"): {"url": "https://idp.example/login"}})
    client = _client(server)

    response = client.sign_in_with_sso(
        {"provider_id": "provider", "options": {"redirect_to": "https://app"}}
    )

    body = server.body("POST", "/sso")
    assert body["provider_id"] == "provider"
    assert body["redirect_to"] == "https://app"
    assert "domain" not in body
    assert response.url == "https://idp.example/login"


def test_sign_in_with_sso_requires_domain_or_provider_id() -> None:
    client = _client(Server())

    with pytest.raises(AuthInvalidCredentialsError):
        client.sign_in_with_sso({})


def test_sign_in_with_oauth_builds_authorize_url() -> None:
    client = _client(Server())

    response = client.sign_in_with_oauth(
        {
            "provider": "github",
            "options": {
                "redirect_to": "https://app/callback",
                "scopes": "repo user",
                "query_params": {"prompt": "consent"},
            },
        }
    )

    url = urlparse(response.url)
    params = parse_qs(url.query)
    assert url.path == "/authorize"
    assert response.provider == "github"
    assert params == {
        "prompt": ["consent"],
        "redirect_to": ["https://app/callback"],
        "scopes": ["repo user"],
        "provider": ["github"],
    }


def test_sign_in_with_oauth_with_pkce_stores_verifier() -> None:
    client = _client(Server(), flow_type="pkce")

    response = client.sign_in_with_oauth({"provider": "github"})

    params = parse_qs(urlparse(response.url).query)
    assert params["code_challenge_method"] == ["s256"]
    assert params["code_challenge"][0]
    assert client._storage.get_item(f"{STORAGE_KEY}-code-verifier")


def test_exchange_code_for_session_uses_stored_recovery_verifier() -> None:
    server = Server()
    client = _client(server, flow_type="pkce")
    client._storage.set_item(
        f"{STORAGE_KEY}-code-verifier", "verifier/PASSWORD_RECOVERY"
    )
    events = _record_events(client)

    response = client.exchange_code_for_session(
        {"auth_code": "code", "redirect_to": "https://app"}
    )

    request = server.find("POST", "/token")
    assert request.url.params["grant_type"] == "pkce"
    assert request.url.params["redirect_to"] == "https://app"
    assert json.loads(request.content) == {
        "auth_code": "code",
        "code_verifier": "verifier",
    }
    assert response.session is not None
    assert client._storage.get_item(f"{STORAGE_KEY}-code-verifier") is None
    assert events == ["PASSWORD_RECOVERY"]


def test_exchange_code_for_session_prefers_explicit_verifier() -> None:
    server = Server()
    client = _client(server, flow_type="pkce")
    client._storage.set_item(f"{STORAGE_KEY}-code-verifier", "stored")

    client.exchange_code_for_session(
        {"auth_code": "code", "code_verifier": "explicit", "redirect_to": None}  # type: ignore[typeddict-item]
    )

    assert server.body("POST", "/token")["code_verifier"] == "explicit"


@pytest.mark.parametrize(
    "operation",
    [
        lambda client: client.link_identity({"provider": "github"}),
        lambda client: client.unlink_identity(
            UserIdentity.model_validate(
                {
                    "id": "1",
                    "identity_id": "2",
                    "user_id": USER["id"],
                    "identity_data": {},
                    "provider": "github",
                    "created_at": "2026-01-01T00:00:00Z",
                    "updated_at": "2026-01-01T00:00:00Z",
                }
            )
        ),
        lambda client: client.get_user_identities(),
        lambda client: client.reauthenticate(),
        lambda client: client.update_user({"data": {"a": 1}}),
        lambda client: client.refresh_session(),
        lambda client: client.mfa.enroll({"factor_type": "totp"}),
        lambda client: client.mfa.challenge({"factor_id": "f"}),
        lambda client: client.mfa.verify(
            {"factor_id": "f", "challenge_id": "c", "code": "1"}
        ),
        lambda client: client.mfa.unenroll({"factor_id": "f"}),
    ],
    ids=[
        "link_identity",
        "unlink_identity",
        "get_user_identities",
        "reauthenticate",
        "update_user",
        "refresh_session",
        "mfa.enroll",
        "mfa.challenge",
        "mfa.verify",
        "mfa.unenroll",
    ],
)
def test_methods_requiring_session_raise_when_signed_out(
    operation: Callable[[SyncGoTrueClient], Any],
) -> None:
    server = Server()
    client = _client(server)

    with pytest.raises(AuthSessionMissingError):
        operation(client)

    assert server.requests == []


def test_link_identity_requests_redirect_url_with_session() -> None:
    server = Server(
        {("GET", "/user/identities/authorize"): {"url": "https://github/authorize"}}
    )
    client = _client(server)
    access_token = _signed_in(client)

    response = client.link_identity(
        {"provider": "github", "options": {"scopes": "repo"}}
    )

    request = server.find("GET", "/user/identities/authorize")
    assert request.headers["Authorization"] == f"Bearer {access_token}"
    assert request.url.params["provider"] == "github"
    assert request.url.params["scopes"] == "repo"
    assert request.url.params["skip_http_redirect"] == "true"
    assert response.url == "https://github/authorize"


def test_unlink_identity_deletes_identity() -> None:
    server = Server({("DELETE", "/user/identities/identity-1"): {}})
    client = _client(server)
    _signed_in(client)
    identity = UserIdentity.model_validate(
        {
            "id": "1",
            "identity_id": "identity-1",
            "user_id": USER["id"],
            "identity_data": {},
            "provider": "github",
            "created_at": "2026-01-01T00:00:00Z",
            "updated_at": "2026-01-01T00:00:00Z",
        }
    )

    client.unlink_identity(identity)

    server.find("DELETE", "/user/identities/identity-1")


def test_reauthenticate_sends_request_with_session() -> None:
    server = Server({("GET", "/reauthenticate"): {}})
    client = _client(server)
    access_token = _signed_in(client)

    response = client.reauthenticate()

    request = server.find("GET", "/reauthenticate")
    assert request.headers["Authorization"] == f"Bearer {access_token}"
    assert response.user is None
    assert response.session is None


def test_mfa_enroll_phone_sends_phone_instead_of_issuer() -> None:
    server = Server(
        {
            ("POST", "/factors"): {
                "id": "factor",
                "type": "phone",
                "friendly_name": "Phone",
                "phone": "+15555550100",
            }
        }
    )
    client = _client(server)
    _signed_in(client)

    response = client.mfa.enroll(
        {"factor_type": "phone", "phone": "+15555550100", "friendly_name": "Phone"}
    )

    assert server.body("POST", "/factors") == {
        "friendly_name": "Phone",
        "factor_type": "phone",
        "phone": "+15555550100",
    }
    assert response.type == "phone"


def test_mfa_challenge_and_verify_saves_session() -> None:
    access_token = _token(int(time.time()) + 3600, aal="aal2")
    server = Server(
        {
            ("POST", "/factors/factor/challenge"): {
                "id": "challenge",
                "expires_at": int(time.time()) + 60,
            },
            ("POST", "/factors/factor/verify"): _session_body(access_token),
        }
    )
    client = _client(server)
    _signed_in(client)
    events = _record_events(client)

    response = client.mfa.challenge_and_verify(
        {"factor_id": "factor", "code": "123456"}
    )

    assert server.body("POST", "/factors/factor/verify") == {
        "factor_id": "factor",
        "challenge_id": "challenge",
        "code": "123456",
    }
    assert response.access_token == access_token
    session = client.get_session()
    assert session is not None
    assert session.access_token == access_token
    assert events == ["MFA_CHALLENGE_VERIFIED"]


def test_mfa_list_factors_groups_verified_factors() -> None:
    factors = [
        {"id": "t1", "factor_type": "totp", "status": "verified", **FACTOR_TIMESTAMPS},
        {
            "id": "t2",
            "factor_type": "totp",
            "status": "unverified",
            **FACTOR_TIMESTAMPS,
        },
        {"id": "p1", "factor_type": "phone", "status": "verified", **FACTOR_TIMESTAMPS},
    ]
    client = _client(Server({("GET", "/user"): {**USER, "factors": factors}}))
    _signed_in(client)

    response = client.mfa.list_factors()

    assert [f.id for f in response.all] == ["t1", "t2", "p1"]
    assert [f.id for f in response.totp] == ["t1"]
    assert [f.id for f in response.phone] == ["p1"]


def test_mfa_list_factors_without_session_is_empty() -> None:
    client = _client(Server())

    response = client.mfa.list_factors()

    assert response.all == []
    assert response.totp == []
    assert response.phone == []


def test_mfa_unenroll_deletes_factor() -> None:
    server = Server({("DELETE", "/factors/factor"): {"id": "factor"}})
    client = _client(server)
    _signed_in(client)

    response = client.mfa.unenroll({"factor_id": "factor"})

    assert response.id == "factor"


def test_refresh_session_uses_current_refresh_token() -> None:
    server = Server()
    client = _client(server)
    _signed_in(client)
    events = _record_events(client)

    response = client.refresh_session()

    assert server.body("POST", "/token") == {"refresh_token": "refresh-token"}
    assert response.session is not None
    assert response.session.access_token == "new-access"
    assert events == ["TOKEN_REFRESHED"]


def test_set_session_with_expired_token_and_no_refresh_token_raises() -> None:
    client = _client(Server())

    with pytest.raises(AuthSessionMissingError):
        client.set_session(_token(int(time.time()) - 60), "")


def test_get_claims_rejects_expired_token() -> None:
    client = _client(Server())

    with pytest.raises(AuthInvalidJwtError, match="JWT has expired"):
        client.get_claims(_token(int(time.time()) - 60))


def test_get_claims_rejects_token_without_expiry() -> None:
    client = _client(Server())
    header = _b64({"alg": "HS256", "typ": "JWT"})
    token = f"{header}.{_b64({'sub': USER['id']})}.{_b64({'sig': 1})}"

    with pytest.raises(AuthInvalidJwtError, match="no expiration time"):
        client.get_claims(token)


def test_api_errors_surface_status_and_code() -> None:
    server = Server(
        {
            ("POST", "/token"): lambda request: Response(
                400,
                json={
                    "code": 400,
                    "error_code": "invalid_credentials",
                    "msg": "Invalid login credentials",
                },
            )
        }
    )
    client = _client(server)

    with pytest.raises(AuthApiError) as exc_info:
        client.sign_in_with_password({"email": "user@example.com", "password": "x"})

    assert exc_info.value.status == 400
    assert exc_info.value.code == "invalid_credentials"
    assert exc_info.value.message == "Invalid login credentials"


def test_weak_password_errors_carry_reasons() -> None:
    server = Server(
        {
            ("POST", "/signup"): lambda request: Response(
                422,
                json={
                    "code": 422,
                    "error_code": "weak_password",
                    "msg": "Password is too weak",
                    "weak_password": {"reasons": ["length"]},
                },
            )
        }
    )
    client = _client(server)

    with pytest.raises(AuthWeakPasswordError) as exc_info:
        client.sign_up({"email": "user@example.com", "password": "x"})

    assert exc_info.value.status == 422
    assert exc_info.value.reasons == ["length"]


def test_admin_list_oauth_clients_parses_pagination_headers() -> None:
    def handler(request: Request) -> Response:
        assert request.url.params["page"] == "2"
        assert request.url.params["per_page"] == "10"
        return Response(
            200,
            json={"clients": []},
            headers={
                "x-total-count": "45",
                "link": (
                    '</admin/oauth/clients?page=3&per_page=10>; rel="next", '
                    '</admin/oauth/clients?page=5&per_page=10>; rel="last"'
                ),
            },
        )

    with Client(transport=MockTransport(handler)) as http_client:
        admin = SyncGoTrueAdminAPI(
            url="https://example.supabase.co/auth/v1", http_client=http_client
        )
        response = admin.oauth.list_clients(PageParams(page=2, per_page=10))

    assert response.total == 45
    assert response.next_page == 3
    assert response.last_page == 5


def test_set_session_rejects_non_jwt_access_token() -> None:
    client = _client(Server())

    with pytest.raises(AuthInvalidJwtError):
        client.set_session("opaque-token", "refresh-token")


def test_initialize_from_url_reads_tokens_from_fragment() -> None:
    client = _client(Server())
    url = IMPLICIT_GRANT_URL.replace("?", "#", 1)

    client.initialize(url=url)

    session = client.get_session()
    assert session is not None
    assert session.access_token == "access"
