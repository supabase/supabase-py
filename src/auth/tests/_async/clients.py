from dataclasses import dataclass
from random import random
from time import time
from typing import Optional

from faker import Faker
from jwt import encode
from supabase_auth import AsyncGoTrueAdminAPI, AsyncGoTrueClient
from supabase_auth.types import User
from typing_extensions import NotRequired, TypedDict


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


@dataclass
class Credentials:
    email: str
    phone: str
    password: str


def mock_user_credentials(
    options: Optional[OptionalCredentials] = None,
) -> Credentials:
    fake = Faker()
    user_options = options or {}
    rand_numbers = str(int(time()))
    return Credentials(
        email=user_options.get("email") or fake.email(),
        phone=user_options.get("phone") or f"1{rand_numbers[-11:]}",
        password=user_options.get("password") or fake.password(),
    )


def mock_verification_otp() -> str:
    return str(int(100000 + random() * 900000))


class UserMetadata(TypedDict):
    profile_image: str


def mock_user_metadata() -> UserMetadata:
    fake = Faker()
    return {
        "profile_image": fake.url(),
    }


class AppMetadata(TypedDict):
    roles: list[str]


def mock_app_metadata() -> AppMetadata:
    return {
        "roles": ["editor", "publisher"],
    }


async def create_new_user_with_email(
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
    response = await service_role_api_client().create_user(
        {
            "email": credentials.email,
            "password": credentials.password,
        }
    )
    return response.user


SIGNUP_ENABLED_AUTO_CONFIRM_OFF_PORT = 9999
SIGNUP_ENABLED_AUTO_CONFIRM_ON_PORT = 9998
SIGNUP_DISABLED_AUTO_CONFIRM_OFF_PORT = 9997
SIGNUP_ENABLED_ASYMMETRIC_AUTO_CONFIRM_ON_PORT = 9996

GOTRUE_URL_SIGNUP_ENABLED_AUTO_CONFIRM_OFF = (
    f"http://localhost:{SIGNUP_ENABLED_AUTO_CONFIRM_OFF_PORT}"
)
GOTRUE_URL_SIGNUP_ENABLED_AUTO_CONFIRM_ON = (
    f"http://localhost:{SIGNUP_ENABLED_AUTO_CONFIRM_ON_PORT}"
)
GOTRUE_URL_SIGNUP_ENABLED_ASYMMETRIC_AUTO_CONFIRM_ON = (
    f"http://localhost:{SIGNUP_ENABLED_ASYMMETRIC_AUTO_CONFIRM_ON_PORT}"
)
GOTRUE_URL_SIGNUP_DISABLED_AUTO_CONFIRM_OFF = (
    f"http://localhost:{SIGNUP_DISABLED_AUTO_CONFIRM_OFF_PORT}"
)

GOTRUE_JWT_SECRET = "37c304f8-51aa-419a-a1af-06154e63707a"

AUTH_ADMIN_JWT = encode(
    {
        "sub": "1234567890",
        "role": "supabase_admin",
    },
    GOTRUE_JWT_SECRET,
)


def auth_client() -> AsyncGoTrueClient:
    return AsyncGoTrueClient(
        url=GOTRUE_URL_SIGNUP_ENABLED_AUTO_CONFIRM_ON,
        auto_refresh_token=False,
        persist_session=True,
    )


async def auth_client_with_session() -> AsyncGoTrueClient:
    client = AsyncGoTrueClient(
        url=GOTRUE_URL_SIGNUP_ENABLED_AUTO_CONFIRM_ON,
        auto_refresh_token=False,
        persist_session=False,
    )
    credentials = mock_user_credentials()
    await client.sign_up({"email": credentials.email, "password": credentials.password})
    return client


def auth_client_with_asymmetric_session() -> AsyncGoTrueClient:
    return AsyncGoTrueClient(
        url=GOTRUE_URL_SIGNUP_ENABLED_ASYMMETRIC_AUTO_CONFIRM_ON,
        auto_refresh_token=False,
        persist_session=False,
    )


def auth_subscription_client() -> AsyncGoTrueClient:
    return AsyncGoTrueClient(
        url=GOTRUE_URL_SIGNUP_ENABLED_AUTO_CONFIRM_ON,
        auto_refresh_token=False,
        persist_session=True,
    )


def client_api_auto_confirm_enabled_client() -> AsyncGoTrueClient:
    return AsyncGoTrueClient(
        url=GOTRUE_URL_SIGNUP_ENABLED_AUTO_CONFIRM_ON,
        auto_refresh_token=False,
        persist_session=True,
    )


def client_api_auto_confirm_off_signups_enabled_client() -> AsyncGoTrueClient:
    return AsyncGoTrueClient(
        url=GOTRUE_URL_SIGNUP_ENABLED_AUTO_CONFIRM_OFF,
        auto_refresh_token=False,
        persist_session=True,
    )


def client_api_auto_confirm_disabled_client() -> AsyncGoTrueClient:
    return AsyncGoTrueClient(
        url=GOTRUE_URL_SIGNUP_DISABLED_AUTO_CONFIRM_OFF,
        auto_refresh_token=False,
        persist_session=True,
    )


def auth_admin_api_auto_confirm_enabled_client() -> AsyncGoTrueAdminAPI:
    return AsyncGoTrueAdminAPI(
        url=GOTRUE_URL_SIGNUP_ENABLED_AUTO_CONFIRM_ON,
        headers={
            "Authorization": f"Bearer {AUTH_ADMIN_JWT}",
        },
    )


def auth_admin_api_auto_confirm_disabled_client() -> AsyncGoTrueAdminAPI:
    return AsyncGoTrueAdminAPI(
        url=GOTRUE_URL_SIGNUP_ENABLED_AUTO_CONFIRM_OFF,
        headers={
            "Authorization": f"Bearer {AUTH_ADMIN_JWT}",
        },
    )


SERVICE_ROLE_JWT = encode(
    {
        "role": "service_role",
    },
    GOTRUE_JWT_SECRET,
)


def service_role_api_client() -> AsyncGoTrueAdminAPI:
    return AsyncGoTrueAdminAPI(
        url=GOTRUE_URL_SIGNUP_ENABLED_AUTO_CONFIRM_ON,
        headers={
            "Authorization": f"Bearer {SERVICE_ROLE_JWT}",
        },
    )


def service_role_api_client_with_sms() -> AsyncGoTrueAdminAPI:
    return AsyncGoTrueAdminAPI(
        url=GOTRUE_URL_SIGNUP_ENABLED_AUTO_CONFIRM_OFF,
        headers={
            "Authorization": f"Bearer {SERVICE_ROLE_JWT}",
        },
    )


def service_role_api_client_no_sms() -> AsyncGoTrueAdminAPI:
    return AsyncGoTrueAdminAPI(
        url=GOTRUE_URL_SIGNUP_DISABLED_AUTO_CONFIRM_OFF,
        headers={
            "Authorization": f"Bearer {SERVICE_ROLE_JWT}",
        },
    )
