from collections.abc import Callable
from dataclasses import dataclass, field
from time import time
from typing import Any

import pytest
from cryptography.hazmat.primitives.asymmetric import ec, ed25519, rsa
from httpx import Client, MockTransport, Request, Response
from jwt import encode
from jwt.algorithms import ECAlgorithm, OKPAlgorithm, RSAAlgorithm
from supabase_utils.http.adapters.httpx import HttpxSession

from supabase_auth import SyncSupabaseAuthClient
from supabase_auth.errors import AuthApiError, AuthInvalidJwtError

from .conftest import base64url_segment

PAYLOAD = base64url_segment({"sub": "user", "exp": 9999999999})
USER: dict[str, object] = {
    "id": "user",
    "aud": "authenticated",
    "user_metadata": {},
    "app_metadata": {},
    "created_at": "2024-01-01T00:00:00Z",
}

EC_KEY = ec.generate_private_key(ec.SECP256R1())
OTHER_EC_KEY = ec.generate_private_key(ec.SECP256R1())
RSA_KEY = rsa.generate_private_key(public_exponent=65537, key_size=2048)
ED25519_KEY = ed25519.Ed25519PrivateKey.generate()


def ec_jwk(kid: str, **extra: object) -> dict[str, Any]:
    jwk = ECAlgorithm.to_jwk(EC_KEY.public_key(), as_dict=True)
    return {**jwk, "kid": kid, **extra}


def rsa_jwk(kid: str) -> dict[str, Any]:
    return {**RSAAlgorithm.to_jwk(RSA_KEY.public_key(), as_dict=True), "kid": kid}


def ed25519_jwk(kid: str) -> dict[str, Any]:
    jwk = OKPAlgorithm.to_jwk(ED25519_KEY.public_key(), as_dict=True)
    return {**jwk, "kid": kid, "alg": "Ed25519"}


def claims(**extra: object) -> dict[str, object]:
    return {"sub": "user", "exp": int(time()) + 3600, **extra}


def token(
    key: ec.EllipticCurvePrivateKey | rsa.RSAPrivateKey | str = EC_KEY,
    algorithm: str = "ES256",
    kid: str | None = "key",
    payload: dict[str, object] | None = None,
) -> str:
    headers = {"kid": kid} if kid else None
    return encode(payload or claims(), key, algorithm=algorithm, headers=headers)


def ed25519_token(alg: str = "Ed25519") -> str:
    signing_input = (
        f"{base64url_segment({'alg': alg, 'kid': 'key'})}.{base64url_segment(claims())}"
    )
    signature = ED25519_KEY.sign(signing_input.encode())
    return f"{signing_input}.{base64url_segment(signature)}"


@dataclass
class Server:
    jwks: Callable[[], Response] = field(
        default_factory=lambda: lambda: Response(200, json={"keys": [ec_jwk("key")]})
    )
    user: Callable[[], Response] = field(
        default_factory=lambda: lambda: Response(200, json=USER)
    )
    requests: list[str] = field(default_factory=list)

    def handle(self, request: Request) -> Response:
        self.requests.append(request.url.path)
        if request.url.path == "/.well-known/jwks.json":
            return self.jwks()
        if request.url.path == "/user":
            return self.user()
        return Response(500)

    def client(self) -> SyncSupabaseAuthClient:
        return SyncSupabaseAuthClient(
            url="http://localhost",
            http_session=HttpxSession(
                client=Client(transport=MockTransport(self.handle))
            ),
            auto_refresh_token=False,
        )


def jwks(*keys: dict[str, Any]) -> Callable[[], Response]:
    return lambda: Response(200, json={"keys": list(keys)})


@pytest.mark.parametrize(
    "token",
    [
        "opaque-token",
        f"{base64url_segment({'typ': 'JWT'})}.not-json.sig",
        "é.é.é",
    ],
    ids=["opaque", "payload-not-json", "non-ascii"],
)
def test_get_claims_raises_auth_error_for_malformed_jwt(token: str) -> None:
    server = Server()

    with pytest.raises(AuthInvalidJwtError, match=r"Invalid JWT structure"):
        server.client().get_claims(token)

    assert server.requests == []


@pytest.mark.parametrize(
    ("jwt", "jwk"),
    [
        (token(EC_KEY, "ES256"), ec_jwk("key")),
        (token(RSA_KEY, "RS256"), rsa_jwk("key")),
        (ed25519_token("EdDSA"), ed25519_jwk("key")),
        (ed25519_token("Ed25519"), ed25519_jwk("key")),
    ],
    ids=["ES256", "RS256", "EdDSA", "Ed25519"],
)
def test_get_claims_verifies_asymmetric_tokens_locally(
    jwt: str, jwk: dict[str, Any]
) -> None:
    server = Server(jwks=jwks(jwk))

    response = server.client().get_claims(jwt)

    assert response is not None
    assert response.claims.sub == "user"
    assert server.requests == ["/.well-known/jwks.json"]


def test_get_claims_rejects_a_header_alg_that_does_not_name_the_jwk_algorithm() -> None:
    server = Server(jwks=jwks(rsa_jwk("key")))

    with pytest.raises(AuthInvalidJwtError, match="Invalid JWT signature"):
        server.client().get_claims(token(EC_KEY, "ES256"))

    assert "/user" not in server.requests


