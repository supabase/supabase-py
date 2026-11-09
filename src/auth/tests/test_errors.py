import pickle

from supabase_utils.errors import SupabaseError
from supabase_utils.http.errors import SupabaseAPIError
from supabase_utils.http.headers import Headers
from supabase_utils.http.request import Request, Response
from yarl import URL

from supabase_auth.errors import (
    AuthApiError,
    AuthError,
    AuthImplicitGrantRedirectError,
    AuthInvalidCredentialsError,
    AuthInvalidJwtError,
    AuthRetryableError,
    AuthSessionMissingError,
    AuthUnknownError,
    AuthWeakPasswordError,
    CustomAuthError,
    UserDoesNotExistError,
)


def make_response(status: int, content: bytes = b"{}") -> Response:
    return Response(
        headers=Headers.empty(),
        content=content,
        status=status,
        request=Request(
            url=URL("https://example.com/auth/v1/token"),
            method="POST",
            headers=Headers.empty(),
            content=None,
            delay=None,
        ),
    )


def test_user_does_not_exist_error_never_carries_the_token() -> None:
    error = UserDoesNotExistError()
    assert isinstance(error, AuthError)
    assert error.message == "User does not exist for the provided access token"
    assert str(error) == error.message
    assert error.code == "user_not_found"
    assert not hasattr(error, "access_token")


def test_auth_error_is_a_supabase_error() -> None:
    assert issubclass(AuthError, SupabaseError)
    assert not issubclass(AuthError, SupabaseAPIError)


def test_client_side_errors_are_not_api_errors() -> None:
    for error in (
        AuthSessionMissingError(),
        AuthInvalidCredentialsError("bad"),
        AuthImplicitGrantRedirectError("bad url", error="e", code="c"),
        AuthInvalidJwtError("bad jwt"),
        UserDoesNotExistError(),
    ):
        assert isinstance(error, CustomAuthError)
        assert not isinstance(error, SupabaseAPIError)
        assert str(error) == error.message


def test_api_error_carries_the_response() -> None:
    response = make_response(400, b'{"msg": "Invalid login"}')
    error = AuthApiError(
        "Invalid login",
        status_code=400,
        code="invalid_credentials",
        response=response,
    )
    assert isinstance(error, SupabaseAPIError)
    assert str(error) == "Invalid login"
    assert error.status_code == 400
    assert error.code == "invalid_credentials"
    assert error.response is response


def test_retryable_and_weak_password_errors_are_api_errors() -> None:
    retryable = AuthRetryableError("down", status_code=503)
    weak = AuthWeakPasswordError("weak", status_code=422, reasons=["length"])
    assert isinstance(retryable, AuthApiError)
    assert retryable.code is None
    assert isinstance(weak, AuthApiError)
    assert weak.code == "weak_password"
    assert weak.reasons == ["length"]


def test_unknown_error_keeps_the_body_on_the_response() -> None:
    response = make_response(500, b"<html>")
    error = AuthUnknownError(
        "Unexpected error",
        status_code=500,
        code="unexpected_failure",
        response=response,
    )
    assert isinstance(error, SupabaseAPIError)
    assert error.response is not None
    assert error.response.content == b"<html>"


def test_errors_can_be_pickled() -> None:
    weak = AuthWeakPasswordError("weak", status_code=422, reasons=["length"])
    copy = pickle.loads(pickle.dumps(weak))
    assert isinstance(copy, AuthWeakPasswordError)
    assert str(copy) == "weak"
    assert copy.status_code == 422
    assert copy.reasons == ["length"]
    assert isinstance(
        pickle.loads(pickle.dumps(AuthSessionMissingError())), AuthSessionMissingError
    )
