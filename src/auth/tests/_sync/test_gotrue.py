import time

import pytest
from jwt import encode

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

from .clients import (
    GOTRUE_JWT_SECRET,
    auth_client,
    auth_client_with_asymmetric_session,
    auth_client_with_session,
    mock_user_credentials,
)


def test_get_claims_returns_none_when_session_is_none() -> None:
    claims = auth_client().get_claims()
    assert claims is None


def test_get_claims_calls_get_user_if_symmetric_jwt(mocker) -> None:
    client = auth_client()
    spy = mocker.spy(client.session_manager, "_get_user")
    credentials = mock_user_credentials()
    options = SignUpWithPassword.email(
        email=credentials.email,
        password=credentials.password,
    )
    user = (client.sign_up(options)).user

    assert user is not None

    response = client.get_claims()
    assert response
    claims = response.claims

    assert claims.model_extra
    assert claims.model_extra["email"] == user.email
    spy.assert_called_once()


def test_get_claims_fetches_jwks_to_verify_asymmetric_jwt(mocker) -> None:
    client = auth_client_with_asymmetric_session()
    credentials = mock_user_credentials()
    options = SignUpWithPassword.email(
        email=credentials.email,
        password=credentials.password,
    )
    user = (client.sign_up(options)).user
    assert user is not None

    response = client.get_claims()
    assert response
    claims = response.claims

    assert claims.model_extra
    assert claims.model_extra["email"] == user.email

    expected_keyid = "638c54b8-28c2-4b12-9598-ba12ef610a29"

    assert len(client._jwks.keys) == 1
    assert client._jwks.keys[0].kid == expected_keyid


def test_jwks_ttl_cache_behavior(mocker) -> None:
    client = auth_client_with_asymmetric_session()
    spy = mocker.spy(client.executor.session, "send")

    # First call should fetch JWKS from endpoint
    credentials = mock_user_credentials()
    options = SignUpWithPassword.email(
        email=credentials.email,
        password=credentials.password,
    )
    user = (client.sign_up(options)).user
    assert user is not None

    client.get_claims()

    first_call_count = spy.call_count

    # Second call within TTL should use cache
    client.get_claims()
    assert spy.call_count == first_call_count  # No additional JWKS request

    # Mock time to be after TTL expiry
    original_time = time.time
    try:
        mock_time = mocker.patch("time.time")
        mock_time.return_value = original_time() + 601  # TTL is 600 seconds

        # Call after TTL expiry should fetch fresh JWKS
        client.get_claims()
        assert spy.call_count == first_call_count + 1  # One more JWKS request
    finally:
        # Restore original time function
        mocker.patch("time.time", original_time)


def test_set_session_with_valid_tokens() -> None:
    client = auth_client()
    credentials = mock_user_credentials()

    # First sign up to get valid tokens
    signup_response = client.sign_up(
        SignUpWithPassword.email(email=credentials.email, password=credentials.password)
    )
    assert signup_response.session is not None

    # Get the tokens from the signup response
    access_token = signup_response.session.access_token
    refresh_token = signup_response.session.refresh_token

    # Clear the session
    client.session_manager.remove_session()

    # Set the session with the tokens
    response = client.set_session(access_token, refresh_token)

    # Verify the response
    assert response.session is not None
    assert response.session.access_token == access_token
    assert response.session.refresh_token == refresh_token
    assert response.user is not None
    assert response.user.email == credentials.email


def test_set_session_with_expired_token() -> None:
    client = auth_client()
    credentials = mock_user_credentials()

    # First sign up to get valid tokens
    signup_response = client.sign_up(
        SignUpWithPassword.email(email=credentials.email, password=credentials.password)
    )
    assert signup_response.session is not None

    # Get the tokens from the signup response
    access_token = signup_response.session.access_token
    refresh_token = signup_response.session.refresh_token

    # Clear the session
    client.session_manager.remove_session()

    # Create an expired token by modifying the JWT
    expired_token = access_token.split(".")
    payload = decode_jwt(access_token).payload
    payload.exp = int(time.time()) - 3600  # Set expiry to 1 hour ago
    expired_token[1] = encode(
        dict(payload), GOTRUE_JWT_SECRET, algorithm="HS256"
    ).split(".")[1]
    expired_access_token = ".".join(expired_token)

    # Set the session with the expired token
    response = client.set_session(expired_access_token, refresh_token)

    # Verify the response has a new access token (refreshed)
    assert response.session is not None
    assert response.session.access_token != expired_access_token
    assert response.session.refresh_token != refresh_token
    assert response.user is not None
    assert response.user.email == credentials.email


def test_set_session_without_refresh_token() -> None:
    client = auth_client()
    credentials = mock_user_credentials()

    # First sign up to get valid tokens
    signup_response = client.sign_up(
        SignUpWithPassword.email(email=credentials.email, password=credentials.password)
    )
    assert signup_response.session is not None

    # Get the access token from the signup response
    access_token = signup_response.session.access_token

    # Clear the session
    client.session_manager.remove_session()

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
        client.set_session(expired_access_token, "")


