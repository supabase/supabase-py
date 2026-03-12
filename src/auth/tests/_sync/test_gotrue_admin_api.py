from supabase_auth.types import (
    AdminUserAttributes,
    CreateOAuthClientParams,
    GenerateLinkParams,
    Resend,
    SignInWithPassword,
    SignUpWithPassword,
    UserAttributes,
)

from .clients import (
    auth_client,
    auth_client_with_session,
    client_api_auto_confirm_off_signups_enabled_client,
    create_new_user_with_email,
    mock_app_metadata,
    mock_user_credentials,
    mock_user_metadata,
    service_role_api_client,
)


def test_create_user_should_create_a_new_user() -> None:
    credentials = mock_user_credentials()
    response = create_new_user_with_email(email=credentials.email)
    assert response.email == credentials.email


def test_create_user_with_user_metadata() -> None:
    user_metadata = mock_user_metadata()
    credentials = mock_user_credentials()
    response = service_role_api_client().create_user(
        AdminUserAttributes(
            email=credentials.email,
            password=credentials.password,
            user_metadata=user_metadata,
        )
    )
    assert response.user.email == credentials.email
    assert response.user.user_metadata == user_metadata
    assert "profile_image" in response.user.user_metadata


def test_create_user_with_user_and_app_metadata() -> None:
    user_metadata = mock_user_metadata()
    app_metadata = mock_app_metadata()
    credentials = mock_user_credentials()
    response = service_role_api_client().create_user(
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


def test_list_users_should_return_registered_users() -> None:
    credentials = mock_user_credentials()
    create_new_user_with_email(email=credentials.email)
    users = service_role_api_client().list_users()
    assert users
    emails = [user.email for user in users]
    assert emails
    assert credentials.email in emails


def test_get_user_by_id_should_a_registered_user_given_its_user_identifier() -> None:
    credentials = mock_user_credentials()
    user = create_new_user_with_email(email=credentials.email)
    assert user.id
    response = service_role_api_client().get_user_by_id(user.id)
    assert response.user.email == credentials.email


def test_modify_email_using_update_user_by_id() -> None:
    credentials = mock_user_credentials()
    user = create_new_user_with_email(email=credentials.email)
    response = service_role_api_client().update_user_by_id(
        user.id,
        AdminUserAttributes(
            email=f"new_{user.email}",
        ),
    )
    assert response.user.email == f"new_{user.email}"


def test_modify_user_metadata_using_update_user_by_id() -> None:
    credentials = mock_user_credentials()
    user = create_new_user_with_email(email=credentials.email)
    user_metadata = {"favorite_color": "yellow"}
    response = service_role_api_client().update_user_by_id(
        user.id,
        AdminUserAttributes(
            user_metadata=user_metadata,
        ),
    )
    assert response.user.email == user.email
    assert response.user.user_metadata == user_metadata


def test_modify_app_metadata_using_update_user_by_id() -> None:
    credentials = mock_user_credentials()
    user = create_new_user_with_email(email=credentials.email)
    app_metadata = {"roles": ["admin", "publisher"]}
    response = service_role_api_client().update_user_by_id(
        user.id,
        AdminUserAttributes(
            app_metadata=app_metadata,
        ),
    )
    assert response.user.email == user.email
    assert "roles" in response.user.app_metadata


def test_modify_confirm_email_using_update_user_by_id() -> None:
    credentials = mock_user_credentials()
    response = client_api_auto_confirm_off_signups_enabled_client().sign_up(
        SignUpWithPassword.email(
            email=credentials.email,
            password=credentials.password,
        )
    )
    assert response.user
    assert not response.user.email_confirmed_at
    auth_response = service_role_api_client().update_user_by_id(
        response.user.id,
        AdminUserAttributes(
            email_confirm=True,
        ),
    )
    assert auth_response.user.email_confirmed_at


def test_resend() -> None:
    client_api_auto_confirm_off_signups_enabled_client().resend(
        Resend.phone(phone="+112345678", type="sms")
    )


def test_reauthenticate() -> None:
    client = auth_client_with_session()
    client.reauthenticate()


def test_refresh_session() -> None:
    client = auth_client_with_session()
    client.refresh_session()


def test_reset_password_for_email() -> None:
    credentials = mock_user_credentials()
    client = auth_client_with_session()
    client.reset_password_for_email(email=credentials.email)


def test_resend_missing_credentials() -> None:
    credentials = mock_user_credentials()
    client_api_auto_confirm_off_signups_enabled_client().resend(
        Resend.email(type="email_change", email=credentials.email)
    )


def test_sign_in_anonymously() -> None:
    client = auth_client_with_session()
    client.sign_in_anonymously()


def test_delete_user_should_be_able_delete_an_existing_user() -> None:
    credentials = mock_user_credentials()
    user = create_new_user_with_email(email=credentials.email)
    service_role_api_client().delete_user(user.id)
    users = service_role_api_client().list_users()
    emails = [user.email for user in users]
    assert credentials.email not in emails


def test_generate_link_supports_sign_up_with_generate_confirmation_signup_link() -> (
    None
):
    credentials = mock_user_credentials()
    redirect_to = "http://localhost:9999/welcome"
    user_metadata = {"status": "alpha"}
    response = service_role_api_client().generate_link(
        GenerateLinkParams.sign_up(
            email=credentials.email,
            password=credentials.password,
            data=user_metadata,
            redirect_to=redirect_to,
        )
    )
    assert response.user.user_metadata == user_metadata


def test_generate_link_supports_updating_emails_with_generate_email_change_links() -> (
    None
):  # noqa: E501
    credentials = mock_user_credentials()
    user = create_new_user_with_email(email=credentials.email)
    assert user.email
    assert user.email == credentials.email
    credentials = mock_user_credentials()
    redirect_to = "http://localhost:9999/welcome"
    response = service_role_api_client().generate_link(
        GenerateLinkParams.email_change_current(
            email=user.email,
            new_email=credentials.email,
            redirect_to=redirect_to,
        )
    )
    assert response.user.new_email == credentials.email


def test_invite_user_by_email_creates_a_new_user_with_an_invited_at_timestamp() -> None:
    credentials = mock_user_credentials()
    redirect_to = "http://localhost:9999/welcome"
    user_metadata = {"status": "alpha"}
    response = service_role_api_client().invite_user_by_email(
        credentials.email,
        data=user_metadata,
        redirect_to=redirect_to,
    )
    assert response.user.invited_at


def test_sign_out_with_an_valid_access_token() -> None:
    client = auth_client_with_session()
    session = client.get_session()
    assert session
    service_role_api_client().sign_out(session.access_token)


def test_sign_in_with_oauth() -> None:
    assert client_api_auto_confirm_off_signups_enabled_client().sign_in_with_oauth(
        provider="google"
    )


def test_get_item_from_memory_storage() -> None:
    credentials = mock_user_credentials()
    client = auth_client()
    client.sign_up(
        SignUpWithPassword.email(
            email=credentials.email,
            password=credentials.password,
        )
    )

    client.sign_in_with_password(
        SignInWithPassword.email(
            email=credentials.email,
            password=credentials.password,
        )
    )
    assert (
        client.session_manager.storage.get_item(client.session_manager.storage_key)
        is not None
    )


def test_recover_and_refresh() -> None:
    credentials = mock_user_credentials()
    client = auth_client()
    client.session_manager.auto_refresh_token = True
    client.sign_up(
        SignUpWithPassword.email(
            email=credentials.email,
            password=credentials.password,
        )
    )

    client.sign_in_with_password(
        SignInWithPassword.email(
            email=credentials.email,
            password=credentials.password,
        )
    )
    client.session_manager.recover_and_refresh()
    assert (client.get_user_identities()).identities[0].identity_data[
        "email"
    ] == credentials.email


def test_update_user() -> None:
    credentials = mock_user_credentials()
    client = auth_client()
    client.session_manager.auto_refresh_token = True
    client.sign_up(
        SignUpWithPassword.email(
            email=credentials.email,
            password=credentials.password,
        )
    )
    client.update_user(UserAttributes(password="123e5a"))
    client.sign_in_with_password(
        SignInWithPassword.email(
            email=credentials.email,
            password="123e5a",
        )
    )


def test_create_user_with_app_metadata() -> None:
    app_metadata = mock_app_metadata()
    credentials = mock_user_credentials()
    response = service_role_api_client().create_user(
        AdminUserAttributes(
            email=credentials.email,
            password=credentials.password,
            app_metadata=app_metadata,
        )
    )
    assert response.user.email == credentials.email
    assert "provider" in response.user.app_metadata
    assert "providers" in response.user.app_metadata


def test_create_oauth_client() -> None:
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


def test_list_oauth_clients() -> None:
    """Test listing OAuth clients."""
    client = service_role_api_client()
    client.oauth.create_client(
        CreateOAuthClientParams(
            client_name="Test OAuth Client",
            redirect_uris=["https://example.com/callback"],
        )
    )
    response = client.oauth.list_clients()
    assert len(response.clients) > 0
    assert any(client.client_name == "Test OAuth Client" for client in response.clients)
    assert any(client.client_id is not None for client in response.clients)


def test_get_oauth_client() -> None:
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


# Server is not yet released, so this test is not yet relevant.
# def test_update_oauth_client() -> None:
#     """Test updating an OAuth client."""
#     # First create a client
#     client = service_role_api_client()
#     create_response = client.oauth.create_client(
#         CreateOAuthClientParams(
#             client_name="Test OAuth Client for Update",
#             redirect_uris=["https://example.com/callback"],
#         )
#     )
#     assert create_response.client is not None
#     client_id = create_response.client.client_id
#     response = client.oauth.update_client(
#         client_id,
#         UpdateOAuthClientParams(
#             client_name="Updated Test OAuth Client",
#         )
#     )
#     assert response.client is not None
#     assert response.client.client_name == "Updated Test OAuth Client"


def test_delete_oauth_client() -> None:
    """Test deleting an OAuth client."""
    # First create a client
    client = service_role_api_client()
    create_response = client.oauth.create_client(
        CreateOAuthClientParams(
            client_name="Test OAuth Client for Delete",
            redirect_uris=["https://example.com/callback"],
        )
    )
    assert create_response.client is not None
    client_id = create_response.client.client_id
    client.oauth.delete_client(client_id)


def test_regenerate_oauth_client_secret() -> None:
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
        response = service_role_api_client().oauth.regenerate_client_secret(client_id)
        assert response.client is not None
        assert response.client.client_secret is not None
