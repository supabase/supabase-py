import uuid

import pytest

from supabase_auth.errors import (
    AuthApiError,
    AuthError,
    AuthInvalidCredentialsError,
    AuthSessionMissingError,
    AuthWeakPasswordError,
)

from .clients import (
    auth_client,
    auth_client_with_session,
    client_api_auto_confirm_disabled_client,
    client_api_auto_confirm_off_signups_enabled_client,
    service_role_api_client,
)
from .utils import (
    create_new_user_with_email,
    mock_app_metadata,
    mock_user_credentials,
    mock_user_metadata,
    mock_verification_otp,
)


async def test_create_user_should_create_a_new_user():
    credentials = mock_user_credentials()
    response = await create_new_user_with_email(email=credentials.get("email"))
    assert response.email == credentials.get("email")


async def test_create_user_with_user_metadata():
    user_metadata = mock_user_metadata()
    credentials = mock_user_credentials()
    response = await service_role_api_client().create_user(
        {
            "email": credentials.get("email"),
            "password": credentials.get("password"),
            "user_metadata": user_metadata,
        }
    )
    assert response.user.email == credentials.get("email")
    assert response.user.user_metadata == user_metadata
    assert "profile_image" in response.user.user_metadata


async def test_create_user_with_user_and_app_metadata():
    user_metadata = mock_user_metadata()
    app_metadata = mock_app_metadata()
    credentials = mock_user_credentials()
    response = await service_role_api_client().create_user(
        {
            "email": credentials.get("email"),
            "password": credentials.get("password"),
            "user_metadata": user_metadata,
            "app_metadata": app_metadata,
        }
    )
    assert response.user.email == credentials.get("email")
    assert "profile_image" in response.user.user_metadata
    assert "provider" in response.user.app_metadata
    assert "providers" in response.user.app_metadata


async def test_list_users_should_return_registered_users():
    credentials = mock_user_credentials()
    await create_new_user_with_email(email=credentials.get("email"))
    users = await service_role_api_client().list_users()
    assert users
    emails = [user.email for user in users]
    assert emails
    assert credentials.get("email") in emails


async def test_get_user_fetches_a_user_by_their_access_token():
    credentials = mock_user_credentials()
    auth_client_with_session_current_user = auth_client_with_session()
    response = await auth_client_with_session_current_user.sign_up(
        {
            "email": credentials.get("email"),
            "password": credentials.get("password"),
        }
    )
    assert response.session
    response = await auth_client_with_session_current_user.get_user()
    assert response.user.email == credentials.get("email")


async def test_get_user_by_id_should_a_registered_user_given_its_user_identifier():
    credentials = mock_user_credentials()
    user = await create_new_user_with_email(email=credentials.get("email"))
    assert user.id
    response = await service_role_api_client().get_user_by_id(user.id)
    assert response.user.email == credentials.get("email")


async def test_modify_email_using_update_user_by_id():
    credentials = mock_user_credentials()
    user = await create_new_user_with_email(email=credentials.get("email"))
    response = await service_role_api_client().update_user_by_id(
        user.id,
        {
            "email": f"new_{user.email}",
        },
    )
    assert response.user.email == f"new_{user.email}"


async def test_modify_user_metadata_using_update_user_by_id():
    credentials = mock_user_credentials()
    user = await create_new_user_with_email(email=credentials.get("email"))
    user_metadata = {"favorite_color": "yellow"}
    response = await service_role_api_client().update_user_by_id(
        user.id,
        {
            "user_metadata": user_metadata,
        },
    )
    assert response.user.email == user.email
    assert response.user.user_metadata == user_metadata


async def test_modify_app_metadata_using_update_user_by_id():
    credentials = mock_user_credentials()
    user = await create_new_user_with_email(email=credentials.get("email"))
    app_metadata = {"roles": ["admin", "publisher"]}
    response = await service_role_api_client().update_user_by_id(
        user.id,
        {
            "app_metadata": app_metadata,
        },
    )
    assert response.user.email == user.email
    assert "roles" in response.user.app_metadata


