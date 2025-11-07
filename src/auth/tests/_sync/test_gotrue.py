import time
from uuid import uuid4

import pytest
from jwt import encode
from supabase_auth.errors import (
    AuthApiError,
    AuthInvalidJwtError,
    AuthSessionMissingError,
)
from supabase_auth.helpers import decode_jwt
from supabase_auth.types import SignUpWithEmailAndPasswordCredentials

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
    spy = mocker.spy(client, "get_user")
    credentials = mock_user_credentials()
    options: SignUpWithEmailAndPasswordCredentials = {
        "email": credentials.email,
        "password": credentials.password,
    }
    user = (client.sign_up(options)).user

    assert user is not None

    response = client.get_claims()
    assert response
    claims = response["claims"]

    assert claims.get("email") == user.email
    spy.assert_called_once()


def test_get_claims_fetches_jwks_to_verify_asymmetric_jwt(mocker) -> None:
    client = auth_client_with_asymmetric_session()
    credentials = mock_user_credentials()
    options: SignUpWithEmailAndPasswordCredentials = {
        "email": credentials.email,
        "password": credentials.password,
    }
    user = (client.sign_up(options)).user
    assert user is not None

    spy = mocker.spy(client, "_request")

    response = client.get_claims()
    assert response
    claims = response["claims"]
    assert claims.get("email") == user.email

    spy.assert_called_once()
    spy.assert_called_with("GET", ".well-known/jwks.json")

    expected_keyid = "638c54b8-28c2-4b12-9598-ba12ef610a29"

    assert len(client._jwks["keys"]) == 1
    assert client._jwks["keys"][0]["kid"] == expected_keyid


def test_jwks_ttl_cache_behavior(mocker) -> None:
    client = auth_client_with_asymmetric_session()

    spy = mocker.spy(client, "_request")

    # First call should fetch JWKS from endpoint
    credentials = mock_user_credentials()
    options: SignUpWithEmailAndPasswordCredentials = {
        "email": credentials.email,
        "password": credentials.password,
    }
    user = (client.sign_up(options)).user
    assert user is not None

    client.get_claims()
    spy.assert_called_with("GET", ".well-known/jwks.json")
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
        {
            "email": credentials.email,
            "password": credentials.password,
        }
    )
    assert signup_response.session is not None

    # Get the tokens from the signup response
    access_token = signup_response.session.access_token
    refresh_token = signup_response.session.refresh_token

    # Clear the session
    client._remove_session()

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
        {
            "email": credentials.email,
            "password": credentials.password,
        }
    )
    assert signup_response.session is not None

    # Get the tokens from the signup response
    access_token = signup_response.session.access_token
    refresh_token = signup_response.session.refresh_token

    # Clear the session
    client._remove_session()

    # Create an expired token by modifying the JWT
    expired_token = access_token.split(".")
    payload = decode_jwt(access_token)["payload"]
    payload["exp"] = int(time.time()) - 3600  # Set expiry to 1 hour ago
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
        {
            "email": credentials.email,
            "password": credentials.password,
        }
    )
    assert signup_response.session is not None

    # Get the access token from the signup response
    access_token = signup_response.session.access_token

    # Clear the session
    client._remove_session()

    # Create an expired token
    expired_token = access_token.split(".")
    payload = decode_jwt(access_token)["payload"]
    payload["exp"] = int(time.time()) - 3600  # Set expiry to 1 hour ago
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
    client.sign_up(
        {
            "email": credentials.email,
            "password": credentials.password,
        }
    )

    # Test MFA enrollment
    enroll_response = client.mfa.enroll(
        {"issuer": "test-issuer", "factor_type": "totp", "friendly_name": "test-factor"}
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
        {
            "email": credentials.email,
            "password": credentials.password,
        }
    )
    assert signup_response.session is not None

    # Enroll a factor first
    enroll_response = client.mfa.enroll(
        {"factor_type": "totp", "issuer": "test-issuer", "friendly_name": "test-factor"}
    )

    # Test MFA challenge
    challenge_response = client.mfa.challenge({"factor_id": enroll_response.id})
    assert challenge_response.id is not None
    assert challenge_response.expires_at is not None


