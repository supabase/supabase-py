import time

import pytest
from jwt import encode

from supabase_auth import AsyncSupabaseAuthClient
from supabase_auth.errors import (
    AuthApiError,
    AuthInvalidJwtError,
    AuthSessionMissingError,
)
from supabase_auth.helpers import decode_jwt
from supabase_auth.types import (
    AuthChangeEvent,
    MFAEnroll,
    Session,
    SignInWithPassword,
    SignUpWithPassword,
)

from .conftest import (
    GOTRUE_JWT_SECRET,
    mock_user_credentials,
)


async def test_get_claims_returns_none_when_session_is_none(
    auth_client: AsyncSupabaseAuthClient,
) -> None:
    claims = await auth_client.get_claims()
    assert claims is None


async def test_get_claims_calls_get_user_if_symmetric_jwt(
    mocker, auth_client: AsyncSupabaseAuthClient
) -> None:
    spy = mocker.spy(auth_client.session_manager, "_get_user")
    credentials = mock_user_credentials()
    options = SignUpWithPassword.email(
        email=credentials.email,
        password=credentials.password,
    )
    user = (await auth_client.sign_up(options)).user

    assert user is not None

    response = await auth_client.get_claims()
    assert response
    claims = response.claims

    assert claims.model_extra
    assert claims.model_extra["email"] == user.email
    spy.assert_called_once()


async def test_get_claims_fetches_jwks_to_verify_asymmetric_jwt(
    mocker, auth_client_with_asymmetric_session: AsyncSupabaseAuthClient
) -> None:
    credentials = mock_user_credentials()
    options = SignUpWithPassword.email(
        email=credentials.email,
        password=credentials.password,
    )
    user = (await auth_client_with_asymmetric_session.sign_up(options)).user
    assert user is not None

    response = await auth_client_with_asymmetric_session.get_claims()
    assert response
    claims = response.claims

    assert claims.model_extra
    assert claims.model_extra["email"] == user.email

    expected_keyid = "638c54b8-28c2-4b12-9598-ba12ef610a29"

    assert len(auth_client_with_asymmetric_session._jwks.keys) == 1
    assert auth_client_with_asymmetric_session._jwks.keys[0].kid == expected_keyid


async def test_jwks_ttl_cache_behavior(
    mocker, auth_client_with_asymmetric_session: AsyncSupabaseAuthClient
) -> None:
    spy = mocker.spy(auth_client_with_asymmetric_session.executor.session, "send")

    # First call should fetch JWKS from endpoint
    credentials = mock_user_credentials()
    options = SignUpWithPassword.email(
        email=credentials.email,
        password=credentials.password,
    )
    user = (await auth_client_with_asymmetric_session.sign_up(options)).user
    assert user is not None

    await auth_client_with_asymmetric_session.get_claims()

    first_call_count = spy.call_count

    # Second call within TTL should use cache
    await auth_client_with_asymmetric_session.get_claims()
    assert spy.call_count == first_call_count  # No additional JWKS request

    # Mock time to be after TTL expiry
    original_time = time.time
    try:
        mock_time = mocker.patch("time.time")
        mock_time.return_value = original_time() + 601  # TTL is 600 seconds

        # Call after TTL expiry should fetch fresh JWKS
        await auth_client_with_asymmetric_session.get_claims()
        assert spy.call_count == first_call_count + 1  # One more JWKS request
    finally:
        # Restore original time function
        mocker.patch("time.time", original_time)


async def test_set_session_with_valid_tokens(
    auth_client: AsyncSupabaseAuthClient,
) -> None:
    credentials = mock_user_credentials()

    # First sign up to get valid tokens
    signup_response = await auth_client.sign_up(
        SignUpWithPassword.email(email=credentials.email, password=credentials.password)
    )
    assert signup_response.session is not None

    # Get the tokens from the signup response
    access_token = signup_response.session.access_token
    refresh_token = signup_response.session.refresh_token

    # Clear the session
    await auth_client.session_manager.remove_session()

    # Set the session with the tokens
    response = await auth_client.set_session(access_token, refresh_token)

    # Verify the response
    assert response.session is not None
    assert response.session.access_token == access_token
    assert response.session.refresh_token == refresh_token
    assert response.user is not None
    assert response.user.email == credentials.email


