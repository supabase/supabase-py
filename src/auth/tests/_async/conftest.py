from dataclasses import dataclass
from random import random
from time import time
from typing import AsyncGenerator

import pytest
from aiohttp import ClientSession
from faker import Faker
from httpx import AsyncClient
from jwt import encode
from supabase_utils.http.adapters.aiohttp import AsyncAiohttpSession
from supabase_utils.http.adapters.httpx import AsyncHttpxSession
from typing_extensions import NotRequired, TypedDict

from supabase_auth import AsyncSupabaseAuthAdmin, AsyncSupabaseAuthClient
from supabase_auth.types import (
    AdminUserAttributes,
    SignInWithPassword,
    SignUpWithPassword,
    User,
)


def mock_access_token() -> str:
    return encode(
        {
            "sub": "1234567890",
            "role": "anon_key",
        },
        GOTRUE_JWT_SECRET,
    )


class OptionalCredentials(TypedDict):
    email: NotRequired[str | None]
    phone: NotRequired[str | None]
    password: NotRequired[str | None]


@dataclass
class Credentials:
    email: str
    phone: str
    password: str


def mock_user_credentials(
    options: OptionalCredentials | None = None,
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


def mock_user_metadata() -> dict[str, str]:
    fake = Faker()
    return {
        "profile_image": fake.url(),
    }


def mock_app_metadata() -> dict[str, list[str]]:
    return {
        "roles": ["editor", "publisher"],
    }


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


def httpx() -> AsyncHttpxSession:
    return AsyncHttpxSession(client=AsyncClient(http2=True, verify=True))


def aiohttp() -> AsyncAiohttpSession:
    return AsyncAiohttpSession(client=ClientSession())


http_sessions = [httpx, aiohttp]


@pytest.fixture
async def admin_client_with_user_and_credentials(
    service_role_api_client: AsyncSupabaseAuthAdmin,
) -> AsyncGenerator[tuple[AsyncSupabaseAuthAdmin, User, Credentials]]:
    credentials = mock_user_credentials()
    response = await service_role_api_client.create_user(
        AdminUserAttributes(email=credentials.email, password=credentials.password)
    )
    yield (service_role_api_client, response.user, credentials)
    await service_role_api_client.delete_user(response.user.id)


@pytest.fixture(params=http_sessions)
async def auth_client(
    request: pytest.FixtureRequest,
) -> AsyncGenerator[AsyncSupabaseAuthClient]:
    async with AsyncSupabaseAuthClient(
        url=GOTRUE_URL_SIGNUP_ENABLED_AUTO_CONFIRM_ON,
        auto_refresh_token=False,
        persist_session=True,
        http_session=request.param(),
    ) as client:
        yield client


@pytest.fixture(params=http_sessions)
async def auth_client_with_session(
    request: pytest.FixtureRequest,
) -> AsyncGenerator[AsyncSupabaseAuthClient]:
    async with AsyncSupabaseAuthClient(
        url=GOTRUE_URL_SIGNUP_ENABLED_AUTO_CONFIRM_ON,
        auto_refresh_token=False,
        persist_session=False,
        http_session=request.param(),
    ) as client:
        credentials = mock_user_credentials()
        await client.sign_up(
            SignUpWithPassword.email(
                email=credentials.email, password=credentials.password
            )
        )
        await client.sign_in_with_password(
            SignInWithPassword.email(
                email=credentials.email, password=credentials.password
            )
        )
        yield client
        await client.sign_out()


@pytest.fixture(params=http_sessions)
async def auth_client_with_asymmetric_session(
    request: pytest.FixtureRequest,
) -> AsyncGenerator[AsyncSupabaseAuthClient]:
    async with AsyncSupabaseAuthClient(
        url=GOTRUE_URL_SIGNUP_ENABLED_ASYMMETRIC_AUTO_CONFIRM_ON,
        auto_refresh_token=False,
        persist_session=False,
        http_session=request.param(),
    ) as client:
        yield client


@pytest.fixture(params=http_sessions)
async def auth_subscription_client(
    request: pytest.FixtureRequest,
) -> AsyncGenerator[AsyncSupabaseAuthClient]:
    async with AsyncSupabaseAuthClient(
        url=GOTRUE_URL_SIGNUP_ENABLED_AUTO_CONFIRM_ON,
        auto_refresh_token=False,
        persist_session=True,
        http_session=request.param(),
    ) as client:
        yield client


@pytest.fixture(params=http_sessions)
async def client_api_auto_confirm_enabled_client(
    request: pytest.FixtureRequest,
) -> AsyncGenerator[AsyncSupabaseAuthClient]:
    async with AsyncSupabaseAuthClient(
        url=GOTRUE_URL_SIGNUP_ENABLED_AUTO_CONFIRM_ON,
        auto_refresh_token=False,
        persist_session=True,
        http_session=request.param(),
    ) as client:
        yield client


@pytest.fixture(params=http_sessions)
async def client_api_auto_confirm_off_signups_enabled_client(
    request: pytest.FixtureRequest,
) -> AsyncGenerator[AsyncSupabaseAuthClient]:
    async with AsyncSupabaseAuthClient(
        url=GOTRUE_URL_SIGNUP_ENABLED_AUTO_CONFIRM_OFF,
        auto_refresh_token=False,
        persist_session=True,
        http_session=request.param(),
    ) as client:
        yield client


@pytest.fixture(params=http_sessions)
async def client_api_auto_confirm_disabled_client(
    request: pytest.FixtureRequest,
) -> AsyncGenerator[AsyncSupabaseAuthClient]:
    async with AsyncSupabaseAuthClient(
        url=GOTRUE_URL_SIGNUP_DISABLED_AUTO_CONFIRM_OFF,
        auto_refresh_token=False,
        persist_session=True,
        http_session=request.param(),
    ) as client:
        yield client


@pytest.fixture(params=http_sessions)
async def auth_admin_api_auto_confirm_enabled_client(
    request: pytest.FixtureRequest,
) -> AsyncGenerator[AsyncSupabaseAuthAdmin]:
    async with AsyncSupabaseAuthAdmin(
        url=GOTRUE_URL_SIGNUP_ENABLED_AUTO_CONFIRM_ON,
        default_headers={
            "Authorization": f"Bearer {AUTH_ADMIN_JWT}",
        },
        http_session=request.param(),
    ) as client:
        yield client


@pytest.fixture(params=http_sessions)
async def auth_admin_api_auto_confirm_disabled_client(
    request: pytest.FixtureRequest,
) -> AsyncGenerator[AsyncSupabaseAuthAdmin]:
    async with AsyncSupabaseAuthAdmin(
        url=GOTRUE_URL_SIGNUP_ENABLED_AUTO_CONFIRM_OFF,
        default_headers={
            "Authorization": f"Bearer {AUTH_ADMIN_JWT}",
        },
        http_session=request.param(),
    ) as client:
        yield client


SERVICE_ROLE_JWT = encode(
    {
        "role": "service_role",
    },
    GOTRUE_JWT_SECRET,
)


@pytest.fixture(params=http_sessions)
async def service_role_api_client(
    request: pytest.FixtureRequest,
) -> AsyncGenerator[AsyncSupabaseAuthAdmin]:
    async with AsyncSupabaseAuthAdmin(
        url=GOTRUE_URL_SIGNUP_ENABLED_AUTO_CONFIRM_ON,
        default_headers={
            "Authorization": f"Bearer {SERVICE_ROLE_JWT}",
        },
        http_session=request.param(),
    ) as client:
        yield client


@pytest.fixture(params=http_sessions)
async def service_role_api_client_with_sms(
    request: pytest.FixtureRequest,
) -> AsyncGenerator[AsyncSupabaseAuthAdmin]:
    async with AsyncSupabaseAuthAdmin(
        url=GOTRUE_URL_SIGNUP_ENABLED_AUTO_CONFIRM_OFF,
        default_headers={
            "Authorization": f"Bearer {SERVICE_ROLE_JWT}",
        },
        http_session=request.param(),
    ) as client:
        yield client


@pytest.fixture(params=http_sessions)
async def service_role_api_client_no_sms(
    request: pytest.FixtureRequest,
) -> AsyncGenerator[AsyncSupabaseAuthAdmin]:
    async with AsyncSupabaseAuthAdmin(
        url=GOTRUE_URL_SIGNUP_DISABLED_AUTO_CONFIRM_OFF,
        default_headers={
            "Authorization": f"Bearer {SERVICE_ROLE_JWT}",
        },
        http_session=request.param(),
    ) as client:
        yield client
