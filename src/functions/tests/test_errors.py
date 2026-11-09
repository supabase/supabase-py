import pickle

import pytest
from supabase_utils.errors import SupabaseError
from supabase_utils.http.errors import SupabaseAPIError
from supabase_utils.http.headers import Headers
from supabase_utils.http.request import Request, Response
from yarl import URL

from supabase_functions.errors import (
    FunctionsError,
    FunctionsHttpError,
    FunctionsRelayError,
    _error_message_from,
    _on_error_response,
)


def make_response(
    content: bytes, status: int = 500, headers: Headers | None = None
) -> Response:
    return Response(
        headers=headers or Headers.empty(),
        content=content,
        status=status,
        request=Request(
            url=URL("https://example.com/test-function"),
            method="POST",
            headers=Headers.empty(),
            content=None,
            delay=None,
        ),
    )


def test_functions_error_is_a_supabase_error() -> None:
    error = FunctionsError("boom", code="x")
    assert isinstance(error, SupabaseError)
    assert not isinstance(error, SupabaseAPIError)
    assert str(error) == "boom"
    assert error.message == "boom"
    assert error.code == "x"


@pytest.mark.parametrize("error_class", [FunctionsHttpError, FunctionsRelayError])
def test_response_errors_are_api_errors(
    error_class: type[FunctionsHttpError | FunctionsRelayError],
) -> None:
    response = make_response(b"nope", status=502)
    error = error_class("Test error message", status_code=502, response=response)
    assert isinstance(error, FunctionsError)
    assert isinstance(error, SupabaseAPIError)
    assert str(error) == "Test error message"
    assert error.message == "Test error message"
    assert error.status_code == 502
    assert error.code is None
    assert error.response is response


def test_relay_error_is_not_an_http_error() -> None:
    assert not issubclass(FunctionsRelayError, FunctionsHttpError)
    assert not issubclass(FunctionsHttpError, FunctionsRelayError)


def test_errors_can_be_pickled() -> None:
    error = FunctionsHttpError("boom", status_code=404, response=make_response(b""))
    copy = pickle.loads(pickle.dumps(error))
    assert isinstance(copy, FunctionsHttpError)
    assert str(copy) == "boom"
    assert copy.status_code == 404
    assert copy.response is not None
    assert copy.response.status == 500


def test_error_message_types() -> None:
    # Test that errors handle different message types appropriately
    test_cases = [
        "Simple string",
        "String with unicode: 你好",
        "String with special chars: !@#$%^&*()",
        "",  # Empty string
        "A" * 1000,  # Long string
    ]

    for message in test_cases:
        error = FunctionsError(message)
        assert error.message == message


@pytest.mark.parametrize(
    ("content", "expected"),
    [
        (b'{"error": "boom"}', "boom"),
        (b'{"detail": "boom"}', '{"detail": "boom"}'),
        (b'{"code": "NOT_FOUND", "message": "missing"}', "missing"),
        (
            b'{"error": {"message": "bad", "field": "email"}}',
            '{"message":"bad","field":"email"}',
        ),
        (b'["boom"]', '["boom"]'),
        (b"plain boom", "plain boom"),
        (b"", None),
    ],
)
def test_error_message_from(content: bytes, expected: str | None) -> None:
    assert _error_message_from(make_response(content)) == expected


def test_on_error_response_http_error() -> None:
    error = _on_error_response(make_response(b'{"error": "boom"}', status=404))
    assert isinstance(error, FunctionsHttpError)
    assert error.message == "boom"
    assert error.status_code == 404
    assert error.response is not None
    assert error.response.status == 404


def test_on_error_response_http_error_fallback_message() -> None:
    error = _on_error_response(make_response(b"", status=500))
    assert isinstance(error, FunctionsHttpError)
    assert "https://example.com/test-function" in error.message


def test_on_error_response_relay_error_keeps_raw_text() -> None:
    error = _on_error_response(
        make_response(
            b'{"error": "relay"}',
            status=546,
            headers=Headers.from_mapping({"x-relay-error": "true"}),
        )
    )
    assert isinstance(error, FunctionsRelayError)
    assert error.message == '{"error": "relay"}'
    assert error.status_code == 546
