import uuid

import pytest

from supabase_auth.errors import (
    AuthApiError,
    AuthError,
    AuthInvalidCredentialsError,
    AuthSessionMissingError,
    AuthWeakPasswordError,
)
from supabase_auth.types import CreateOAuthClientParams
from .clients import (
    auth_client,
    auth_client_with_session,
    client_api_auto_confirm_disabled_client,
    client_api_auto_confirm_off_signups_enabled_client,
    create_new_user_with_email,
    mock_app_metadata,
    mock_user_credentials,
    mock_user_metadata,
    mock_verification_otp,
    service_role_api_client,
)


def test_create_user_should_create_a_new_user():
    credentials = mock_user_credentials()
    response = create_new_user_with_email(email=credentials.email)
    assert response.email == credentials.email


def test_create_user_with_user_metadata():
    user_metadata = mock_user_metadata()
    credentials = mock_user_credentials()
    response = service_role_api_client().create_user(
        {
            "email": credentials.email,
            "password": credentials.password,
            "user_metadata": user_metadata,
        }
    )
    assert response.user.email == credentials.email
    assert response.user.user_metadata == user_metadata
    assert "profile_image" in response.user.user_metadata


def test_create_user_with_user_and_app_metadata():
    user_metadata = mock_user_metadata()
    app_metadata = mock_app_metadata()
    credentials = mock_user_credentials()
    response = service_role_api_client().create_user(
        {
            "email": credentials.email,
            "password": credentials.password,
            "user_metadata": user_metadata,
            "app_metadata": app_metadata,
        }
    )
    assert response.user.email == credentials.email
    assert "profile_image" in response.user.user_metadata
    assert "provider" in response.user.app_metadata
    assert "providers" in response.user.app_metadata


def test_list_users_should_return_registered_users():
    credentials = mock_user_credentials()
    create_new_user_with_email(email=credentials.email)
    users = service_role_api_client().list_users()
    assert users
    emails = [user.email for user in users]
    assert emails
    assert credentials.email in emails


def test_get_user_by_id_should_a_registered_user_given_its_user_identifier():
    credentials = mock_user_credentials()
    user = create_new_user_with_email(email=credentials.email)
    assert user.id
    response = service_role_api_client().get_user_by_id(user.id)
    assert response.user.email == credentials.email


def test_modify_email_using_update_user_by_id():
    credentials = mock_user_credentials()
    user = create_new_user_with_email(email=credentials.email)
    response = service_role_api_client().update_user_by_id(
        user.id,
        {
            "email": f"new_{user.email}",
        },
    )
    assert response.user.email == f"new_{user.email}"


def test_modify_user_metadata_using_update_user_by_id():
    credentials = mock_user_credentials()
    user = create_new_user_with_email(email=credentials.email)
    user_metadata = {"favorite_color": "yellow"}
    response = service_role_api_client().update_user_by_id(
        user.id,
        {
            "user_metadata": user_metadata,
        },
    )
    assert response.user.email == user.email
    assert response.user.user_metadata == user_metadata


def test_modify_app_metadata_using_update_user_by_id():
    credentials = mock_user_credentials()
    user = create_new_user_with_email(email=credentials.email)
    app_metadata = {"roles": ["admin", "publisher"]}
    response = service_role_api_client().update_user_by_id(
        user.id,
        {
            "app_metadata": app_metadata,
        },
    )
    assert response.user.email == user.email
    assert "roles" in response.user.app_metadata


def test_modify_confirm_email_using_update_user_by_id():
    credentials = mock_user_credentials()
    response = client_api_auto_confirm_off_signups_enabled_client().sign_up(
        {
            "email": credentials.email,
            "password": credentials.password,
        }
    )
    assert response.user
    assert not response.user.email_confirmed_at
    response = service_role_api_client().update_user_by_id(
        response.user.id,
        {
            "email_confirm": True,
        },
    )
    assert response.user.email_confirmed_at


def test_invalid_credential_sign_in_with_phone():
    try:
        response = client_api_auto_confirm_off_signups_enabled_client().sign_in_with_password(
            {
                "phone": "+123456789",
                "password": "strong_pwd",
            }
        )
    except AuthApiError as e:
        assert e.to_dict()


