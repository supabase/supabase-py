from supabase_auth.errors import AuthError, UserDoesNotExistError


def test_user_does_not_exist_error_never_carries_the_token() -> None:
    error = UserDoesNotExistError()
    assert isinstance(error, AuthError)
    assert error.message == "User does not exist for the provided access token"
    assert error.code == "user_not_found"
    assert error.status == 404
    assert not hasattr(error, "access_token")
