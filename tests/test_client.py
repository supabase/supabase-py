from __future__ import annotations

from typing import Any
from faker import Faker

import pytest
from supabase import Client, create_client, SupabaseAuthClient
from gotrue import (
    AuthResponse, 
    SignUpWithEmailAndPasswordCredentials, 
    SignInWithEmailAndPasswordCredentials
)
from postgrest import (
    SyncPostgrestClient,
    AsyncPostgrestClient,
    APIResponse,
    APIError,
)

EMAIL='use.to.test.email@gmail.com'
PASSWORD='abc123ABC'
FAKER = Faker()

@pytest.mark.xfail(
    reason="None of these values should be able to instantiate a client object"
)
@pytest.mark.parametrize("url", ["", None, "valeefgpoqwjgpj", 139, -1, {}, []])
@pytest.mark.parametrize("key", ["", None, "valeefgpoqwjgpj", 139, -1, {}, []])
def test_incorrect_values_dont_instantiate_client(url: Any, key: Any) -> None:
    """Ensure we can't instantiate client with invalid values."""
    _: Client = create_client(url, key)

# def test_gotrue_signup_email_password(gotrue: SupabaseAuthClient):
#     credentials = SignUpWithEmailAndPasswordCredentials(
#         email = FAKER.email(),
#         password = FAKER.password()
#     )
#     response: AuthResponse = gotrue.sign_up(credentials=credentials)
#     assert response.user is not None, "Failed to sign up user with email & password!"

def test_gotrue_signin_email_password(gotrue: SupabaseAuthClient):
    credentials = SignInWithEmailAndPasswordCredentials(
        email=EMAIL,
        password=PASSWORD
    )
    response: AuthResponse = gotrue.sign_in_with_password(credentials=credentials)
    assert response.user is not None, "Failed to sign in user with email & password!"

@pytest.mark.xfail(raises=APIError)
def test_postgrest_select_table(gotrue: SupabaseAuthClient, postgrest: SyncPostgrestClient):
    response: APIResponse = postgrest.table("testing").select("*").execute()
    assert response.data is not None, "Failed to select value from table!"
    