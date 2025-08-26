import time
import unittest
from uuid import uuid4

import pytest
from jwt import encode

from supabase_auth.errors import (
    AuthApiError,
    AuthInvalidJwtError,
    AuthSessionMissingError,
)
from supabase_auth.helpers import decode_jwt

from .clients import (
    GOTRUE_JWT_SECRET,
    auth_client,
    auth_client_with_asymmetric_session,
    auth_client_with_session,
)
from .utils import mock_user_credentials


async def test_get_claims_returns_none_when_session_is_none():
    claims = await auth_client().get_claims()
    assert claims is None


async def test_get_claims_calls_get_user_if_symmetric_jwt(mocker):
    client = auth_client()
    spy = mocker.spy(client, "get_user")

    user = (await client.sign_up(mock_user_credentials())).user
    assert user is not None

    claims = (await client.get_claims())["claims"]
    assert claims["email"] == user.email
    spy.assert_called_once()


async def test_get_claims_fetches_jwks_to_verify_asymmetric_jwt(mocker):
    client = auth_client_with_asymmetric_session()

    user = (await client.sign_up(mock_user_credentials())).user
    assert user is not None

    spy = mocker.spy(client, "_request")

    claims = (await client.get_claims())["claims"]
    assert claims["email"] == user.email

    spy.assert_called_once()
    spy.assert_called_with("GET", ".well-known/jwks.json", xform=unittest.mock.ANY)

    expected_keyid = "638c54b8-28c2-4b12-9598-ba12ef610a29"

    assert len(client._jwks["keys"]) == 1
    assert client._jwks["keys"][0]["kid"] == expected_keyid


async def test_jwks_ttl_cache_behavior(mocker):
    client = auth_client_with_asymmetric_session()

    spy = mocker.spy(client, "_request")

    # First call should fetch JWKS from endpoint
    user = (await client.sign_up(mock_user_credentials())).user
    assert user is not None

    await client.get_claims()
    spy.assert_called_with("GET", ".well-known/jwks.json", xform=unittest.mock.ANY)
    first_call_count = spy.call_count

    # Second call within TTL should use cache
    await client.get_claims()
    assert spy.call_count == first_call_count  # No additional JWKS request

    # Mock time to be after TTL expiry
    original_time = time.time
    try:
        mock_time = mocker.patch("time.time")
        mock_time.return_value = original_time() + 601  # TTL is 600 seconds

        # Call after TTL expiry should fetch fresh JWKS
        await client.get_claims()
        assert spy.call_count == first_call_count + 1  # One more JWKS request
    finally:
        # Restore original time function
        mocker.patch("time.time", original_time)


async def test_set_session_with_valid_tokens():
    client = auth_client()
    credentials = mock_user_credentials()

    # First sign up to get valid tokens
    signup_response = await client.sign_up(
        {
            "email": credentials.get("email"),
            "password": credentials.get("password"),
        }
    )
    assert signup_response.session is not None

    # Get the tokens from the signup response
    access_token = signup_response.session.access_token
    refresh_token = signup_response.session.refresh_token

    # Clear the session
    await client._remove_session()

    # Set the session with the tokens
    response = await client.set_session(access_token, refresh_token)

    # Verify the response
    assert response.session is not None
    assert response.session.access_token == access_token
    assert response.session.refresh_token == refresh_token
    assert response.user is not None
    assert response.user.email == credentials.get("email")


async def test_set_session_with_expired_token():
    client = auth_client()
    credentials = mock_user_credentials()

    # First sign up to get valid tokens
    signup_response = await client.sign_up(
        {
            "email": credentials.get("email"),
            "password": credentials.get("password"),
        }
    )
    assert signup_response.session is not None

    # Get the tokens from the signup response
    access_token = signup_response.session.access_token
    refresh_token = signup_response.session.refresh_token

    # Clear the session
    await client._remove_session()

    # Create an expired token by modifying the JWT
    expired_token = access_token.split(".")
    payload = decode_jwt(access_token)["payload"]
    payload["exp"] = int(time.time()) - 3600  # Set expiry to 1 hour ago
    expired_token[1] = encode(payload, GOTRUE_JWT_SECRET, algorithm="HS256").split(".")[
        1
    ]
    expired_access_token = ".".join(expired_token)

    # Set the session with the expired token
    response = await client.set_session(expired_access_token, refresh_token)

    # Verify the response has a new access token (refreshed)
    assert response.session is not None
    assert response.session.access_token != expired_access_token
    assert response.session.refresh_token != refresh_token
    assert response.user is not None
    assert response.user.email == credentials.get("email")