async def test_set_session_with_expired_token(
    auth_client: AsyncSupabaseAuthClient,
) -> None:
    credentials = mock_user_credentials()

    # First sign up to get valid tokens
    signup_response = await auth_client.sign_up(
        SignUpWithPassword.email(email=credentials.email, password=credentials.password)
    )
    assert signup_response.session is not None

    # Get the tokens from the signup response
    access_token = signup_response.session.access_token
    refresh_token = signup_response.session.refresh_token

    # Clear the session
    await auth_client.session_manager.remove_session()

    # Create an expired token by modifying the JWT
    expired_token = access_token.split(".")
    payload = decode_jwt(access_token).payload
    payload.exp = int(time.time()) - 3600  # Set expiry to 1 hour ago
    expired_token[1] = encode(
        dict(payload), GOTRUE_JWT_SECRET, algorithm="HS256"
    ).split(".")[1]
    expired_access_token = ".".join(expired_token)

    # Set the session with the expired token
    response = await auth_client.set_session(expired_access_token, refresh_token)

    # Verify the response has a new access token (refreshed)
    assert response.session is not None
    assert response.session.access_token != expired_access_token
    assert response.session.refresh_token != refresh_token
    assert response.user is not None
    assert response.user.email == credentials.email


async def test_set_session_without_refresh_token(
    auth_client: AsyncSupabaseAuthClient,
) -> None:
    credentials = mock_user_credentials()

    # First sign up to get valid tokens
    signup_response = await auth_client.sign_up(
        SignUpWithPassword.email(email=credentials.email, password=credentials.password)
    )
    assert signup_response.session is not None

    # Get the access token from the signup response
    access_token = signup_response.session.access_token

    # Clear the session
    await auth_client.session_manager.remove_session()

    # Create an expired token
    expired_token = access_token.split(".")
    payload = decode_jwt(access_token).payload
    payload.exp = int(time.time()) - 3600  # Set expiry to 1 hour ago
    expired_token[1] = encode(
        dict(payload), GOTRUE_JWT_SECRET, algorithm="HS256"
    ).split(".")[1]
    expired_access_token = ".".join(expired_token)

    # Try to set the session with an expired token but no refresh token
    with pytest.raises(AuthSessionMissingError):
        await auth_client.set_session(expired_access_token, "")


async def test_set_session_with_invalid_token(
    auth_client: AsyncSupabaseAuthClient,
) -> None:
    # Try to set the session with invalid tokens
    with pytest.raises(AuthInvalidJwtError):
        await auth_client.set_session("invalid.token.here", "invalid_refresh_token")


async def test_mfa_enroll(auth_client_with_session: AsyncSupabaseAuthClient) -> None:
    credentials = mock_user_credentials()

    # First sign up to get a valid session
    _signup_response = await auth_client_with_session.sign_up(
        SignUpWithPassword.email(email=credentials.email, password=credentials.password)
    )
    # Test MFA enrollment
    enroll_response = await auth_client_with_session.mfa.enroll(
        MFAEnroll.totp(issuer="test-issuer", friendly_name="test-factor")
    )

    assert enroll_response.id is not None
    assert enroll_response.type == "totp"
    assert enroll_response.friendly_name == "test-factor"
    assert enroll_response.totp
    assert enroll_response.totp.qr_code is not None


async def test_mfa_challenge(auth_client: AsyncSupabaseAuthClient) -> None:
    credentials = mock_user_credentials()

    # First sign up to get a valid session
    signup_response = await auth_client.sign_up(
        SignUpWithPassword.email(email=credentials.email, password=credentials.password)
    )
    assert signup_response.session is not None

    # Enroll a factor first
    enroll_response = await auth_client.mfa.enroll(
        MFAEnroll.totp(issuer="test-issuer", friendly_name="test-factor")
    )

    # Test MFA challenge
    challenge_response = await auth_client.mfa.challenge(factor_id=enroll_response.id)
    assert challenge_response.id is not None
    assert challenge_response.expires_at is not None