def test_set_session_with_invalid_token() -> None:
    client = auth_client()

    # Try to set the session with invalid tokens
    with pytest.raises(AuthInvalidJwtError):
        client.set_session("invalid.token.here", "invalid_refresh_token")


def test_mfa_enroll() -> None:
    client = auth_client_with_session()

    credentials = mock_user_credentials()

    # First sign up to get a valid session
    _signup_response = client.sign_up(
        SignUpWithPassword.email(email=credentials.email, password=credentials.password)
    )
    # Test MFA enrollment
    enroll_response = client.mfa.enroll(
        MFAEnroll.totp(issuer="test-issuer", friendly_name="test-factor")
    )

    assert enroll_response.id is not None
    assert enroll_response.type == "totp"
    assert enroll_response.friendly_name == "test-factor"
    assert enroll_response.totp
    assert enroll_response.totp.qr_code is not None


def test_mfa_challenge() -> None:
    client = auth_client()
    credentials = mock_user_credentials()

    # First sign up to get a valid session
    signup_response = client.sign_up(
        SignUpWithPassword.email(email=credentials.email, password=credentials.password)
    )
    assert signup_response.session is not None

    # Enroll a factor first
    enroll_response = client.mfa.enroll(
        MFAEnroll.totp(issuer="test-issuer", friendly_name="test-factor")
    )

    # Test MFA challenge
    challenge_response = client.mfa.challenge(factor_id=enroll_response.id)
    assert challenge_response.id is not None
    assert challenge_response.expires_at is not None


def test_mfa_unenroll() -> None:
    client = auth_client()
    credentials = mock_user_credentials()

    # First sign up to get a valid session
    signup_response = client.sign_up(
        SignUpWithPassword.email(email=credentials.email, password=credentials.password)
    )
    assert signup_response.session is not None

    # Enroll a factor first
    enroll_response = client.mfa.enroll(
        MFAEnroll.totp(issuer="test-issuer", friendly_name="test-factor")
    )

    # Test MFA unenroll
    unenroll_response = client.mfa.unenroll(factor_id=enroll_response.id)
    assert unenroll_response.id == enroll_response.id


def test_mfa_list_factors() -> None:
    client = auth_client()
    credentials = mock_user_credentials()

    # First sign up to get a valid session
    signup_response = client.sign_up(
        SignUpWithPassword.email(email=credentials.email, password=credentials.password)
    )
    assert signup_response.session is not None

    # Enroll a factor first
    client.mfa.enroll(MFAEnroll.totp(issuer="test-issuer", friendly_name="test-factor"))

    # Test MFA list factors
    list_response = client.mfa.list_factors()
    assert len(list_response.all) == 1


def test_get_authenticator_assurance_level() -> None:
    client = auth_client()
    credentials = mock_user_credentials()

    # Without a session, should return null values
    aal_response = client.mfa.get_authenticator_assurance_level()
    assert aal_response.current_level is None
    assert aal_response.next_level is None
    assert aal_response.current_authentication_methods == []

    # Sign up to get a valid session
    signup_response = client.sign_up(
        SignUpWithPassword.email(email=credentials.email, password=credentials.password)
    )
    assert signup_response.session is not None

    # With a session, should return authentication methods
    aal_response = client.mfa.get_authenticator_assurance_level()
    # Basic auth will have password as an authentication method
    assert aal_response.current_authentication_methods is not None


def test_get_user_identities() -> None:
    client = auth_client()
    credentials = mock_user_credentials()

    # Sign up to get a valid session
    signup_response = client.sign_up(
        SignUpWithPassword.email(email=credentials.email, password=credentials.password)
    )
    assert signup_response.session is not None

    # New users won't have any identities yet, but the call should work
    identities_response = client.get_user_identities()
    assert identities_response is not None
    # For a new user, identities will be an empty list or None
    assert hasattr(identities_response, "identities")


def test_sign_in_with_password() -> None:
    client = auth_client()
    credentials = mock_user_credentials()

    # First create a user we can sign in with
    signup_response = client.sign_up(
        SignUpWithPassword.email(email=credentials.email, password=credentials.password)
    )
    assert signup_response.session is not None

    # Test signing in with the same credentials (email)
    signin_response = client.sign_in_with_password(
        SignInWithPassword.email(
            email=credentials.email,
            password=credentials.password,
        )
    )

    # Verify the response has a valid session and user
    assert signin_response.session is not None
    assert signin_response.user is not None
    assert signin_response.user.email == credentials.email

    # Test error case: wrong password

    # We need to create a custom client to avoid affecting other tests
    test_client = auth_client()

    try:
        test_client.sign_in_with_password(
            SignInWithPassword.email(
                email=credentials.email,
                password="wrong_password",
            )
        )
        raise AssertionError("Expected AuthApiError for wrong password")
    except AuthApiError:
        pass


def test_sign_out() -> None:
    client = auth_client()
    credentials = mock_user_credentials()

    signup_response = client.sign_up(
        SignUpWithPassword.email(email=credentials.email, password=credentials.password)
    )
    assert signup_response.session is not None

    signin_response = client.sign_in_with_password(
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

    client.on_auth_state_change(sign_out_callback)

    client.sign_out()

    no_more_session = client.get_session()
    assert no_more_session is None
    assert called
