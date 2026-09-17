from supabase_auth.errors import AuthError, UserDoesntExist


def test_user_doesnt_exist_never_carries_the_token() -> None:
    error = UserDoesntExist()
    assert isinstance(error, AuthError)
    assert str(error) == "User does not exist for the provided access token"
    assert error.args == ("User does not exist for the provided access token",)
    assert not hasattr(error, "access_token")
