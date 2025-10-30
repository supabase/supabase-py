from time import time

from .clients import (
    create_new_user_with_email,
    mock_app_metadata,
    mock_user_credentials,
    mock_user_metadata,
)


def test_create_new_user_with_email():
    email = f"user+{int(time())}@example.com"
    user = create_new_user_with_email(email=email)
    assert user.email == email


def test_mock_user_metadata():
    user_metadata = mock_user_metadata()
    assert user_metadata
    assert user_metadata.get("profile_image")


def test_mock_app_metadata():
    app_metadata = mock_app_metadata()
    assert app_metadata
    assert app_metadata.get("roles")
