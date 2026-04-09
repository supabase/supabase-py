from supabase_auth import SyncSupabaseAuthAdmin, SyncSupabaseAuthClient
from supabase_auth.types import (
    AdminUserAttributes,
    CreateOAuthClientParams,
    GenerateLinkParams,
    MFAEnroll,
    Resend,
    SignInWithPassword,
    SignUpWithPassword,
    UpdateOAuthClientParams,
    UserAttributes,
)

from .conftest import (
    create_new_user_with_email,
    mock_app_metadata,
    mock_user_credentials,
    mock_user_metadata,
)


def test_create_user_should_create_a_new_user(
    service_role_api_client: SyncSupabaseAuthAdmin,
) -> None:
    credentials = mock_user_credentials()
    response = create_new_user_with_email(
        service_role_api_client, email=credentials.email
    )
    assert response.email == credentials.email


def test_create_user_with_user_metadata(
    service_role_api_client: SyncSupabaseAuthAdmin,
) -> None:
    user_metadata = mock_user_metadata()
    credentials = mock_user_credentials()
    response = service_role_api_client.create_user(
        AdminUserAttributes(
            email=credentials.email,
            password=credentials.password,
            user_metadata=user_metadata,
        )
    )
    assert response.user.email == credentials.email
    assert response.user.user_metadata == user_metadata
    assert "profile_image" in response.user.user_metadata


def test_create_user_with_user_and_app_metadata(
    service_role_api_client: SyncSupabaseAuthAdmin,
) -> None:
    user_metadata = mock_user_metadata()
    app_metadata = mock_app_metadata()
    credentials = mock_user_credentials()
    response = service_role_api_client.create_user(
        AdminUserAttributes(
            email=credentials.email,
            password=credentials.password,
            user_metadata=user_metadata,
            app_metadata=app_metadata,
        )
    )
    assert response.user.email == credentials.email
    assert "profile_image" in response.user.user_metadata
    assert "provider" in response.user.app_metadata
    assert "providers" in response.user.app_metadata


def test_list_users_should_return_registered_users(
    service_role_api_client: SyncSupabaseAuthAdmin,
) -> None:
    credentials = mock_user_credentials()
    create_new_user_with_email(service_role_api_client, email=credentials.email)
    users = service_role_api_client.list_users()
    assert users
    emails = [user.email for user in users]
    assert emails
    assert credentials.email in emails


def test_get_user_by_id_should_a_registered_user_given_its_user_identifier(
    service_role_api_client: SyncSupabaseAuthAdmin,
) -> None:
    credentials = mock_user_credentials()
    user = create_new_user_with_email(service_role_api_client, email=credentials.email)
    assert user.id
    response = service_role_api_client.get_user_by_id(user.id)
    assert response.user.email == credentials.email


def test_modify_email_using_update_user_by_id(
    service_role_api_client: SyncSupabaseAuthAdmin,
) -> None:
    credentials = mock_user_credentials()
    user = create_new_user_with_email(service_role_api_client, email=credentials.email)
    response = service_role_api_client.update_user_by_id(
        user.id,
        AdminUserAttributes(
            email=f"new_{user.email}",
        ),
    )
    assert response.user.email == f"new_{user.email}"


def test_modify_user_metadata_using_update_user_by_id(
    service_role_api_client: SyncSupabaseAuthAdmin,
) -> None:
    credentials = mock_user_credentials()
    user = create_new_user_with_email(service_role_api_client, email=credentials.email)
    user_metadata = {"favorite_color": "yellow"}
    response = service_role_api_client.update_user_by_id(
        user.id,
        AdminUserAttributes(
            user_metadata=user_metadata,
        ),
    )
    assert response.user.email == user.email
    assert response.user.user_metadata == user_metadata


def test_modify_app_metadata_using_update_user_by_id(
    service_role_api_client: SyncSupabaseAuthAdmin,
) -> None:
    credentials = mock_user_credentials()
    user = create_new_user_with_email(service_role_api_client, email=credentials.email)
    app_metadata = {"roles": ["admin", "publisher"]}
    response = service_role_api_client.update_user_by_id(
        user.id,
        AdminUserAttributes(
            app_metadata=app_metadata,
        ),
    )
    assert response.user.email == user.email
    assert "roles" in response.user.app_metadata


def test_modify_confirm_email_using_update_user_by_id(
    service_role_api_client: SyncSupabaseAuthAdmin,
    client_api_auto_confirm_off_signups_enabled_client: SyncSupabaseAuthClient,
) -> None:
    credentials = mock_user_credentials()
    response = client_api_auto_confirm_off_signups_enabled_client.sign_up(
        SignUpWithPassword.email(
            email=credentials.email,
            password=credentials.password,
        )
    )
    assert response.user
    assert not response.user.email_confirmed_at
    auth_response = service_role_api_client.update_user_by_id(
        response.user.id,
        AdminUserAttributes(
            email_confirm=True,
        ),
    )
    assert auth_response.user.email_confirmed_at


def test_resend(
    client_api_auto_confirm_off_signups_enabled_client: SyncSupabaseAuthClient,
) -> None:
    client_api_auto_confirm_off_signups_enabled_client.resend(
        Resend.phone(phone="+112345678", type="sms")
    )


