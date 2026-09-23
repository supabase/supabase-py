from time import time

from .clients import (
    create_new_user_with_email,
    mock_app_metadata,
    mock_user_metadata,
)


def test_create_new_user_with_email() -> None:
    email = f"user+{int(time())}@example.com"
    user = create_new_user_with_email(email=email)
    assert user.email == email


def test_mock_user_metadata() -> None:
    user_metadata = mock_user_metadata()
    assert user_metadata
    assert user_metadata.get("profile_image")


def test_mock_app_metadata() -> None:
    app_metadata = mock_app_metadata()
    assert app_metadata
    assert app_metadata.get("roles")