def test_invalid_credential_sign_in_with_email():
    try:
        response = client_api_auto_confirm_off_signups_enabled_client().sign_in_with_password(
            {
                "email": "unknown_user@unknowndomain.com",
                "password": "strong_pwd",
            }
        )
    except AuthApiError as e:
        assert e.to_dict()


def test_sign_in_with_otp_email():
    try:
        client_api_auto_confirm_off_signups_enabled_client().sign_in_with_otp(
            {
                "email": "unknown_user@unknowndomain.com",
            }
        )
    except AuthApiError as e:
        assert e.to_dict()


def test_sign_in_with_otp_phone():
    try:
        client_api_auto_confirm_off_signups_enabled_client().sign_in_with_otp(
            {
                "phone": "+112345678",
            }
        )
    except AuthApiError as e:
        assert e.to_dict()


def test_resend():
    client_api_auto_confirm_off_signups_enabled_client().resend(
        {"phone": "+112345678", "type": "sms"}
    )


def test_reauthenticate():
    client = auth_client_with_session()
    client.reauthenticate()


def test_refresh_session():
    client = auth_client_with_session()
    client.refresh_session()


def test_reset_password_for_email():
    credentials = mock_user_credentials()
    client = auth_client_with_session()
    client.reset_password_email(email=credentials.email)


def test_resend_missing_credentials():
    credentials = mock_user_credentials()
    client_api_auto_confirm_off_signups_enabled_client().resend(
        {"type": "email_change", "email": credentials.email}
    )


def test_sign_in_anonymously():
    client = auth_client_with_session()
    client.sign_in_anonymously()


def test_delete_user_should_be_able_delete_an_existing_user():
    credentials = mock_user_credentials()
    user = create_new_user_with_email(email=credentials.email)
    service_role_api_client().delete_user(user.id)
    users = service_role_api_client().list_users()
    emails = [user.email for user in users]
    assert credentials.email not in emails


def test_generate_link_supports_sign_up_with_generate_confirmation_signup_link():
    credentials = mock_user_credentials()
    redirect_to = "http://localhost:9999/welcome"
    user_metadata = {"status": "alpha"}
    response = service_role_api_client().generate_link(
        {
            "type": "signup",
            "email": credentials.email,
            "password": credentials.password,
            "options": {
                "data": user_metadata,
                "redirect_to": redirect_to,
            },
        },
    )
    assert response.user.user_metadata == user_metadata


def test_generate_link_supports_updating_emails_with_generate_email_change_links():  # noqa: E501
    credentials = mock_user_credentials()
    user = create_new_user_with_email(email=credentials.email)
    assert user.email
    assert user.email == credentials.email
    credentials = mock_user_credentials()
    redirect_to = "http://localhost:9999/welcome"
    response = service_role_api_client().generate_link(
        {
            "type": "email_change_current",
            "email": user.email,
            "new_email": credentials.email,
            "options": {
                "redirect_to": redirect_to,
            },
        },
    )
    assert response.user.new_email == credentials.email


def test_invite_user_by_email_creates_a_new_user_with_an_invited_at_timestamp():
    credentials = mock_user_credentials()
    redirect_to = "http://localhost:9999/welcome"
    user_metadata = {"status": "alpha"}
    response = service_role_api_client().invite_user_by_email(
        credentials.email,
        {
            "data": user_metadata,
            "redirect_to": redirect_to,
        },
    )
    assert response.user.invited_at


def test_sign_out_with_an_valid_access_token():
    credentials = mock_user_credentials()
    client = auth_client_with_session()
    response = client.sign_up(
        {
            "email": credentials.email,
            "password": credentials.password,
        },
    )
    assert response.session
    service_role_api_client().sign_out(response.session.access_token)


def test_sign_out_with_an_invalid_access_token():
    try:
        service_role_api_client().sign_out("this-is-a-bad-token")
        assert False
    except AuthError:
        pass


def test_verify_otp_with_non_existent_phone_number():
    credentials = mock_user_credentials()
    otp = mock_verification_otp()
    try:
        client_api_auto_confirm_disabled_client().verify_otp(
            {
                "phone": credentials.phone,
                "token": otp,
                "type": "sms",
            },
        )
        assert False
    except AuthError as e:
        assert e.message == "Token has expired or is invalid"


