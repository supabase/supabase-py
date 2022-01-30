from __future__ import annotations

import random
import string
from typing import TYPE_CHECKING, Any, Union

import pytest
from gotrue import Session, User

if TYPE_CHECKING:
    from supabase import Client


def _random_string(length: int = 10) -> str:
    """Generate random string."""
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


def _assert_authenticated_user(data: Union[Session, User, str, None]) -> None:
    """Raise assertion error if user is not logged in correctly."""
    assert data is not None
    assert isinstance(data, Session)
    assert data.user is not None
    assert data.user.aud == "authenticated"


@pytest.mark.xfail(
    reason="None of these values should be able to instanciate a client object"
)
@pytest.mark.parametrize("url", ["", None, "valeefgpoqwjgpj", 139, -1, {}, []])
@pytest.mark.parametrize("key", ["", None, "valeefgpoqwjgpj", 139, -1, {}, []])
def test_incorrect_values_dont_instanciate_client(url: Any, key: Any) -> None:
    """Ensure we can't instanciate client with nonesense values."""
    from supabase import Client, create_client

    _: Client = create_client(url, key)


@pytest.mark.skip(reason="TO FIX: Session does not terminate with test included.")
def test_client_auth(supabase: Client) -> None:
    """Ensure we can create an auth user, and login with it."""
    # Create a random user login email and password.
    random_email = f"{_random_string(10)}@supamail.com"
    random_password = _random_string(20)
    # Sign up (and sign in).
    user = supabase.auth.sign_up(
        email=random_email,
        password=random_password,
        phone=None,
    )
    _assert_authenticated_user(user)
    # Sign out.
    supabase.auth.sign_out()
    assert supabase.auth.user() is None
    assert supabase.auth.session() is None
    # Sign in (explicitly this time).
    user = supabase.auth.sign_in(email=random_email, password=random_password)
    _assert_authenticated_user(user)
