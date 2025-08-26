from random import random
from time import time
from typing import Optional

from faker import Faker
from jwt import encode
from typing_extensions import NotRequired, TypedDict

from supabase_auth.types import User

from .clients import GOTRUE_JWT_SECRET, service_role_api_client


def mock_access_token() -> str:
    return encode(
        {
            "sub": "1234567890",
            "role": "anon_key",
        },
        GOTRUE_JWT_SECRET,
    )


class OptionalCredentials(TypedDict):
    email: NotRequired[Optional[str]]
    phone: NotRequired[Optional[str]]
    password: NotRequired[Optional[str]]


class Credentials(TypedDict):
    email: str
    phone: str
    password: str


def mock_user_credentials(
    options: OptionalCredentials = {},
) -> Credentials:
    fake = Faker()
    rand_numbers = str(int(time()))
    return {
        "email": options.get("email") or fake.email(),
        "phone": options.get("phone") or f"1{rand_numbers[-11:]}",
        "password": options.get("password") or fake.password(),
    }


def mock_verification_otp() -> str:
    return str(int(100000 + random() * 900000))


def mock_user_metadata():
    fake = Faker()
    return {
        "profile_image": fake.url(),
    }


def mock_app_metadata():
    return {
        "roles": ["editor", "publisher"],
    }


def create_new_user_with_email(
    *,
    email: Optional[str] = None,
    password: Optional[str] = None,
) -> User:
    credentials = mock_user_credentials(
        {
            "email": email,
            "password": password,
        }
    )
    response = service_role_api_client().create_user(
        {
            "email": credentials["email"],
            "password": credentials["password"],
        }
    )
    return response.user