async def test_modify_confirm_email_using_update_user_by_id():
    credentials = mock_user_credentials()
    response = await client_api_auto_confirm_off_signups_enabled_client().sign_up(
        {
            "email": credentials.get("email"),
            "password": credentials.get("password"),
        }
    )
    assert response.user
    assert not response.user.email_confirmed_at
    response = await service_role_api_client().update_user_by_id(
        response.user.id,
        {
            "email_confirm": True,
        },
    )
    assert response.user.email_confirmed_at


async def test_invalid_credential_sign_in_with_phone():
    try:
        response = await client_api_auto_confirm_off_signups_enabled_client().sign_in_with_password(
            {
                "phone": "+123456789",
                "password": "strong_pwd",
            }
        )
    except AuthApiError as e:
        assert e.to_dict()


async def test_invalid_credential_sign_in_with_email():
    try:
        response = await client_api_auto_confirm_off_signups_enabled_client().sign_in_with_password(
            {
                "email": "unknown_user@unknowndomain.com",
                "password": "strong_pwd",
            }
        )
    except AuthApiError as e:
        assert e.to_dict()


async def test_sign_in_with_otp_email():
    try:
        await client_api_auto_confirm_off_signups_enabled_client().sign_in_with_otp(
            {
                "email": "unknown_user@unknowndomain.com",
            }
        )
    except AuthApiError as e:
        assert e.to_dict()


async def test_sign_in_with_otp_phone():
    try:
        await client_api_auto_confirm_off_signups_enabled_client().sign_in_with_otp(
            {
                "phone": "+112345678",
            }
        )
    except AuthApiError as e:
        assert e.to_dict()


async def test_resend():
    try:
        await client_api_auto_confirm_off_signups_enabled_client().resend(
            {"phone": "+112345678", "type": "sms"}
        )
    except AuthApiError as e:
        assert e.to_dict()


async def test_reauthenticate():
    try:
        response = await auth_client_with_session().reauthenticate()
    except AuthSessionMissingError:
        pass


async def test_refresh_session():
    try:
        response = await auth_client_with_session().refresh_session()
    except AuthSessionMissingError:
        pass


async def test_reset_password_for_email():
    credentials = mock_user_credentials()
    try:
        response = await auth_client_with_session().reset_password_email(
            email=credentials.get("email")
        )
    except AuthSessionMissingError:
        pass


async def test_resend_missing_credentials():
    try:
        await client_api_auto_confirm_off_signups_enabled_client().resend(
            {"type": "email_change"}
        )
    except AuthInvalidCredentialsError as e:
        assert e.to_dict()


async def test_sign_in_anonymously():
    try:
        response = await auth_client_with_session().sign_in_anonymously()
        assert response
    except AuthApiError:
        pass


async def test_delete_user_should_be_able_delete_an_existing_user():
    credentials = mock_user_credentials()
    user = await create_new_user_with_email(email=credentials.get("email"))
    await service_role_api_client().delete_user(user.id)
    users = await service_role_api_client().list_users()
    emails = [user.email for user in users]
    assert credentials.get("email") not in emails


async def test_generate_link_supports_sign_up_with_generate_confirmation_signup_link():
    credentials = mock_user_credentials()
    redirect_to = "http://localhost:9999/welcome"
    user_metadata = {"status": "alpha"}
    response = await service_role_api_client().generate_link(
        {
            "type": "signup",
            "email": credentials.get("email"),
            "password": credentials.get("password"),
            "options": {
                "data": user_metadata,
                "redirect_to": redirect_to,
            },
        },
    )
    assert response.user.user_metadata == user_metadata


async def test_generate_link_supports_updating_emails_with_generate_email_change_links():  # noqa: E501
    credentials = mock_user_credentials()
    user = await create_new_user_with_email(email=credentials.get("email"))
    assert user.email
    assert user.email == credentials.get("email")
    credentials = mock_user_credentials()
    redirect_to = "http://localhost:9999/welcome"
    response = await service_role_api_client().generate_link(
        {
            "type": "email_change_current",
            "email": user.email,
            "new_email": credentials.get("email"),
            "options": {
                "redirect_to": redirect_to,
            },
        },
    )
    assert response.user.new_email == credentials.get("email")