async def test_set_session_without_refresh_token():
    client = auth_client()
    credentials = mock_user_credentials()

    # First sign up to get valid tokens
    signup_response = await client.sign_up(
        {
            "email": credentials.get("email"),
            "password": credentials.get("password"),
        }
    )
    assert signup_response.session is not None

    # Get the access token from the signup response
    access_token = signup_response.session.access_token

    # Clear the session
    await client._remove_session()

    # Create an expired token
    expired_token = access_token.split(".")
    payload = decode_jwt(access_token)["payload"]
    payload["exp"] = int(time.time()) - 3600  # Set expiry to 1 hour ago
    expired_token[1] = encode(payload, GOTRUE_JWT_SECRET, algorithm="HS256").split(".")[
        1
    ]
    expired_access_token = ".".join(expired_token)

    # Try to set the session with an expired token but no refresh token
    with pytest.raises(AuthSessionMissingError):
        await client.set_session(expired_access_token, "")


async def test_set_session_with_invalid_token():
    client = auth_client()

    # Try to set the session with invalid tokens
    with pytest.raises(AuthInvalidJwtError):
        await client.set_session("invalid.token.here", "invalid_refresh_token")


async def test_mfa_enroll():
    client = auth_client_with_session()

    credentials = mock_user_credentials()

    # First sign up to get a valid session
    await client.sign_up(
        {
            "email": credentials.get("email"),
            "password": credentials.get("password"),
        }
    )

    # Test MFA enrollment
    enroll_response = await client.mfa.enroll(
        {"issuer": "test-issuer", "factor_type": "totp", "friendly_name": "test-factor"}
    )

    assert enroll_response.id is not None
    assert enroll_response.type == "totp"
    assert enroll_response.friendly_name == "test-factor"
    assert enroll_response.totp.qr_code is not None


async def test_mfa_challenge():
    client = auth_client()
    credentials = mock_user_credentials()

    # First sign up to get a valid session
    signup_response = await client.sign_up(
        {
            "email": credentials.get("email"),
            "password": credentials.get("password"),
        }
    )
    assert signup_response.session is not None

    # Enroll a factor first
    enroll_response = await client.mfa.enroll(
        {"factor_type": "totp", "issuer": "test-issuer", "friendly_name": "test-factor"}
    )

    # Test MFA challenge
    challenge_response = await client.mfa.challenge({"factor_id": enroll_response.id})
    assert challenge_response.id is not None
    assert challenge_response.expires_at is not None


async def test_mfa_unenroll():
    client = auth_client()
    credentials = mock_user_credentials()

    # First sign up to get a valid session
    signup_response = await client.sign_up(
        {
            "email": credentials.get("email"),
            "password": credentials.get("password"),
        }
    )
    assert signup_response.session is not None

    # Enroll a factor first
    enroll_response = await client.mfa.enroll(
        {"factor_type": "totp", "issuer": "test-issuer", "friendly_name": "test-factor"}
    )

    # Test MFA unenroll
    unenroll_response = await client.mfa.unenroll({"factor_id": enroll_response.id})
    assert unenroll_response.id == enroll_response.id


async def test_mfa_list_factors():
    client = auth_client()
    credentials = mock_user_credentials()

    # First sign up to get a valid session
    signup_response = await client.sign_up(
        {
            "email": credentials.get("email"),
            "password": credentials.get("password"),
        }
    )
    assert signup_response.session is not None

    # Enroll a factor first
    await client.mfa.enroll(
        {"factor_type": "totp", "issuer": "test-issuer", "friendly_name": "test-factor"}
    )

    # Test MFA list factors
    list_response = await client.mfa.list_factors()
    assert len(list_response.all) == 1