def test_get_claims_rejects_an_invalid_signature() -> None:
    server = Server()

    with pytest.raises(AuthInvalidJwtError, match="Invalid JWT signature"):
        server.client().get_claims(token(OTHER_EC_KEY))

    assert "/user" not in server.requests


@pytest.mark.parametrize(
    "jwt",
    [
        token("a-shared-secret-of-at-least-32-bytes", "HS256"),
        token(kid=None),
        token(ec.generate_private_key(ec.SECP384R1()), "ES384"),
        f"{base64url_segment({'kid': 'key'})}.{PAYLOAD}.sig",
    ],
    ids=["HS256", "no-kid", "unsupported-alg", "no-alg"],
)
def test_get_claims_falls_back_to_get_user_without_fetching_jwks(
    jwt: str,
) -> None:
    server = Server()

    response = server.client().get_claims(jwt)

    assert response is not None
    assert server.requests == ["/user"]


@pytest.mark.parametrize(
    "keys",
    [
        [],
        [ec_jwk("other")],
        [ec_jwk("key", alg="ES384")],
        [{"kty": "EC", "crv": "P-384", "kid": "key", "x": "AA", "y": "AA"}],
        [{"kty": "unknown", "kid": "key"}],
        [{"kty": "EC", "crv": "P-256", "kid": "key"}],
        [{"kty": "EC", "crv": "P-256", "kid": "key", "x": "AA", "y": "AA"}],
    ],
    ids=[
        "empty",
        "unknown-kid",
        "unsupported-jwk-alg",
        "unsupported-crv",
        "kty",
        "missing-coordinates",
        "point-not-on-curve",
    ],
)
def test_get_claims_falls_back_to_get_user_when_no_key_binds(
    keys: list[dict[str, Any]],
) -> None:
    server = Server(jwks=jwks(*keys))

    response = server.client().get_claims(token())

    assert response is not None
    assert response.claims.sub == "user"
    assert server.requests == ["/.well-known/jwks.json", "/user"]


def test_get_claims_surfaces_the_get_user_error_on_fallback() -> None:
    server = Server(
        user=lambda: Response(
            403, json={"code": 403, "error_code": "bad_jwt", "msg": "invalid JWT"}
        )
    )

    with pytest.raises(AuthApiError):
        server.client().get_claims(
            token("a-shared-secret-of-at-least-32-bytes", "HS256")
        )


def test_get_claims_surfaces_a_failed_jwks_download() -> None:
    server = Server(jwks=lambda: Response(500, json={"msg": "down"}))

    with pytest.raises(AuthApiError):
        server.client().get_claims(token())

    assert server.requests == ["/.well-known/jwks.json"]


def test_get_claims_rejects_expired_tokens() -> None:
    server = Server()

    with pytest.raises(AuthInvalidJwtError, match="JWT has expired"):
        server.client().get_claims(token(payload=claims(exp=int(time()) - 10)))

    assert server.requests == []


def test_get_claims_allow_expired_still_verifies_the_signature() -> None:
    server = Server()
    expired = claims(exp=int(time()) - 10)
    client = server.client()

    response = client.get_claims(token(payload=expired), allow_expired=True)

    assert response is not None
    assert response.claims.exp == expired["exp"]
    with pytest.raises(AuthInvalidJwtError, match="Invalid JWT signature"):
        client.get_claims(token(OTHER_EC_KEY, payload=expired), allow_expired=True)


def test_get_claims_rejects_tokens_that_are_not_yet_valid() -> None:
    server = Server()

    with pytest.raises(AuthInvalidJwtError, match="JWT is not yet valid"):
        server.client().get_claims(
            token(payload=claims(nbf=int(time()) + 60)), allow_expired=True
        )


def test_get_claims_refetches_jwks_for_a_rotated_key() -> None:
    keys = [ec_jwk("old")]
    server = Server(jwks=lambda: Response(200, json={"keys": keys}))
    client = server.client()
    client.get_claims(token(kid="old"))

    keys.append(ec_jwk("key"))
    response = client.get_claims(token())

    assert response is not None
    assert server.requests == ["/.well-known/jwks.json", "/.well-known/jwks.json"]
    assert client._jwks_refetch_wait == 0


def test_get_claims_backs_off_forced_jwks_refetches() -> None:
    server = Server()
    client = server.client()
    client.get_claims(token())
    server.requests.clear()

    client.get_claims(token(kid="unknown"))
    client.get_claims(token(kid="unknown"))

    assert server.requests == ["/.well-known/jwks.json", "/user", "/user"]
    assert client._jwks_refetch_wait == 1

    client._jwks_refetch_blocked_until = 0
    client.get_claims(token(kid="unknown"))
    assert client._jwks_refetch_wait == 2

    for _ in range(5):
        client._jwks_refetch_blocked_until = 0
        client.get_claims(token(kid="unknown"))
    assert client._jwks_refetch_wait == 16


def test_get_claims_backs_off_after_a_failed_forced_refetch() -> None:
    responses = [Response(200, json={"keys": [ec_jwk("key")]})]
    server = Server(
        jwks=lambda: responses.pop(0) if responses else Response(503, json={})
    )
    client = server.client()
    client.get_claims(token())

    with pytest.raises(AuthApiError):
        client.get_claims(token(kid="unknown"))

    assert client._jwks_refetch_wait == 1
    assert client._jwks.keys[0].kid == "key"
    response = client.get_claims(token(kid="unknown"))
    assert response is not None
    assert server.requests[-1] == "/user"
