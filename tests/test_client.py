from __future__ import annotations

import random
import string
from typing import TYPE_CHECKING, Any, Dict

import pytest

if TYPE_CHECKING:
    from supabase_py import Client, create_client


def _random_string(length: int = 10) -> str:
    """Generate random string."""
    return "".join(random.choices(string.ascii_uppercase + string.digits, k=length))


def _assert_authenticated_user(data: Dict[str, Any]) -> None:
    """Raise assertion error if user is not logged in correctly."""
    assert "access_token" in data
    assert "refresh_token" in data
    assert data.get("status_code") == 200
    user = data.get("user")
    assert user is not None
    assert user.get("id") is not None
    assert user.get("aud") == "authenticated"


@pytest.mark.xfail(
    reason="None of these values should be able to instanciate a client object"
)
@pytest.mark.parametrize("url", ["", None, "valeefgpoqwjgpj", 139, -1, {}, []])
@pytest.mark.parametrize("key", ["", None, "valeefgpoqwjgpj", 139, -1, {}, []])
def test_incorrect_values_dont_instanciate_client(url: Any, key: Any) -> None:
    """Ensure we can't instanciate client with nonesense values."""
    from supabase_py import Client, create_client

    _: Client = create_client(url, key)


def test_client_auth(supabase: Client) -> None:
    """Ensure we can create an auth user, and login with it."""
    # Create a random user login email and password.
    random_email: str = f"{_random_string(10)}@supamail.com"
    random_password: str = _random_string(20)
    # Sign up (and sign in).
    user = supabase.auth.sign_up(email=random_email, password=random_password)
    _assert_authenticated_user(user)
    # Sign out.
    supabase.auth.sign_out()
    assert supabase.auth.user() is None
    assert supabase.auth.session() is None
    # Sign in (explicitly this time).
    user = supabase.auth.sign_in(email=random_email, password=random_password)
    _assert_authenticated_user(user)


def test_client_select(supabase: Client) -> None:
    """Ensure we can select data from a table."""
    # TODO(fedden): Add this set back in (and expand on it) when postgrest and
    #               realtime libs are working.
    data = supabase.table("countries").select("*").execute()
    # Assert we pulled real data.
    assert len(data.get("data", [])) > 0


def test_client_insert(supabase: Client) -> None:
    """Ensure we can select data from a table."""
    data = supabase.table("countries").select("*").execute()
    # Assert we pulled real data.
    previous_length: int = len(data.get("data", []))
    new_row = {
        "name": "test name",
        "iso2": "test iso2",
        "iso3": "test iso3",
        "local_name": "test local name",
        "continent": None,
    }
    result = supabase.table("countries").insert(new_row).execute()
    data = supabase.table("countries").select("*").execute()
    current_length: int = len(data.get("data", []))
    # Ensure we've added a row remotely.
    assert current_length == previous_length + 1
    # Check returned result for insert was valid.
    assert result.get("status_code", 400) == 201
