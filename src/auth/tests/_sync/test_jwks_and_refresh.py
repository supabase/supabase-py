import json
import sys
import time
from typing import Any
from unittest.mock import patch

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec
from httpx import Client, ConnectError, MockTransport, Request, Response
from jwt.algorithms import ECAlgorithm
from supabase_auth import SyncGoTrueClient
from supabase_auth.errors import AuthInvalidJwtError, AuthSessionMissingError
from supabase_auth.types import JWKSet, Session

STORAGE_KEY = "supabase.auth.token"

USER: dict[str, Any] = {
    "id": "11111111-1111-1111-1111-111111111111",
    "aud": "authenticated",
    "app_metadata": {},
    "user_metadata": {},
    "created_at": "2026-01-01T00:00:00Z",
    "email": "user@example.com",
}

PRIVATE_KEY = ec.generate_private_key(ec.SECP256R1())
OTHER_PRIVATE_KEY = ec.generate_private_key(ec.SECP256R1())


def _jwk(kid: str, private_key: ec.EllipticCurvePrivateKey = PRIVATE_KEY) -> dict:
    jwk = json.loads(ECAlgorithm.to_jwk(private_key.public_key()))
    return {**jwk, "kid": kid, "alg": "ES256", "use": "sig"}


def _signed_token(
    kid: str = "key-1", private_key: ec.EllipticCurvePrivateKey = PRIVATE_KEY
) -> str:
    return jwt.encode(
        {"sub": USER["id"], "exp": int(time.time()) + 3600, "role": "authenticated"},
        private_key,
        algorithm="ES256",
        headers={"kid": kid},
    )


class JwksServer:
    def __init__(self, keys: list[dict]) -> None:
        self.keys = keys
        self.requests: list[Request] = []

    def __call__(self, request: Request) -> Response:
        self.requests.append(request)
        if request.url.path == "/.well-known/jwks.json":
            return Response(200, json={"keys": self.keys})
        return Response(404, json={"msg": "not found"})

    @property
    def jwks_fetches(self) -> int:
        return sum(r.url.path == "/.well-known/jwks.json" for r in self.requests)


def _client(handler: Any, **kwargs: Any) -> SyncGoTrueClient:
    return SyncGoTrueClient(
        url="http://localhost",
        http_client=Client(transport=MockTransport(handler)),
        auto_refresh_token=False,
        **kwargs,
    )


def test_get_claims_verifies_asymmetric_token_and_caches_jwks() -> None:
    server = JwksServer([_jwk("key-1")])
    client = _client(server)

    first = client.get_claims(_signed_token())
    second = client.get_claims(_signed_token())

    assert first is not None
    assert first["claims"]["sub"] == USER["id"]
    assert first["headers"]["kid"] == "key-1"
    assert second is not None
    assert server.jwks_fetches == 1


def test_get_claims_refetches_jwks_after_ttl() -> None:
    server = JwksServer([_jwk("key-1")])
    client = _client(server)
    client.get_claims(_signed_token())

    client._jwks_cached_at = time.time() - client._jwks_ttl - 1
    client.get_claims(_signed_token())

    assert server.jwks_fetches == 2


def test_get_claims_prefers_supplied_jwks() -> None:
    server = JwksServer([])
    client = _client(server)
    jwks: JWKSet = {"keys": [_jwk("key-1")]}  # type: ignore[list-item]

    response = client.get_claims(_signed_token(), jwks=jwks)

    assert response is not None
    assert server.requests == []


def test_get_claims_rejects_unknown_signing_key() -> None:
    client = _client(JwksServer([_jwk("other-key")]))

    with pytest.raises(AuthInvalidJwtError, match="No matching signing key"):
        client.get_claims(_signed_token(kid="key-1"))


def test_get_claims_rejects_empty_jwks() -> None:
    client = _client(JwksServer([]))

    with pytest.raises(AuthInvalidJwtError, match="JWKS is empty"):
        client.get_claims(_signed_token())


def test_get_claims_rejects_invalid_signature() -> None:
    client = _client(JwksServer([_jwk("key-1")]))
    forged = _signed_token(kid="key-1", private_key=OTHER_PRIVATE_KEY)

    with pytest.raises(AuthInvalidJwtError, match="Invalid JWT signature"):
        client.get_claims(forged)


def _session_json(expires_at: int | None) -> str:
    body: dict[str, Any] = {
        "access_token": "stored-access",
        "refresh_token": "stored-refresh",
        "expires_in": 3600,
        "token_type": "bearer",
        "user": USER,
    }
    if expires_at is None:
        return json.dumps({**body, "expires_in": 0})
    return Session.model_validate({**body, "expires_at": expires_at}).model_dump_json()


def test_stored_session_without_expiry_is_treated_as_missing() -> None:
    client = _client(JwksServer([]))
    client._storage.set_item(STORAGE_KEY, _session_json(None))

    assert client.get_session() is None
    assert client._storage.get_item(STORAGE_KEY) is None


def test_initialize_schedules_retry_on_network_error() -> None:
    def offline(request: Request) -> Response:
        raise ConnectError("offline", request=request)

    client = SyncGoTrueClient(
        url="http://localhost",
        http_client=Client(transport=MockTransport(offline)),
    )
    client._storage.set_item(STORAGE_KEY, _session_json(int(time.time()) + 1))

    with patch.object(sys.modules[SyncGoTrueClient.__module__], "Timer") as timer:
        client.initialize()

    timer.assert_called_once()
    assert timer.call_args.args[0] == 200
    timer.return_value.start.assert_called_once()
    assert client._storage.get_item(STORAGE_KEY) is not None


def test_refresh_returning_no_session_raises_session_missing() -> None:
    def handler(request: Request) -> Response:
        return Response(200, json=USER)

    client = _client(handler)

    with pytest.raises(AuthSessionMissingError):
        client.refresh_session("refresh-token")


def test_update_user_email_with_pkce_sends_code_challenge() -> None:
    requests: list[Request] = []
    now = int(time.time())

    def handler(request: Request) -> Response:
        requests.append(request)
        if request.url.path == "/token":
            return Response(
                200,
                json={
                    "access_token": "access",
                    "refresh_token": "refresh",
                    "expires_in": 3600,
                    "expires_at": now + 3600,
                    "token_type": "bearer",
                    "user": USER,
                },
            )
        return Response(200, json=USER)

    client = _client(handler, flow_type="pkce")
    client.refresh_session("refresh-token")

    client.update_user(
        {"email": "new@example.com"},
        {"email_redirect_to": "https://app/confirm"},
    )

    update = next(r for r in requests if r.method == "PUT")
    body = json.loads(update.content)
    assert body["email"] == "new@example.com"
    assert body["code_challenge_method"] == "s256"
    assert body["code_challenge"]
    assert update.url.params["redirect_to"] == "https://app/confirm"
    assert client._storage.get_item(f"{STORAGE_KEY}-code-verifier")
