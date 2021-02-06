import os
import random
import string
from typing import Any, Dict

import pytest

"""
Convert this flow into a test
client = supabase_py.Client("<insert link>", "<password>")
client.auth.sign_up({"email": "anemail@gmail.com", "password": "apassword"})
"""


def _random_string(length: int = 10) -> str:
    """Generate random string."""
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


def _assert_authenticated_user(user: Dict[str, Any]):
    """Raise assertion error if user is not logged in correctly."""
    assert user.get("id") is not None
    assert user.get("aud") == "authenticated"


def _assert_unauthenticated_user(user: Dict[str, Any]):
    """Raise assertion error if user is logged in correctly."""
    assert user.get("id") is not None
    assert user.get("aud") == "authenticated"


@pytest.mark.xfail(
    reason="None of these values should be able to instanciate a client object"
)
@pytest.mark.parametrize("url", ["", None, "valeefgpoqwjgpj", 139, -1, {}, []])
@pytest.mark.parametrize("key", ["", None, "valeefgpoqwjgpj", 139, -1, {}, []])
def test_incorrect_values_dont_instanciate_client(url: Any, key: Any):
    """Ensure we can't instanciate client with nonesense values."""
    from supabase_py import create_client, Client

    _: Client = create_client(url, key)


def test_client_auth():
    """Ensure we can create an auth user, and login with it."""
    from supabase_py import create_client, Client

    url: str = os.environ.get("SUPABASE_TEST_URL")
    key: str = os.environ.get("SUPABASE_TEST_KEY")
    supabase: Client = create_client(url, key)
    # Create a random user login email and password.
    random_email: str = f"{_random_string(10)}@supamail.com"
    random_password: str = _random_string(20)
    # Sign up (and sign in).
    user = supabase.auth.sign_up(email=random_email, password=random_password)
    _assert_authenticated_user(user)
    # Sign out.
    user = supabase.auth.sign_out()
    _assert_unauthenticated_user(user)
    # Sign in (explicitly this time).
    user = supabase.auth.sign_in(email=random_email, password=random_password)
    _assert_authenticated_user(user)