async def test_initialize_from_url():
    # This test verifies the URL format detection and initialization from URL
    client = auth_client()

    # First we'll test the _is_implicit_grant_flow method
    # The method checks for access_token or error_description in the query string, not the fragment
    url_with_token = "http://example.com/?access_token=test_token&other=value"
    assert client._is_implicit_grant_flow(url_with_token) == True

    url_with_error = "http://example.com/?error_description=test_error&other=value"
    assert client._is_implicit_grant_flow(url_with_error) == True

    url_without_token = "http://example.com/?other=value"
    assert client._is_implicit_grant_flow(url_without_token) == False

    # Now test actual URL initialization with a valid URL containing auth tokens
    from unittest.mock import patch

    from supabase_auth.types import Session, User, UserResponse

    # Create a mock user and session to avoid actual API calls
    mock_user = User(
        id="user123",
        email="test@example.com",
        app_metadata={},
        user_metadata={},
        aud="authenticated",
        created_at="2023-01-01T00:00:00Z",
        confirmed_at="2023-01-01T00:00:00Z",
        last_sign_in_at="2023-01-01T00:00:00Z",
        role="authenticated",
        updated_at="2023-01-01T00:00:00Z",
    )

    # Wrap the user in a UserResponse as that's what get_user returns
    mock_user_response = UserResponse(user=mock_user)

    # Test successful initialization with tokens in URL
    good_url = "http://example.com/?access_token=mock_access_token&refresh_token=mock_refresh_token&expires_in=3600&token_type=bearer"

    # We need to mock:
    # 1. get_user which is called by _get_session_from_url to validate the token
    # 2. _save_session which is called to store the session data
    # 3. _notify_all_subscribers which is called to notify about sign-in
    with patch.object(client, "get_user") as mock_get_user:
        mock_get_user.return_value = mock_user_response

        with patch.object(client, "_save_session") as mock_save_session:
            with patch.object(client, "_notify_all_subscribers") as mock_notify:
                # Call initialize_from_url with the good URL
                result = await client.initialize_from_url(good_url)

                # Verify get_user was called with the access token
                mock_get_user.assert_called_once_with("mock_access_token")

                # Verify _save_session was called with a Session object
                mock_save_session.assert_called_once()
                session_arg = mock_save_session.call_args[0][0]
                assert isinstance(session_arg, Session)
                assert session_arg.access_token == "mock_access_token"
                assert session_arg.refresh_token == "mock_refresh_token"
                assert session_arg.expires_in == 3600

                # Verify _notify_all_subscribers was called
                mock_notify.assert_called_with("SIGNED_IN", session_arg)

                assert result is None  # initialize_from_url doesn't have a return value

    # Test URL with error - need to include error_code for the test to work correctly
    error_url = "http://example.com/?error=invalid_request&error_description=Invalid+request&error_code=400"

    # Should throw an error when URL contains error parameters
    from supabase_auth.errors import AuthImplicitGrantRedirectError

    try:
        await client.initialize_from_url(error_url)
        assert False, "Expected AuthImplicitGrantRedirectError"
    except AuthImplicitGrantRedirectError as e:
        # The error message includes the error_description value
        assert "Invalid request" in str(e)

    # Test URL with code for PKCE flow
    code_url = "http://example.com/?code=authorization_code"

    # For the code URL path, we're not testing it here since it requires more mocking
    # and is indirectly tested via other tests like exchange_code_for_session

    # Test URL with neither tokens nor code - should not throw but also not call anything
    invalid_url = "http://example.com/?foo=bar"
    with patch.object(client, "_get_session_from_url") as mock_get_session:
        result = await client.initialize_from_url(invalid_url)
        mock_get_session.assert_not_called()
        assert result is None


async def test_exchange_code_for_session():
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
    provider = "github"
    url, params = await client._get_url_for_provider(
        f"{client._url}/authorize", provider, {}
    )

    # Verify PKCE parameters were added
    assert "code_challenge" in params
    assert "code_challenge_method" in params

    # Verify the code verifier was stored
    code_verifier = await client._storage.get_item(storage_key)
    assert code_verifier is not None


async def test_get_authenticator_assurance_level():
    client = auth_client()
    credentials = mock_user_credentials()

    # Without a session, should return null values
    aal_response = await client.mfa.get_authenticator_assurance_level()
    assert aal_response.current_level is None
    assert aal_response.next_level is None
    assert aal_response.current_authentication_methods == []

    # Sign up to get a valid session
    signup_response = await client.sign_up(
        {
            "email": credentials.get("email"),
            "password": credentials.get("password"),
        }
    )
    assert signup_response.session is not None

    # With a session, should return authentication methods
    aal_response = await client.mfa.get_authenticator_assurance_level()
    # Basic auth will have password as an authentication method
    assert aal_response.current_authentication_methods is not None