async def test_invite_user_by_email_creates_a_new_user_with_an_invited_at_timestamp():
    credentials = mock_user_credentials()
    redirect_to = "http://localhost:9999/welcome"
    user_metadata = {"status": "alpha"}
    response = await service_role_api_client().invite_user_by_email(
        credentials.get("email"),
        {
            "data": user_metadata,
            "redirect_to": redirect_to,
        },
    )
    assert response.user.invited_at


async def test_sign_out_with_an_valid_access_token():
    credentials = mock_user_credentials()
    response = await auth_client_with_session().sign_up(
        {
            "email": credentials.get("email"),
            "password": credentials.get("password"),
        },
    )
    assert response.session
    response = await service_role_api_client().sign_out(response.session.access_token)


async def test_sign_out_with_an_invalid_access_token():
    try:
        await service_role_api_client().sign_out("this-is-a-bad-token")
        assert False
    except AuthError:
        pass


async def test_verify_otp_with_non_existent_phone_number():
    credentials = mock_user_credentials()
    otp = mock_verification_otp()
    try:
        await client_api_auto_confirm_disabled_client().verify_otp(
            {
                "phone": credentials.get("phone"),
                "token": otp,
                "type": "sms",
            },
        )
        assert False
    except AuthError as e:
        assert e.message == "Token has expired or is invalid"


async def test_verify_otp_with_invalid_phone_number():
    credentials = mock_user_credentials()
    otp = mock_verification_otp()
    try:
        await client_api_auto_confirm_disabled_client().verify_otp(
            {
                "phone": f"{credentials.get('phone')}-invalid",
                "token": otp,
                "type": "sms",
            },
        )
        assert False
    except AuthError as e:
        assert e.message == "Invalid phone number format (E.164 required)"


async def test_sign_in_with_id_token():
    try:
        await (
            client_api_auto_confirm_off_signups_enabled_client().sign_in_with_id_token(
                {
                    "provider": "google",
                    "token": "123456",
                }
            )
        )
    except AuthApiError as e:
        assert e.to_dict()


async def test_sign_in_with_sso():
    with pytest.raises(AuthApiError, match=r"SAML 2.0 is disabled") as exc:
        await client_api_auto_confirm_off_signups_enabled_client().sign_in_with_sso(
            {
                "domain": "google",
            }
        )
    assert exc.value is not None


async def test_sign_in_with_oauth():
    assert (
        await client_api_auto_confirm_off_signups_enabled_client().sign_in_with_oauth(
            {
                "provider": "google",
            }
        )
    )


async def test_link_identity_missing_session():
    with pytest.raises(AuthSessionMissingError) as exc:
        await client_api_auto_confirm_off_signups_enabled_client().link_identity(
            {
                "provider": "google",
            }
        )
    assert exc.value is not None


async def test_get_item_from_memory_storage():
    credentials = mock_user_credentials()
    client = auth_client()
    await client.sign_up(
        {
            "email": credentials.get("email"),
            "password": credentials.get("password"),
        }
    )

    await client.sign_in_with_password(
        {
            "email": credentials.get("email"),
            "password": credentials.get("password"),
        }
    )
    assert await client._storage.get_item(client._storage_key) is not None


async def test_remove_item_from_memory_storage():
    credentials = mock_user_credentials()
    client = auth_client()
    await client.sign_up(
        {
            "email": credentials.get("email"),
            "password": credentials.get("password"),
        }
    )

    await client.sign_in_with_password(
        {
            "email": credentials.get("email"),
            "password": credentials.get("password"),
        }
    )
    await client._storage.remove_item(client._storage_key)
    assert client._storage_key not in client._storage.storage


async def test_list_factors():
    credentials = mock_user_credentials()
    client = auth_client()
    await client.sign_up(
        {
            "email": credentials.get("email"),
            "password": credentials.get("password"),
        }
    )

    await client.sign_in_with_password(
        {
            "email": credentials.get("email"),
            "password": credentials.get("password"),
        }
    )
    factors = await client._list_factors()
    assert factors
    assert isinstance(factors.totp, list) and isinstance(factors.phone, list)


async def test_start_auto_refresh_token():
    credentials = mock_user_credentials()
    client = auth_client()
    client._auto_refresh_token = True
    await client.sign_up(
        {
            "email": credentials.get("email"),
            "password": credentials.get("password"),
        }
    )

    await client.sign_in_with_password(
        {
            "email": credentials.get("email"),
            "password": credentials.get("password"),
        }
    )

    assert await client._start_auto_refresh_token(2.0) is None