def test_reauthenticate(auth_client_with_session: SyncSupabaseAuthClient) -> None:
    auth_client_with_session.reauthenticate()


def test_refresh_session(auth_client_with_session: SyncSupabaseAuthClient) -> None:
    auth_client_with_session.refresh_session()


def test_reset_password_for_email(
    auth_client_with_session: SyncSupabaseAuthClient,
) -> None:
    credentials = mock_user_credentials()
    auth_client_with_session.reset_password_for_email(email=credentials.email)


def test_resend_missing_credentials(
    client_api_auto_confirm_off_signups_enabled_client: SyncSupabaseAuthClient,
) -> None:
    credentials = mock_user_credentials()
    client_api_auto_confirm_off_signups_enabled_client.resend(
        Resend.email(type="email_change", email=credentials.email)
    )


def test_sign_in_anonymously(auth_client_with_session: SyncSupabaseAuthClient) -> None:
    auth_client_with_session.sign_in_anonymously()


def test_delete_user_should_be_able_delete_an_existing_user(
    service_role_api_client: SyncSupabaseAuthAdmin,
) -> None:
    credentials = mock_user_credentials()
    user = create_new_user_with_email(service_role_api_client, email=credentials.email)
    service_role_api_client.delete_user(user.id)
    users = service_role_api_client.list_users()
    emails = [user.email for user in users]
    assert credentials.email not in emails


def test_generate_link_supports_sign_up_with_generate_confirmation_signup_link(
    service_role_api_client: SyncSupabaseAuthAdmin,
) -> None:
    credentials = mock_user_credentials()
    redirect_to = "http://localhost:9999/welcome"
    user_metadata = {"status": "alpha"}
    response = service_role_api_client.generate_link(
        GenerateLinkParams.sign_up(
            email=credentials.email,
            password=credentials.password,
            data=user_metadata,
            redirect_to=redirect_to,
        )
    )
    assert response.user.user_metadata == user_metadata


def test_generate_link_supports_updating_emails_with_generate_email_change_links(
    service_role_api_client: SyncSupabaseAuthAdmin,
) -> None:  # noqa: E501
    credentials = mock_user_credentials()
    user = create_new_user_with_email(service_role_api_client, email=credentials.email)
    assert user.email
    assert user.email == credentials.email
    credentials = mock_user_credentials()
    redirect_to = "http://localhost:9999/welcome"
    response = service_role_api_client.generate_link(
        GenerateLinkParams.email_change_current(
            email=user.email,
            new_email=credentials.email,
            redirect_to=redirect_to,
        )
    )
    assert response.user.new_email == credentials.email


def test_invite_user_by_email_creates_a_new_user_with_an_invited_at_timestamp(
    service_role_api_client: SyncSupabaseAuthAdmin,
) -> None:
    credentials = mock_user_credentials()
    redirect_to = "http://localhost:9999/welcome"
    user_metadata = {"status": "alpha"}
    response = service_role_api_client.invite_user_by_email(
        credentials.email,
        data=user_metadata,
        redirect_to=redirect_to,
    )
    assert response.user.invited_at


def test_sign_in_with_oauth(
    client_api_auto_confirm_off_signups_enabled_client: SyncSupabaseAuthClient,
) -> None:
    assert client_api_auto_confirm_off_signups_enabled_client.sign_in_with_oauth(
        provider="google"
    )


def test_get_item_from_memory_storage(auth_client: SyncSupabaseAuthClient) -> None:
    credentials = mock_user_credentials()
    auth_client.sign_up(
        SignUpWithPassword.email(
            email=credentials.email,
            password=credentials.password,
        )
    )

    auth_client.sign_in_with_password(
        SignInWithPassword.email(
            email=credentials.email,
            password=credentials.password,
        )
    )
    assert (
        auth_client.session_manager.storage.get_item(
            auth_client.session_manager.storage_key
        )
        is not None
    )


def test_recover_and_refresh(auth_client: SyncSupabaseAuthClient) -> None:
    credentials = mock_user_credentials()
    auth_client.session_manager.auto_refresh_token = True
    auth_client.sign_up(
        SignUpWithPassword.email(
            email=credentials.email,
            password=credentials.password,
        )
    )

    auth_client.sign_in_with_password(
        SignInWithPassword.email(
            email=credentials.email,
            password=credentials.password,
        )
    )
    auth_client.session_manager.recover_and_refresh()
    assert (auth_client.get_user_identities()).identities[0].identity_data[
        "email"
    ] == credentials.email


def test_update_user(auth_client: SyncSupabaseAuthClient) -> None:
    credentials = mock_user_credentials()
    auth_client.session_manager.auto_refresh_token = True
    auth_client.sign_up(
        SignUpWithPassword.email(
            email=credentials.email,
            password=credentials.password,
        )
    )
    auth_client.update_user(UserAttributes(password="123e5a"))
    auth_client.sign_in_with_password(
        SignInWithPassword.email(
            email=credentials.email,
            password="123e5a",
        )
    )


