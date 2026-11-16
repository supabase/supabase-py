import base64
import json
from datetime import UTC, datetime
from typing import Any

import pytest
from supabase_utils.http.headers import Headers
from supabase_utils.http.request import Request, Response
from yarl import URL

from supabase_auth.client import _append_flow_id, _parse_url_params
from supabase_auth.errors import (
    AuthApiError,
    AuthInvalidJwtError,
    AuthRetryableError,
    AuthUnknownError,
    AuthWeakPasswordError,
    ErrorCode,
)
from supabase_auth.helpers import (
    _handle_error_response,
    decode_jwt,
    generate_pkce_challenge,
    generate_pkce_verifier,
    parse_jwks,
    parse_link_identity_response,
    validate_expiration,
)
from supabase_auth.types import AMREntry, JWTPayload

from ._sync.conftest import mock_access_token

TEST_URL = "http://localhost"


def valid_request() -> Request:
    return Request(
        url=URL(TEST_URL),
        method="GET",
        headers=Headers.empty(),
        content=None,
        delay=None,
    )


def test_parse_link_identity_response() -> None:
    resp = Response(
        content=f'{{"url": "{TEST_URL}/hello-world"}}'.encode(),
        status=200,
        headers=Headers.empty(),
        request=valid_request(),
    )
    assert parse_link_identity_response(resp)


def test_parse_jwks_raises_the_api_error_of_an_error_response() -> None:
    response = error_response(
        401, {"code": 401, "error_code": "no_authorization", "msg": "denied"}
    )

    with pytest.raises(AuthApiError) as exc_info:
        parse_jwks(response)

    assert exc_info.value.message == "denied"
    assert exc_info.value.status_code == 401
    assert exc_info.value.code is ErrorCode.NO_AUTHORIZATION


def test_parse_jwks_accepts_an_empty_key_set() -> None:
    assert parse_jwks(error_response(200, {"keys": []})).keys == []


def test_decode_jwt() -> None:
    assert decode_jwt(mock_access_token())

    with pytest.raises(AuthInvalidJwtError, match=r"Invalid JWT structure") as exc:
        decode_jwt("non-valid-jwt")
    assert exc.value is not None


def _segment(value: object) -> str:
    raw = value if isinstance(value, bytes) else json.dumps(value).encode()
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode()


def _token(header: object, payload: object) -> str:
    return f"{_segment(header)}.{_segment(payload)}.{_segment(b'signature')}"


_HEADER = {"alg": "HS256", "typ": "JWT"}
_PAYLOAD = {"sub": "user", "exp": 9999999999}


@pytest.mark.parametrize(
    "token",
    [
        _token(b"not json", _PAYLOAD),
        _token(_HEADER, b"not json"),
        _token([_HEADER], _PAYLOAD),
        _token(_HEADER, {"sub": "user", "exp": "soon"}),
        "a.b.c",
        "\u00e9.\u00e9.\u00e9",
        f"{_segment(_HEADER)}.{_segment(_PAYLOAD)}.a",
    ],
    ids=[
        "header-not-json",
        "payload-not-json",
        "header-array",
        "exp-string",
        "undecodable-base64",
        "non-ascii",
        "undecodable-signature",
    ],
)
def test_decode_jwt_raises_auth_error_for_malformed_segments(token: str) -> None:
    with pytest.raises(AuthInvalidJwtError, match=r"Invalid JWT structure"):
        decode_jwt(token)


@pytest.mark.parametrize("alg", ["none", "EdDSA", "PS512", None])
def test_decode_jwt_reads_alg_as_an_opaque_string(alg: str | None) -> None:
    header = {"typ": "JWT"} if alg is None else {"alg": alg, "typ": "JWT"}

    assert decode_jwt(_token(header, _PAYLOAD)).header.alg == alg


def test_decode_jwt_accepts_header_without_typ() -> None:
    decoded = decode_jwt(_token({"alg": "HS256"}, _PAYLOAD))

    assert decoded.header.alg == "HS256"
    assert decoded.header.typ is None
    assert decoded.payload.sub == "user"
    assert decoded.payload.exp == 9999999999


