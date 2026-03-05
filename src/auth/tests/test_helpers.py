from datetime import datetime
from unittest.mock import MagicMock, patch

import pytest
from httpx import Headers, Response

from supabase_auth.constants import (
    API_VERSION_HEADER_NAME,
)
from supabase_auth.errors import (
    AuthInvalidJwtError,
    AuthWeakPasswordError,
)
from supabase_auth.helpers import (
    decode_jwt,
    generate_pkce_challenge,
    generate_pkce_verifier,
    handle_error_response,
    parse_link_identity_response,
    parse_response_api_version,
    validate_exp,
)

from ._sync.clients import mock_access_token

TEST_URL = "http://localhost"


def test_parse_response_api_version_with_valid_date() -> None:
    headers = Headers({API_VERSION_HEADER_NAME: "2024-01-01"})
    response = Response(headers=headers, status_code=200)
    api_ver = parse_response_api_version(response)
    assert api_ver
    assert datetime.timestamp(api_ver) == datetime.timestamp(
        datetime.strptime("2024-01-01", "%Y-%m-%d")
    )


def test_parse_response_api_version_with_invalid_dates() -> None:
    dates = ["2024-01-32", "", "notadate", "Sat Feb 24 2024 17:59:17 GMT+0100"]
    for date in dates:
        headers = Headers({API_VERSION_HEADER_NAME: date})
        response = Response(headers=headers, status_code=200)
        api_ver = parse_response_api_version(response)
        assert api_ver is None


def test_parse_link_identity_response() -> None:
    resp = Response(content=f'{{"url": "{TEST_URL}/hello-world"}}', status_code=200)
    assert parse_link_identity_response(resp)


def test_decode_jwt() -> None:
    assert decode_jwt(mock_access_token())

    with pytest.raises(AuthInvalidJwtError, match=r"Invalid JWT structure") as exc:
        decode_jwt("non-valid-jwt")
    assert exc.value is not None


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


def test_parse_response_api_version_invalid_date() -> None:
    mock_response = MagicMock(spec=Response)
    mock_response.headers = {API_VERSION_HEADER_NAME: "2023-02-30"}  # Invalid date

    result = parse_response_api_version(mock_response)
    assert result is None


def test_handle_exception_with_new_api_version() -> None:
    # Test case for new API version with "code" field
    mock_response = MagicMock(spec=Response)
    mock_response.status_code = 400
    mock_response.content = b"""{
        "message": "Password too weak",
        "error_code": "weak_password",
        "weak_password": {"reasons": ["Password too simple"]}
    }"""

    # Mock datetime for January 2, 2024 (after 2024-01-01 API version)
    mock_date = datetime(2024, 1, 2)

    with patch(
        "supabase_auth.helpers.parse_response_api_version", return_value=mock_date
    ):
        result = handle_error_response(mock_response)

        assert isinstance(result, AuthWeakPasswordError)
        assert result.message == "Password too weak"
        assert result.status == 400


def test_validate_exp_with_expired_exp() -> None:
    # Set expiry to 1 hour ago
    exp = int(datetime.now().timestamp()) - 3600

    with pytest.raises(AuthInvalidJwtError, match="JWT has expired"):
        validate_exp(exp)


def test_validate_exp_with_valid_exp() -> None:
    # Set expiry to 1 hour in the future
    exp = int(datetime.now().timestamp()) + 3600

    # Should not raise an exception
    validate_exp(exp)


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