async def test_mfa_unenroll(auth_client: AsyncSupabaseAuthClient) -> None:
    credentials = mock_user_credentials()

    # First sign up to get a valid session
    signup_response = await auth_client.sign_up(
        SignUpWithPassword.email(email=credentials.email, password=credentials.password)
    )
    assert signup_response.session is not None

    # Enroll a factor first
    enroll_response = await auth_client.mfa.enroll(
        MFAEnroll.totp(issuer="test-issuer", friendly_name="test-factor")
    )

    # Test MFA unenroll
    unenroll_response = await auth_client.mfa.unenroll(factor_id=enroll_response.id)
    assert unenroll_response.id == enroll_response.id


async def test_mfa_list_factors(auth_client: AsyncSupabaseAuthClient) -> None:
    credentials = mock_user_credentials()

    # First sign up to get a valid session
    signup_response = await auth_client.sign_up(
        SignUpWithPassword.email(email=credentials.email, password=credentials.password)
    )
    assert signup_response.session is not None

    # Enroll a factor first
    await auth_client.mfa.enroll(
        MFAEnroll.totp(issuer="test-issuer", friendly_name="test-factor")
    )

    # Test MFA list factors
    list_response = await auth_client.mfa.list_factors()
    assert len(list_response.all) == 1


async def test_get_authenticator_assurance_level(
    auth_client: AsyncSupabaseAuthClient,
) -> None:
    credentials = mock_user_credentials()

    # Without a session, should return null values
    aal_response = await auth_client.mfa.get_authenticator_assurance_level()
    assert aal_response.current_level is None
    assert aal_response.next_level is None
    assert aal_response.current_authentication_methods == []

    # Sign up to get a valid session
    signup_response = await auth_client.sign_up(
        SignUpWithPassword.email(email=credentials.email, password=credentials.password)
    )
    assert signup_response.session is not None

    # With a session, should return authentication methods
    aal_response = await auth_client.mfa.get_authenticator_assurance_level()
    # Basic auth will have password as an authentication method
    assert aal_response.current_authentication_methods is not None


async def test_get_user_identities(auth_client: AsyncSupabaseAuthClient) -> None:
    credentials = mock_user_credentials()

    # Sign up to get a valid session
    signup_response = await auth_client.sign_up(
        SignUpWithPassword.email(email=credentials.email, password=credentials.password)
    )
    assert signup_response.session is not None

    # New users won't have any identities yet, but the call should work
    identities_response = await auth_client.get_user_identities()
    assert identities_response is not None
    # For a new user, identities will be an empty list or None
    assert hasattr(identities_response, "identities")


async def test_sign_in_with_password(auth_client: AsyncSupabaseAuthClient) -> None:
    credentials = mock_user_credentials()

    # First create a user we can sign in with
    signup_response = await auth_client.sign_up(
        SignUpWithPassword.email(email=credentials.email, password=credentials.password)
    )
    assert signup_response.session is not None

    # Test signing in with the same credentials (email)
    signin_response = await auth_client.sign_in_with_password(
        SignInWithPassword.email(
            email=credentials.email,
            password=credentials.password,
        )
    )

    # Verify the response has a valid session and user
    assert signin_response.session is not None
    assert signin_response.user is not None
    assert signin_response.user.email == credentials.email

    try:
        await auth_client.sign_in_with_password(
            SignInWithPassword.email(
                email=credentials.email,
                password="wrong_password",
            )
        )
        raise AssertionError("Expected AuthApiError for wrong password")
    except AuthApiError:
        pass


async def test_sign_out(auth_client: AsyncSupabaseAuthClient) -> None:
    credentials = mock_user_credentials()

    signup_response = await auth_client.sign_up(
        SignUpWithPassword.email(email=credentials.email, password=credentials.password)
    )
    assert signup_response.session is not None

    signin_response = await auth_client.sign_in_with_password(
        SignInWithPassword.email(
            email=credentials.email,
            password=credentials.password,
        )
    )

    # Verify the response has a valid session and user
    assert signin_response.session is not None
    assert signin_response.user is not None
    assert signin_response.user.email == credentials.email

    called = False

    def sign_out_callback(auth_event: AuthChangeEvent, session: Session | None) -> None:
        nonlocal called
        called = True

    auth_client.on_auth_state_change(sign_out_callback)

    await auth_client.sign_out()

    no_more_session = await auth_client.get_session()
    assert no_more_session is None
    assert called