def test_jwt_payload_parses_amr_entries_into_models() -> None:
    payload = JWTPayload.model_validate(
        {"amr": [{"method": "password", "timestamp": 1700000000}]}
    )

    assert payload.amr == [AMREntry(method="password", timestamp=1700000000)]


def test_generate_pkce_verifier() -> None:
    assert isinstance(generate_pkce_verifier(45), str)
    with pytest.raises(
        ValueError, match=r"PKCE verifier length must be between 43 and 128 characters"
    ) as exc:
        generate_pkce_verifier(42)
    assert exc.value is not None


def test_generate_pkce_challenge() -> None:
    pkce = generate_pkce_verifier(45)
    assert isinstance(generate_pkce_challenge(pkce), str)


def test_validate_expiration_with_expired_timestamp() -> None:
    # Set expiry to 1 hour ago
    exp = int(datetime.now(UTC).timestamp()) - 3600

    with pytest.raises(AuthInvalidJwtError, match="JWT has expired"):
        validate_expiration(exp)


def test_validate_expiration_with_valid_timestamp() -> None:
    # Set expiry to 1 hour in the future
    exp = int(datetime.now(UTC).timestamp()) + 3600

    # Should not raise an exception
    validate_expiration(exp)


def test_is_http_url() -> None:
    from supabase_auth.helpers import is_http_url

    # Test valid HTTP URLs
    assert is_http_url("http://example.com") is True
    assert is_http_url("https://example.com") is True
    assert is_http_url("https://example.com/path?query=value#fragment") is True

    # Test invalid URLs
    assert is_http_url("ftp://example.com") is False
    assert is_http_url("file:///path/to/file.txt") is False
    assert is_http_url("example.com") is False  # Missing scheme
    assert is_http_url("") is False
    assert is_http_url("not a url") is False


def error_response(status: int, body: Any) -> Response:
    return Response(
        headers=Headers.empty(),
        content=json.dumps(body).encode(),
        status=status,
        request=valid_request(),
    )


def test_handle_error_response_legacy_weak_password_without_error_code() -> None:
    result = _handle_error_response(
        error_response(
            422,
            {
                "message": "Password too weak",
                "weak_password": {"reasons": ["length", "characters"]},
            },
        )
    )

    assert isinstance(result, AuthWeakPasswordError)
    assert result.message == "Password too weak"
    assert result.status_code == 422
    assert result.reasons == ["length", "characters"]


@pytest.mark.parametrize(
    "weak_password",
    [
        {"reasons": []},
        {"reasons": "length"},
        {"reasons": ["length", 1]},
        {},
        "length",
    ],
)
def test_handle_error_response_legacy_weak_password_ignores_malformed_reasons(
    weak_password: Any,
) -> None:
    result = _handle_error_response(
        error_response(
            422,
            {"message": "Password too weak", "weak_password": weak_password},
        )
    )

    assert isinstance(result, AuthApiError)
    assert not isinstance(result, AuthWeakPasswordError)
    assert result.message == "Password too weak"
    assert result.status_code == 422


def test_handle_error_response_weak_password_with_error_code() -> None:
    result = _handle_error_response(
        error_response(
            422,
            {
                "message": "Password too weak",
                "error_code": "weak_password",
                "weak_password": {"reasons": ["length"]},
            },
        )
    )

    assert isinstance(result, AuthWeakPasswordError)
    assert result.reasons == ["length"]


def test_handle_error_response_parses_a_known_error_code() -> None:
    response = Response(
        content=b'{"code": 400, "error_code": "refresh_token_not_found", "msg": "gone"}',
        status=400,
        headers=Headers.empty(),
        request=valid_request(),
    )

    error = _handle_error_response(response)

    assert isinstance(error, AuthApiError)
    assert error.code is ErrorCode.REFRESH_TOKEN_NOT_FOUND
    assert error.code == "refresh_token_not_found"


def test_handle_error_response_passes_an_unknown_error_code_through() -> None:
    response = Response(
        content=b'{"code": 400, "error_code": "brand_new_code", "msg": "new"}',
        status=400,
        headers=Headers.empty(),
        request=valid_request(),
    )

    error = _handle_error_response(response)

    assert isinstance(error, AuthApiError)
    assert not isinstance(error.code, ErrorCode)
    assert error.code == "brand_new_code"


