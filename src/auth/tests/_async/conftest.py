from collections.abc import AsyncGenerator
from dataclasses import dataclass
from random import random
from time import time
from typing import NotRequired, TypedDict

import pytest
from jwt import encode

from supabase_auth import AsyncSupabaseAuthAdmin, AsyncSupabaseAuthClient
from supabase_auth.types import (
    AdminUserAttributes,
    SignInWithPassword,
    SignUpWithPassword,
    User,
)

from ..conftest import fake
from ..http_sessions import async_http_sessions as http_sessions


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
    user_options = options or {}
    rand_numbers = str(int(time()))
    return Credentials(
        email=user_options.get("email") or fake.unique.email(),
        phone=user_options.get("phone") or f"1{rand_numbers[-11:]}",
        password=user_options.get("password") or fake.password(),
    )


def mock_verification_otp() -> str:
    return str(int(100000 + random() * 900000))


def mock_user_metadata() -> dict[str, str]:
    return {
        "profile_image": fake.url(),
    }


def mock_app_metadata() -> dict[str, list[str]]:
    return {
        "roles": ["editor", "publisher"],
    }


AUTH_URL = "http://127.0.0.1:57321/auth/v1"

GOTRUE_JWT_SECRET = "37c304f8-51aa-419a-a1af-06154e63707a"


@pytest.fixture
async def admin_client_with_user_and_credentials(
    secret_key_api_client: AsyncSupabaseAuthAdmin,
) -> AsyncGenerator[tuple[AsyncSupabaseAuthAdmin, User, Credentials]]:
    credentials = mock_user_credentials()
    response = await secret_key_api_client.create_user(
        AdminUserAttributes(email=credentials.email, password=credentials.password)
    )
    yield (secret_key_api_client, response.user, credentials)
    await secret_key_api_client.delete_user(response.user.id)


@pytest.fixture(params=http_sessions)
async def auth_client(
    request: pytest.FixtureRequest,
) -> AsyncGenerator[AsyncSupabaseAuthClient]:
    async with AsyncSupabaseAuthClient(
        url=AUTH_URL,
        auto_refresh_token=False,
        http_session=request.param(),
    ) as client:
        yield client


@pytest.fixture(params=http_sessions)
async def auth_client_with_session(
    request: pytest.FixtureRequest,
) -> AsyncGenerator[AsyncSupabaseAuthClient]:
    async with AsyncSupabaseAuthClient(
        url=AUTH_URL,
        auto_refresh_token=False,
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


SECRET_KEY_JWT = encode(
    {
        "role": "service_role",
    },
    GOTRUE_JWT_SECRET,
)


@pytest.fixture(params=http_sessions)
async def secret_key_api_client(
    request: pytest.FixtureRequest,
) -> AsyncGenerator[AsyncSupabaseAuthAdmin]:
    async with AsyncSupabaseAuthAdmin(
        url=AUTH_URL,
        default_headers={
            "Authorization": f"Bearer {SECRET_KEY_JWT}",
        },
        http_session=request.param(),
    ) as client:
        yield client