async def test_link_identity():
    client = auth_client()
    credentials = mock_user_credentials()

    # Sign up to get a valid session
    signup_response = await client.sign_up(
        {
            "email": credentials.get("email"),
            "password": credentials.get("password"),
        }
    )
    assert signup_response.session is not None

    from unittest.mock import patch

    from supabase_auth.types import OAuthResponse

    # Since the test server has manual linking disabled, we'll mock the URL generation
    with patch.object(client, "_get_url_for_provider") as mock_url_provider:
        mock_url = "http://example.com/authorize?provider=github"
        mock_params = {"provider": "github"}
        mock_url_provider.return_value = (mock_url, mock_params)

        # Also mock the _request method since the server would reject it
        with patch.object(client, "_request") as mock_request:
            mock_request.return_value = OAuthResponse(provider="github", url=mock_url)

            # Call the method
            response = await client.link_identity({"provider": "github"})

            # Verify the response
            assert response.provider == "github"
            assert response.url == mock_url


async def test_get_user_identities():
    client = auth_client()
    credentials = mock_user_credentials()

    # Sign up to get a valid session
    signup_response = await client.sign_up(
        {
            "email": credentials.get("email"),
            "password": credentials.get("password"),
        }
    )
    assert signup_response.session is not None

    # New users won't have any identities yet, but the call should work
    identities_response = await client.get_user_identities()
    assert identities_response is not None
    # For a new user, identities will be an empty list or None
    assert hasattr(identities_response, "identities")


async def test_unlink_identity():
    client = auth_client()
    credentials = mock_user_credentials()

    # Sign up to get a valid session
    signup_response = await client.sign_up(
        {
            "email": credentials.get("email"),
            "password": credentials.get("password"),
        }
    )
    assert signup_response.session is not None

    # Mock a UserIdentity to test unlink_identity
    from unittest.mock import patch

    from supabase_auth.types import UserIdentity

    # Create a mock identity
    mock_identity = UserIdentity(
        id="user-id",
        identity_id="identity-id-1",
        user_id="user-id",
        identity_data={"email": "user@example.com"},
        provider="github",
        created_at="2023-01-01T00:00:00Z",
        last_sign_in_at="2023-01-01T00:00:00Z",
        updated_at="2023-01-01T00:00:00Z",
    )

    # Mock the _request method since we can't actually unlink an identity that doesn't exist
    with patch.object(client, "_request") as mock_request:
        mock_request.return_value = None

        # Call the method
        await client.unlink_identity(mock_identity)

        # Verify the request was made properly
        mock_request.assert_called_once_with(
            "DELETE",
            "user/identities/identity-id-1",
            jwt=signup_response.session.access_token,
        )

    # Test error case: no session
    with patch.object(client, "get_session") as mock_get_session:
        from supabase_auth.errors import AuthSessionMissingError

        mock_get_session.return_value = None

        try:
            await client.unlink_identity(mock_identity)
            assert False, "Expected AuthSessionMissingError"
        except AuthSessionMissingError:
            pass


async def test_verify_otp():
    client = auth_client()

    # Mock the _request method since we can't actually verify an OTP in the test
    import time
    from unittest.mock import patch

    from supabase_auth.types import AuthResponse, Session, User

    mock_user = User(
        id="test-user-id",
        app_metadata={},
        user_metadata={},
        aud="test-aud",
        email="test@example.com",
        phone="",
        created_at="2023-01-01T00:00:00Z",
        confirmed_at="2023-01-01T00:00:00Z",
        last_sign_in_at="2023-01-01T00:00:00Z",
        role="",
        updated_at="2023-01-01T00:00:00Z",
    )

    mock_session = Session(
        access_token="mock-access-token",
        refresh_token="mock-refresh-token",
        expires_in=3600,
        expires_at=round(time.time()) + 3600,
        token_type="bearer",
        user=mock_user,
    )

    mock_response = AuthResponse(session=mock_session, user=mock_user)

    with patch.object(client, "_request") as mock_request:
        # Configure the mock to return a predefined response
        mock_request.return_value = mock_response

        # Also patch _save_session to avoid actual storage interactions
        with patch.object(client, "_save_session") as mock_save:
            # Call verify_otp with test parameters
            params = {
                "type": "sms",
                "phone": "+11234567890",
                "token": "123456",
                "options": {"redirect_to": "https://example.com/callback"},
            }

            response = await client.verify_otp(params)

            # Verify the request was made with correct parameters
            mock_request.assert_called_once()
            args, kwargs = mock_request.call_args
            assert args[0] == "POST"  # method
            assert args[1] == "verify"  # path
            assert kwargs["body"]["phone"] == "+11234567890"
            assert kwargs["body"]["token"] == "123456"
            assert kwargs["redirect_to"] == "https://example.com/callback"

            # Verify the session was saved
            mock_save.assert_called_once_with(mock_session)

            # Verify the response
            assert response == mock_response