@pytest.mark.parametrize("status", [429, 502, 503, 504, 520])
@pytest.mark.parametrize("content", [b"", b"<html>Service Unavailable</html>"])
def test_handle_error_response_retries_a_retryable_status_whatever_the_body(
    status: int, content: bytes
) -> None:
    response = Response(
        content=content,
        status=status,
        headers=Headers.empty(),
        request=valid_request(),
    )

    error = _handle_error_response(response)

    assert isinstance(error, AuthRetryableError)
    assert error.status_code == status
    assert error.code is ErrorCode.UNEXPECTED_FAILURE


def test_handle_error_response_keeps_the_message_of_a_retryable_error() -> None:
    response = Response(
        content=b'{"msg": "upstream unavailable"}',
        status=503,
        headers=Headers.empty(),
        request=valid_request(),
    )

    error = _handle_error_response(response)

    assert isinstance(error, AuthRetryableError)
    assert error.message == "upstream unavailable"
    assert error.status_code == 503
    assert error.code is None


def test_handle_error_response_keeps_an_unparsable_client_error_unknown() -> None:
    response = Response(
        content=b"<html>404 Not Found</html>",
        status=404,
        headers=Headers.empty(),
        request=valid_request(),
    )

    error = _handle_error_response(response)

    assert isinstance(error, AuthUnknownError)
    assert error.status_code == 404


@pytest.mark.parametrize(
    ("redirect_to", "expected"),
    [
        (
            "https://app.example/callback",
            "https://app.example/callback?sb_flow_id=abcdef0123456789",
        ),
        (
            "https://app.example/callback?next=%2Fhome&a=b+c",
            "https://app.example/callback?next=%2Fhome&a=b+c&sb_flow_id=abcdef0123456789",
        ),
        (
            "https://app.example/callback?sb_flow_id=old&next=1#section",
            "https://app.example/callback?next=1&sb_flow_id=abcdef0123456789#section",
        ),
        (
            "myapp://login-callback/?",
            "myapp://login-callback/?sb_flow_id=abcdef0123456789",
        ),
        (
            "https://app.example/callback#a?b",
            "https://app.example/callback?sb_flow_id=abcdef0123456789#a?b",
        ),
    ],
)
def test_append_flow_id(redirect_to: str, expected: str) -> None:
    assert _append_flow_id(redirect_to, "abcdef0123456789") == expected


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        pytest.param(
            "https://app.example/callback#access_token=a&refresh_token=r",
            {"access_token": "a", "refresh_token": "r"},
            id="fragment",
        ),
        pytest.param(
            "https://app.example/callback?access_token=a&refresh_token=r",
            {"access_token": "a", "refresh_token": "r"},
            id="query",
        ),
        pytest.param(
            "https://app.example/callback?access_token=q#access_token=f&type=recovery",
            {"access_token": "q", "type": "recovery"},
            id="query-wins-over-fragment",
        ),
        pytest.param(
            "https://app.example/callback#error_description=Email+link+is%20invalid",
            {"error_description": "Email link is invalid"},
            id="fragment-is-decoded",
        ),
        pytest.param(
            "https://app.example/callback#provider_token=abc%2Bdef%3D&error_description=a%26b",
            {"provider_token": "abc+def=", "error_description": "a&b"},
            id="fragment-is-decoded-once",
        ),
        pytest.param(
            "https://app.example/callback?provider_token=abc%2Bdef%3D&error_description=a%26b",
            {"provider_token": "abc+def=", "error_description": "a&b"},
            id="query-is-decoded-once",
        ),
        pytest.param(
            "https://app.example/callback?access_token=#access_token=f",
            {"access_token": "f"},
            id="blank-values-are-dropped",
        ),
        pytest.param(
            "myapp://login-callback/#access_token=a",
            {"access_token": "a"},
            id="custom-scheme",
        ),
        pytest.param("https://app.example/callback", {}, id="no-parameters"),
    ],
)
def test_parse_url_params(url: str, expected: dict[str, str]) -> None:
    assert _parse_url_params(url) == expected