def test_mfa_unenroll() -> None:
    client = auth_client()
    credentials = mock_user_credentials()

    # First sign up to get a valid session
    signup_response = client.sign_up(
        {
            "email": credentials.email,
            "password": credentials.password,
        }
    )
    assert signup_response.session is not None

    # Enroll a factor first
    enroll_response = client.mfa.enroll(
        {"factor_type": "totp", "issuer": "test-issuer", "friendly_name": "test-factor"}
    )

    # Test MFA unenroll
    unenroll_response = client.mfa.unenroll({"factor_id": enroll_response.id})
    assert unenroll_response.id == enroll_response.id


def test_mfa_list_factors() -> None:
    client = auth_client()
    credentials = mock_user_credentials()

    # First sign up to get a valid session
    signup_response = client.sign_up(
        {
            "email": credentials.email,
            "password": credentials.password,
        }
    )
    assert signup_response.session is not None

    # Enroll a factor first
    client.mfa.enroll(
        {"factor_type": "totp", "issuer": "test-issuer", "friendly_name": "test-factor"}
    )

    # Test MFA list factors
    list_response = client.mfa.list_factors()
    assert len(list_response.all) == 1


def test_exchange_code_for_session() -> None:
    client = auth_client()

    # We'll test the flow type setting instead of the actual exchange, since the
    # actual exchange requires a live OAuth flow which isn't practical in tests
    assert client._flow_type in ["implicit", "pkce"]

    # This part would normally need a live OAuth flow, so we verify the logic paths
    # Get the storage key for PKCE flow
    storage_key = f"{client._storage_key}-code-verifier"

    # Set the flow type to pkce
    client._flow_type = "pkce"

    # Test the PKCE URL generation which is needed for exchange_code_for_session
    url, params = client._get_url_for_provider(f"{client._url}/authorize", "github", {})

    # Verify PKCE parameters were added
    assert "code_challenge" in params
    assert "code_challenge_method" in params

    # Verify the code verifier was stored
    code_verifier = client._storage.get_item(storage_key)
    assert code_verifier is not None


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
        {
            "email": credentials.email,
            "password": credentials.password,
        }
    )
    assert signup_response.session is not None

    # With a session, should return authentication methods
    aal_response = client.mfa.get_authenticator_assurance_level()
    # Basic auth will have password as an authentication method
    assert aal_response.current_authentication_methods is not None


def test_link_identity() -> None:
    client = auth_client()
    credentials = mock_user_credentials()

    # Sign up to get a valid session
    signup_response = client.sign_up(
        {
            "email": credentials.email,
            "password": credentials.password,
        }
    )
    assert signup_response.session is not None

    from unittest.mock import patch

    from httpx import Response

    # Since the test server has manual linking disabled, we'll mock the URL generation
    with patch.object(client, "_get_url_for_provider") as mock_url_provider:
        mock_url = "http://example.com/authorize?provider=github"
        mock_params = {"provider": "github"}
        mock_url_provider.return_value = (mock_url, mock_params)

        # Also mock the _request method since the server would reject it
        with patch.object(client, "_request") as mock_request:
            mock_request.return_value = Response(
                content=f'{{"url":"{mock_url}"}}', status_code=200
            )

            # Call the method
            response = client.link_identity({"provider": "github"})

            # Verify the response
            assert response.provider == "github"
            assert response.url == mock_url


