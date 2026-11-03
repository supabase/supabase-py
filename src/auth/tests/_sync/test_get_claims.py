import base64
import json

import httpx
import pytest
from supabase_auth import SyncGoTrueClient
from supabase_auth.errors import AuthInvalidJwtError
from supabase_auth.types import JWKSet


def _client() -> SyncGoTrueClient:
    transport = httpx.MockTransport(lambda request: httpx.Response(500))
    return SyncGoTrueClient(
        url="http://localhost",
        http_client=httpx.Client(transport=transport),
        auto_refresh_token=False,
    )


def _segment(value: object) -> str:
    raw = value if isinstance(value, bytes) else json.dumps(value).encode()
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def test_get_claims_raises_auth_error_for_malformed_header() -> None:
    token = ".".join(
        [
            _segment({"alg": "none", "typ": "JWT"}),
            _segment({"sub": "user", "exp": 9999999999}),
            _segment(b"signature"),
        ]
    )

    with pytest.raises(AuthInvalidJwtError):
        _client().get_claims(jwt=token)


def test_fetch_jwks_skips_keys_without_kid() -> None:
    jwks: JWKSet = {"keys": [{"kty": "RSA"}, {"kty": "RSA", "kid": "signing-key"}]}

    jwk = _client()._fetch_jwks("signing-key", jwks)

    assert jwk == {"kty": "RSA", "kid": "signing-key"}