async def test_sign_in_with_password():
    client = auth_client()
    credentials = mock_user_credentials()
    from supabase_auth.errors import AuthApiError, AuthInvalidCredentialsError

    # First create a user we can sign in with
    signup_response = await client.sign_up(
        {
            "email": credentials.get("email"),
            "password": credentials.get("password"),
        }
    )
    assert signup_response.session is not None

    # Test signing in with the same credentials (email)
    signin_response = await client.sign_in_with_password(
        {
            "email": credentials.get("email"),
            "password": credentials.get("password"),
        }
    )

    # Verify the response has a valid session and user
    assert signin_response.session is not None
    assert signin_response.user is not None
    assert signin_response.user.email == credentials.get("email")

    # Test error case: wrong password

    # We need to create a custom client to avoid affecting other tests
    test_client = auth_client()

    try:
        await test_client.sign_in_with_password(
            {
                "email": credentials.get("email"),
                "password": "wrong_password",
            }
        )
        assert False, "Expected AuthApiError for wrong password"
    except AuthApiError:
        pass

    # Test error case: missing credentials
    try:
        await test_client.sign_in_with_password({})
        assert False, "Expected AuthInvalidCredentialsError for missing credentials"
    except AuthInvalidCredentialsError:
        pass


async def test_sign_in_with_otp():
    client = auth_client()

    # Test with email OTP
    email = f"test-{uuid4()}@example.com"

    # When sign_in_with_otp is called with valid email, it should return a AuthOtpResponse
    # We can't fully test the actual OTP flow since that requires email verification
    from unittest.mock import patch

    from supabase_auth.types import AuthOtpResponse

    # First test for email OTP
    with patch.object(client, "_request") as mock_request:
        mock_response = AuthOtpResponse(
            message_id="mock-message-id", email=email, phone=None, hash=None
        )
        mock_request.return_value = mock_response

        response = await client.sign_in_with_otp(
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
        assert kwargs["body"]["create_user"] == True
        assert kwargs["body"]["data"] == {"custom": "data"}
        assert (
            kwargs["body"]["gotrue_meta_security"]["captcha_token"]
            == "mock-captcha-token"
        )
        assert kwargs["redirect_to"] == "https://example.com/callback"

        # Verify response
        assert response == mock_response

    # Test with phone OTP
    phone = "+11234567890"

    with patch.object(client, "_request") as mock_request:
        mock_response = AuthOtpResponse(
            message_id="mock-message-id", email=None, phone=phone, hash=None
        )
        mock_request.return_value = mock_response

        response = await client.sign_in_with_otp(
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
        assert kwargs["body"]["create_user"] == True
        assert kwargs["body"]["data"] == {"custom": "data"}
        assert kwargs["body"]["channel"] == "whatsapp"
        assert (
            kwargs["body"]["gotrue_meta_security"]["captcha_token"]
            == "mock-captcha-token"
        )
        assert kwargs.get("redirect_to") is None  # No redirect for phone

        # Verify response
        assert response == mock_response

    # Test with invalid parameters (missing both email and phone)
    from supabase_auth.errors import AuthInvalidCredentialsError

    try:
        await client.sign_in_with_otp({})
        assert False, "Expected AuthInvalidCredentialsError"
    except AuthInvalidCredentialsError:
        pass


async def test_sign_out():
    from unittest.mock import patch

    from supabase_auth.types import Session, User

    client = auth_client()

    # Create a mock user and session
    mock_user = User(
        id="user123",
        email="test@example.com",
        app_metadata={},
        user_metadata={},
        aud="authenticated",
        created_at="2023-01-01T00:00:00Z",
        confirmed_at="2023-01-01T00:00:00Z",
        last_sign_in_at="2023-01-01T00:00:00Z",
        role="authenticated",
        updated_at="2023-01-01T00:00:00Z",
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
                    await client.sign_out()

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
                    await client.sign_out({"scope": "local"})

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
                    await client.sign_out({"scope": "others"})

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
                    await client.sign_out()

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
                "Test error", 401, "auth_error"
            )

            with patch.object(client, "_remove_session") as mock_remove_session:
                with patch.object(client, "_notify_all_subscribers") as mock_notify:
                    # Call sign_out with default scope
                    await client.sign_out()

                    # Verify that _remove_session was still called despite the error
                    mock_remove_session.assert_called_once()

                    # Verify that _notify_all_subscribers was still called despite the error
                    mock_notify.assert_called_once_with("SIGNED_OUT", None)