def test_create_user_with_app_metadata(
    service_role_api_client: SyncSupabaseAuthAdmin,
) -> None:
    app_metadata = mock_app_metadata()
    credentials = mock_user_credentials()
    response = service_role_api_client.create_user(
        AdminUserAttributes(
            email=credentials.email,
            password=credentials.password,
            app_metadata=app_metadata,
        )
    )
    assert response.user.email == credentials.email
    assert "provider" in response.user.app_metadata
    assert "providers" in response.user.app_metadata


def test_admin_list_factors(
    auth_client: SyncSupabaseAuthClient, service_role_api_client: SyncSupabaseAuthAdmin
) -> None:
    import pyotp

    credentials = mock_user_credentials()
    auth_client.sign_up(
        SignUpWithPassword.email(
            email=credentials.email,
            password=credentials.password,
        )
    )

    auth_response = auth_client.sign_in_with_password(
        SignInWithPassword.email(
            email=credentials.email,
            password=credentials.password,
        )
    )
    assert auth_response.user
    enroll_response = auth_client.mfa.enroll(MFAEnroll.totp(friendly_name="test_otp"))
    assert enroll_response.totp
    totp = pyotp.TOTP(enroll_response.totp.secret)
    res = auth_client.mfa.challenge_and_verify(
        factor_id=enroll_response.id,
        code=totp.now(),
    )
    factors = service_role_api_client.mfa.list_factors(
        user_id=res.user.id,
    )
    assert factors[0].friendly_name == "test_otp"
    assert factors[0].factor_type == "totp"
    assert factors[0].status == "verified"
    service_role_api_client.mfa.delete_factor(
        factor_id=factors[0].id,
        user_id=res.user.id,
    )
    factors = service_role_api_client.mfa.list_factors(user_id=res.user.id)
    assert len(factors) == 0


def test_create_oauth_client(service_role_api_client: SyncSupabaseAuthAdmin) -> None:
    """Test creating an OAuth client."""
    response = service_role_api_client.oauth.create_client(
        CreateOAuthClientParams(
            client_name="Test OAuth Client",
            redirect_uris=["https://example.com/callback"],
        )
    )
    assert response.client is not None
    assert response.client.client_name == "Test OAuth Client"
    assert response.client.client_id is not None


def test_list_oauth_clients(service_role_api_client: SyncSupabaseAuthAdmin) -> None:
    """Test listing OAuth clients."""
    service_role_api_client.oauth.create_client(
        CreateOAuthClientParams(
            client_name="Test OAuth Client",
            redirect_uris=["https://example.com/callback"],
        )
    )
    response = service_role_api_client.oauth.list_clients()
    assert len(response.clients) > 0
    assert any(client.client_name == "Test OAuth Client" for client in response.clients)
    assert any(client.client_id is not None for client in response.clients)


def test_get_oauth_client(service_role_api_client: SyncSupabaseAuthAdmin) -> None:
    """Test getting an OAuth client by ID."""
    # First create a client
    create_response = service_role_api_client.oauth.create_client(
        CreateOAuthClientParams(
            client_name="Test OAuth Client for Get",
            redirect_uris=["https://example.com/callback"],
        )
    )
    if create_response.client:
        client_id = create_response.client.client_id
        response = service_role_api_client.oauth.get_client(client_id)
        assert response.client is not None
        assert response.client.client_id == client_id


# Server is not yet released, so this test is not yet relevant.
def test_update_oauth_client(service_role_api_client: SyncSupabaseAuthAdmin) -> None:
    """Test updating an OAuth client."""
    # First create a client
    create_response = service_role_api_client.oauth.create_client(
        CreateOAuthClientParams(
            client_name="Test OAuth Client for Update",
            redirect_uris=["https://example.com/callback"],
        )
    )
    assert create_response.client is not None
    client_id = create_response.client.client_id
    response = service_role_api_client.oauth.update_client(
        client_id,
        UpdateOAuthClientParams(
            client_name="Updated Test OAuth Client",
        ),
    )
    assert response.client is not None
    assert response.client.client_name == "Updated Test OAuth Client"


def test_delete_oauth_client(service_role_api_client: SyncSupabaseAuthAdmin) -> None:
    """Test deleting an OAuth client."""
    # First create a client
    create_response = service_role_api_client.oauth.create_client(
        CreateOAuthClientParams(
            client_name="Test OAuth Client for Delete",
            redirect_uris=["https://example.com/callback"],
        )
    )
    assert create_response.client is not None
    client_id = create_response.client.client_id
    service_role_api_client.oauth.delete_client(client_id)


def test_regenerate_oauth_client_secret(
    service_role_api_client: SyncSupabaseAuthAdmin,
) -> None:
    """Test regenerating an OAuth client secret."""
    # First create a client
    create_response = service_role_api_client.oauth.create_client(
        CreateOAuthClientParams(
            client_name="Test OAuth Client for Regenerate",
            redirect_uris=["https://example.com/callback"],
        )
    )
    if create_response.client:
        client_id = create_response.client.client_id
        response = service_role_api_client.oauth.regenerate_client_secret(client_id)
        assert response.client is not None
        assert response.client.client_secret is not None