def test_verify_otp_with_invalid_phone_number():
    credentials = mock_user_credentials()
    otp = mock_verification_otp()
    try:
        client_api_auto_confirm_disabled_client().verify_otp(
            {
                "phone": f"{credentials.phone}-invalid",
                "token": otp,
                "type": "sms",
            },
        )
        assert False
    except AuthError as e:
        assert e.message == "Invalid phone number format (E.164 required)"


def test_sign_in_with_id_token():
    try:
        (
            client_api_auto_confirm_off_signups_enabled_client().sign_in_with_id_token(
                {
                    "provider": "google",
                    "token": "123456",
                }
            )
        )
    except AuthApiError as e:
        assert e.to_dict()


def test_sign_in_with_sso():
    with pytest.raises(AuthApiError, match=r"SAML 2.0 is disabled") as exc:
        client_api_auto_confirm_off_signups_enabled_client().sign_in_with_sso(
            {
                "domain": "google",
            }
        )
    assert exc.value is not None


def test_sign_in_with_oauth():
    assert (
        client_api_auto_confirm_off_signups_enabled_client().sign_in_with_oauth(
            {
                "provider": "google",
            }
        )
    )


def test_link_identity_missing_session():
    with pytest.raises(AuthSessionMissingError) as exc:
        client_api_auto_confirm_off_signups_enabled_client().link_identity(
            {
                "provider": "google",
            }
        )
    assert exc.value is not None


def test_get_item_from_memory_storage():
    credentials = mock_user_credentials()
    client = auth_client()
    client.sign_up(
        {
            "email": credentials.email,
            "password": credentials.password,
        }
    )

    client.sign_in_with_password(
        {
            "email": credentials.email,
            "password": credentials.password,
        }
    )
    assert client._storage.get_item(client._storage_key) is not None


def test_remove_item_from_memory_storage():
    credentials = mock_user_credentials()
    client = auth_client()
    client.sign_up(
        {
            "email": credentials.email,
            "password": credentials.password,
        }
    )

    client.sign_in_with_password(
        {
            "email": credentials.email,
            "password": credentials.password,
        }
    )
    client._storage.remove_item(client._storage_key)


def test_list_factors():
    credentials = mock_user_credentials()
    client = auth_client()
    client.sign_up(
        {
            "email": credentials.email,
            "password": credentials.password,
        }
    )

    client.sign_in_with_password(
        {
            "email": credentials.email,
            "password": credentials.password,
        }
    )
    factors = client._list_factors()
    assert factors
    assert isinstance(factors.totp, list) and isinstance(factors.phone, list)


def test_start_auto_refresh_token():
    credentials = mock_user_credentials()
    client = auth_client()
    client._auto_refresh_token = True
    client.sign_up(
        {
            "email": credentials.email,
            "password": credentials.password,
        }
    )

    client.sign_in_with_password(
        {
            "email": credentials.email,
            "password": credentials.password,
        }
    )


def test_recover_and_refresh():
    credentials = mock_user_credentials()
    client = auth_client()
    client._auto_refresh_token = True
    client.sign_up(
        {
            "email": credentials.email,
            "password": credentials.password,
        }
    )

    client.sign_in_with_password(
        {
            "email": credentials.email,
            "password": credentials.password,
        }
    )
    client._recover_and_refresh()


def test_get_user_identities():
    credentials = mock_user_credentials()
    client = auth_client()
    client._auto_refresh_token = True
    client.sign_up(
        {
            "email": credentials.email,
            "password": credentials.password,
        }
    )

    client.sign_in_with_password(
        {
            "email": credentials.email,
            "password": credentials.password,
        }
    )
    assert (client.get_user_identities()).identities[0].identity_data[
        "email"
    ] == credentials.email


def test_update_user():
    credentials = mock_user_credentials()
    client = auth_client()
    client._auto_refresh_token = True
    client.sign_up(
        {
            "email": credentials.email,
            "password": credentials.password,
        }
    )
    client.update_user({"password": "123e5a"})
    client.sign_in_with_password(
        {
            "email": credentials.email,
            "password": "123e5a",
        }
    )


def test_create_user_with_app_metadata():
    app_metadata = mock_app_metadata()
    credentials = mock_user_credentials()
    response = service_role_api_client().create_user(
        {
            "email": credentials.email,
            "password": credentials.password,
            "app_metadata": app_metadata,
        }
    )
    assert response.user.email == credentials.email
    assert "provider" in response.user.app_metadata
    assert "providers" in response.user.app_metadata