def test_get_user_identities() -> None:
    client = auth_client()
    credentials = mock_user_credentials()

    # Sign up to get a valid session
    signup_response = client.sign_up(
        {
            "email": credentials.email,
            "password": credentials.password,
        }
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
    from supabase_auth.errors import AuthApiError, AuthInvalidCredentialsError

    # First create a user we can sign in with
    signup_response = client.sign_up(
        {
            "email": credentials.email,
            "password": credentials.password,
        }
    )
    assert signup_response.session is not None

    # Test signing in with the same credentials (email)
    signin_response = client.sign_in_with_password(
        {
            "email": credentials.email,
            "password": credentials.password,
        }
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
            {
                "email": credentials.email,
                "password": "wrong_password",
            }
        )
        raise AssertionError("Expected AuthApiError for wrong password")
    except AuthApiError:
        pass

    # Test error case: missing credentials
    try:
        test_client.sign_in_with_password({})  # type: ignore
        raise AssertionError(
            "Expected AuthInvalidCredentialsError for missing credentials"
        )
    except AuthInvalidCredentialsError:
        pass


def test_sign_in_with_otp() -> None:
    client = auth_client()

    # Test with email OTP
    email = f"test-{uuid4()}@example.com"

    # When sign_in_with_otp is called with valid email, it should return a AuthOtpResponse
    # We can't fully test the actual OTP flow since that requires email verification
    from unittest.mock import patch

    from httpx import Response
    from supabase_auth.types import AuthOtpResponse

    # First test for email OTP
    auth_otp = AuthOtpResponse(
        message_id="mock-message-id",
    )
    with patch.object(client, "_request") as mock_request:
        mock_response = Response(content=auth_otp.model_dump_json(), status_code=200)
        mock_request.return_value = mock_response

        response = client.sign_in_with_otp(
            {
                "email": email,
                "options": {
                    "email_redirect_to": "https://example.com/callback",
                    "should_create_user": True,
                    "data": {"custom": "data"},
                    "captcha_token": "mock-captcha-token",
                },
            }
        )

        # Verify request parameters
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        assert args[0] == "POST"
        assert args[1] == "otp"
        assert kwargs["body"]["email"] == email
        assert kwargs["body"]["create_user"]
        assert kwargs["body"]["data"] == {"custom": "data"}
        assert (
            kwargs["body"]["gotrue_meta_security"]["captcha_token"]
            == "mock-captcha-token"
        )
        assert kwargs["redirect_to"] == "https://example.com/callback"

        # Verify response
        assert response == auth_otp

    # Test with phone OTP
    phone = "+11234567890"
    auth_otp = AuthOtpResponse(message_id="mock-message-id")
    with patch.object(client, "_request") as mock_request:
        mock_response = Response(content=auth_otp.model_dump_json(), status_code=200)
        mock_request.return_value = mock_response

        response = client.sign_in_with_otp(
            {
                "phone": phone,
                "options": {
                    "should_create_user": True,
                    "data": {"custom": "data"},
                    "channel": "whatsapp",  # Test alternate channel
                    "captcha_token": "mock-captcha-token",
                },
            }
        )

        # Verify request parameters
        mock_request.assert_called_once()
        args, kwargs = mock_request.call_args
        assert args[0] == "POST"
        assert args[1] == "otp"
        assert kwargs["body"]["phone"] == phone
        assert kwargs["body"]["create_user"]
        assert kwargs["body"]["data"] == {"custom": "data"}
        assert kwargs["body"]["channel"] == "whatsapp"
        assert (
            kwargs["body"]["gotrue_meta_security"]["captcha_token"]
            == "mock-captcha-token"
        )
        assert kwargs.get("redirect_to") is None  # No redirect for phone

        # Verify response
        assert response == auth_otp

    # Test with invalid parameters (missing both email and phone)
    from supabase_auth.errors import AuthInvalidCredentialsError

    try:
        client.sign_in_with_otp({})  # type: ignore
        raise AssertionError("Expected AuthInvalidCredentialsError")
    except AuthInvalidCredentialsError:
        pass


def test_sign_out() -> None:
    from datetime import datetime
    from unittest.mock import patch

    from supabase_auth.types import Session, User

    client = auth_client()

    # Create a mock user and session
    date = datetime(year=2023, month=1, day=1, hour=0, minute=0, second=0)
    mock_user = User(
        id="user123",
        email="test@example.com",
        app_metadata={},
        user_metadata={},
        aud="authenticated",
        created_at=date,
        confirmed_at=date,
        last_sign_in_at=date,
        role="authenticated",
        updated_at=date,
    )

    mock_session = Session(
        access_token="mock_access_token",
        refresh_token="mock_refresh_token",
        expires_in=3600,
        token_type="bearer",
        user=mock_user,
    )

    # Test sign_out with "global" scope (default)
    # This should call admin.sign_out, _remove_session, and _notify_all_subscribers
    with patch.object(client, "get_session") as mock_get_session:
        mock_get_session.return_value = mock_session

        with patch.object(client.admin, "sign_out") as mock_admin_sign_out:
            with patch.object(client, "_remove_session") as mock_remove_session:
                with patch.object(client, "_notify_all_subscribers") as mock_notify:
                    # Call sign_out with default scope (global)
                    client.sign_out()

                    # Verify that admin.sign_out was called with correct parameters
                    mock_admin_sign_out.assert_called_once_with(
                        "mock_access_token", "global"
                    )

                    # Verify that _remove_session was called
                    mock_remove_session.assert_called_once()

                    # Verify that _notify_all_subscribers was called with SIGNED_OUT
                    mock_notify.assert_called_once_with("SIGNED_OUT", None)

    # Test sign_out with "local" scope
    # Should behave the same as "global" for client-side
    with patch.object(client, "get_session") as mock_get_session:
        mock_get_session.return_value = mock_session

        with patch.object(client.admin, "sign_out") as mock_admin_sign_out:
            with patch.object(client, "_remove_session") as mock_remove_session:
                with patch.object(client, "_notify_all_subscribers") as mock_notify:
                    # Call sign_out with local scope
                    client.sign_out({"scope": "local"})

                    # Verify that admin.sign_out was called with correct parameters
                    mock_admin_sign_out.assert_called_once_with(
                        "mock_access_token", "local"
                    )

                    # Verify that _remove_session was called
                    mock_remove_session.assert_called_once()

                    # Verify that _notify_all_subscribers was called with SIGNED_OUT
                    mock_notify.assert_called_once_with("SIGNED_OUT", None)

    # Test sign_out with "others" scope
    # This should only call admin.sign_out but not _remove_session or _notify_all_subscribers
    with patch.object(client, "get_session") as mock_get_session:
        mock_get_session.return_value = mock_session

        with patch.object(client.admin, "sign_out") as mock_admin_sign_out:
            with patch.object(client, "_remove_session") as mock_remove_session:
                with patch.object(client, "_notify_all_subscribers") as mock_notify:
                    # Call sign_out with others scope
                    client.sign_out({"scope": "others"})

                    # Verify that admin.sign_out was called with correct parameters
                    mock_admin_sign_out.assert_called_once_with(
                        "mock_access_token", "others"
                    )

                    # Verify that _remove_session was NOT called
                    mock_remove_session.assert_not_called()

                    # Verify that _notify_all_subscribers was NOT called
                    mock_notify.assert_not_called()

    # Test sign_out with no session
    # This should not call admin.sign_out but still call _remove_session and _notify_all_subscribers
    with patch.object(client, "get_session") as mock_get_session:
        mock_get_session.return_value = None

        with patch.object(client.admin, "sign_out") as mock_admin_sign_out:
            with patch.object(client, "_remove_session") as mock_remove_session:
                with patch.object(client, "_notify_all_subscribers") as mock_notify:
                    # Call sign_out with default scope
                    client.sign_out()

                    # Verify that admin.sign_out was NOT called
                    mock_admin_sign_out.assert_not_called()

                    # Verify that _remove_session was called
                    mock_remove_session.assert_called_once()

                    # Verify that _notify_all_subscribers was called with SIGNED_OUT
                    mock_notify.assert_called_once_with("SIGNED_OUT", None)

    # Test when admin.sign_out raises an error
    # This should suppress the error and continue with _remove_session and _notify_all_subscribers
    with patch.object(client, "get_session") as mock_get_session:
        mock_get_session.return_value = mock_session

        with patch.object(client.admin, "sign_out") as mock_admin_sign_out:
            mock_admin_sign_out.side_effect = AuthApiError(
                "Test error", 401, "validation_failed"
            )

            with patch.object(client, "_remove_session") as mock_remove_session:
                with patch.object(client, "_notify_all_subscribers") as mock_notify:
                    # Call sign_out with default scope
                    client.sign_out()

                    # Verify that _remove_session was still called despite the error
                    mock_remove_session.assert_called_once()

                    # Verify that _notify_all_subscribers was still called despite the error
                    mock_notify.assert_called_once_with("SIGNED_OUT", None)