async def test_recover_and_refresh():
    credentials = mock_user_credentials()
    client = auth_client()
    client._auto_refresh_token = True
    await client.sign_up(
        {
            "email": credentials.get("email"),
            "password": credentials.get("password"),
        }
    )

    await client.sign_in_with_password(
        {
            "email": credentials.get("email"),
            "password": credentials.get("password"),
        }
    )
    await client._recover_and_refresh()
    assert client._storage_key in client._storage.storage


async def test_get_user_identities():
    credentials = mock_user_credentials()
    client = auth_client()
    client._auto_refresh_token = True
    await client.sign_up(
        {
            "email": credentials.get("email"),
            "password": credentials.get("password"),
        }
    )

    await client.sign_in_with_password(
        {
            "email": credentials.get("email"),
            "password": credentials.get("password"),
        }
    )
    assert (await client.get_user_identities()).identities[0].identity_data[
        "email"
    ] == credentials.get("email")


async def test_update_user():
    credentials = mock_user_credentials()
    client = auth_client()
    client._auto_refresh_token = True
    await client.sign_up(
        {
            "email": credentials.get("email"),
            "password": credentials.get("password"),
        }
    )
    await client.update_user({"password": "123e5a"})
    await client.sign_in_with_password(
        {
            "email": credentials.get("email"),
            "password": "123e5a",
        }
    )


async def test_create_user_with_app_metadata():
    app_metadata = mock_app_metadata()
    credentials = mock_user_credentials()
    response = await service_role_api_client().create_user(
        {
            "email": credentials.get("email"),
            "password": credentials.get("password"),
            "app_metadata": app_metadata,
        }
    )
    assert response.user.email == credentials.get("email")
    assert "provider" in response.user.app_metadata
    assert "providers" in response.user.app_metadata


async def test_weak_email_password_error():
    credentials = mock_user_credentials()
    try:
        await client_api_auto_confirm_off_signups_enabled_client().sign_up(
            {
                "email": credentials.get("email"),
                "password": "123",
            }
        )
    except (AuthWeakPasswordError, AuthApiError) as e:
        assert e.to_dict()


async def test_weak_phone_password_error():
    credentials = mock_user_credentials()
    try:
        await client_api_auto_confirm_off_signups_enabled_client().sign_up(
            {
                "phone": credentials.get("phone"),
                "password": "123",
            }
        )
    except (AuthWeakPasswordError, AuthApiError) as e:
        assert e.to_dict()


async def test_get_user_by_id_invalid_id_raises_error():
    with pytest.raises(
        ValueError, match=r"Invalid id, 'invalid_id' is not a valid uuid"
    ):
        await service_role_api_client().get_user_by_id("invalid_id")


async def test_update_user_by_id_invalid_id_raises_error():
    with pytest.raises(
        ValueError, match=r"Invalid id, 'invalid_id' is not a valid uuid"
    ):
        await service_role_api_client().update_user_by_id(
            "invalid_id", {"email": "test@test.com"}
        )


async def test_delete_user_invalid_id_raises_error():
    with pytest.raises(
        ValueError, match=r"Invalid id, 'invalid_id' is not a valid uuid"
    ):
        await service_role_api_client().delete_user("invalid_id")


async def test_list_factors_invalid_id_raises_error():
    with pytest.raises(
        ValueError, match=r"Invalid id, 'invalid_id' is not a valid uuid"
    ):
        await service_role_api_client()._list_factors({"user_id": "invalid_id"})


async def test_delete_factor_invalid_id_raises_error():
    # invalid user id
    with pytest.raises(
        ValueError, match=r"Invalid id, 'invalid_id' is not a valid uuid"
    ):
        await service_role_api_client()._delete_factor(
            {"user_id": "invalid_id", "id": "invalid_id"}
        )

    # valid user id, invalid factor id
    with pytest.raises(
        ValueError, match=r"Invalid id, 'invalid_id' is not a valid uuid"
    ):
        await service_role_api_client()._delete_factor(
            {"user_id": str(uuid.uuid4()), "id": "invalid_id"}
        )