def test_weak_email_password_error():
    credentials = mock_user_credentials()
    try:
        client_api_auto_confirm_off_signups_enabled_client().sign_up(
            {
                "email": credentials.email,
                "password": "123",
            }
        )
    except (AuthWeakPasswordError, AuthApiError) as e:
        assert e.to_dict()


def test_weak_phone_password_error():
    credentials = mock_user_credentials()
    try:
        client_api_auto_confirm_off_signups_enabled_client().sign_up(
            {
                "phone": credentials.phone,
                "password": "123",
            }
        )
    except (AuthWeakPasswordError, AuthApiError) as e:
        assert e.to_dict()


def test_get_user_by_id_invalid_id_raises_error():
    with pytest.raises(
        ValueError, match=r"Invalid id, 'invalid_id' is not a valid uuid"
    ):
        service_role_api_client().get_user_by_id("invalid_id")


def test_update_user_by_id_invalid_id_raises_error():
    with pytest.raises(
        ValueError, match=r"Invalid id, 'invalid_id' is not a valid uuid"
    ):
        service_role_api_client().update_user_by_id(
            "invalid_id", {"email": "test@test.com"}
        )


def test_delete_user_invalid_id_raises_error():
    with pytest.raises(
        ValueError, match=r"Invalid id, 'invalid_id' is not a valid uuid"
    ):
        service_role_api_client().delete_user("invalid_id")


def test_list_factors_invalid_id_raises_error():
    with pytest.raises(
        ValueError, match=r"Invalid id, 'invalid_id' is not a valid uuid"
    ):
        service_role_api_client()._list_factors({"user_id": "invalid_id"})


def test_delete_factor_invalid_id_raises_error():
    # invalid user id
    with pytest.raises(
        ValueError, match=r"Invalid id, 'invalid_id' is not a valid uuid"
    ):
        service_role_api_client()._delete_factor(
            {"user_id": "invalid_id", "id": "invalid_id"}
        )

    # valid user id, invalid factor id
    with pytest.raises(
        ValueError, match=r"Invalid id, 'invalid_id' is not a valid uuid"
    ):
        service_role_api_client()._delete_factor(
            {"user_id": str(uuid.uuid4()), "id": "invalid_id"}
        )


def test_create_oauth_client():
    """Test creating an OAuth client."""
    response = service_role_api_client().oauth.create_client(
        CreateOAuthClientParams(
            client_name="Test OAuth Client",
            redirect_uris=["https://example.com/callback"],
        )
    )
    assert response.client is not None
    assert response.client.client_name == "Test OAuth Client"
    assert response.client.client_id is not None


def test_list_oauth_clients():
    """Test listing OAuth clients."""
    response = service_role_api_client().oauth.list_clients()
    assert response.clients is not None
    assert isinstance(response.clients, list)


def test_get_oauth_client():
    """Test getting an OAuth client by ID."""
    # First create a client
    create_response = service_role_api_client().oauth.create_client(
        CreateOAuthClientParams(
            client_name="Test OAuth Client for Get",
            redirect_uris=["https://example.com/callback"],
        )
    )
    if create_response.client:
        client_id = create_response.client.client_id
        response = service_role_api_client().oauth.get_client(client_id)
        assert response.client is not None
        assert response.client.client_id == client_id


def test_delete_oauth_client():
    """Test deleting an OAuth client."""
    # First create a client
    create_response = service_role_api_client().oauth.create_client(
        CreateOAuthClientParams(
            client_name="Test OAuth Client for Delete",
            redirect_uris=["https://example.com/callback"],
        )
    )
    if create_response.client:
        client_id = create_response.client.client_id
        response = service_role_api_client().oauth.delete_client(client_id)
        # DELETE operations return an empty response
        assert response is not None


def test_regenerate_oauth_client_secret():
    """Test regenerating an OAuth client secret."""
    # First create a client
    create_response = service_role_api_client().oauth.create_client(
        CreateOAuthClientParams(
            client_name="Test OAuth Client for Regenerate",
            redirect_uris=["https://example.com/callback"],
        )
    )
    if create_response.client:
        client_id = create_response.client.client_id
        response = service_role_api_client().oauth.regenerate_client_secret(
            client_id
        )
        assert response.client is not None
        assert response.client.client_secret is not None
