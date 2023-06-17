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

def test_gotrue_signup_email_password(gotrue: SupabaseAuthClient):
    credentials = SignUpWithEmailAndPasswordCredentials(
        email = FAKER.email(),
        password = FAKER.password()
    )
    response: AuthResponse = gotrue.sign_up(credentials=credentials)
    assert response.user is not None, "Failed to sign up user with email & password!"

def test_gotrue_signin_email_password(gotrue: SupabaseAuthClient):
    credentials = SignInWithEmailAndPasswordCredentials(
        email=EMAIL,
        password=PASSWORD
    )
    response: AuthResponse = gotrue.sign_in_with_password(credentials=credentials)
    assert response.user is not None, "Failed to sign in user with email & password!"

# Turn off Row Level Security to pass this test.
def test_postgrest_RLS_OFF_select_table(postgrest: SyncPostgrestClient):
    response: APIResponse = postgrest.table("testing").select("*").execute()
    assert len(response.data) > 0, "Failed to select value from table with RLS OFF!"

# Row Level Security : remember to add policy to allow authenticated user to read the table.
# Follow guide line: https://supabase.com/docs/learn/auth-deep-dive/auth-row-level-security
def test_postgrest_RLS_ON_select_table(gotrue: SupabaseAuthClient, postgrest: SyncPostgrestClient):
    # Manually pass access token to postgrest to fullfill auth parameters 
    postgrest.auth(gotrue.get_session().access_token)
    response: APIResponse = postgrest.table("testing").select("*").execute()
    assert len(response.data) > 0, "Failed to select value from table with RLS ON!"
