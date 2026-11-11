# supabase_auth

[![CI](https://github.com/supabase/supabase-py/actions/workflows/ci.yml/badge.svg)](https://github.com/supabase/supabase-py/actions/workflows/ci.yml)
[![Python](https://img.shields.io/pypi/pyversions/supabase_auth)](https://pypi.org/project/supabase_auth)
[![Version](https://img.shields.io/pypi/v/supabase_auth?color=%2334D058)](https://pypi.org/project/supabase_auth)

Python client for [Supabase Auth](https://github.com/supabase/auth), the Python counterpart of [`@supabase/auth-js`](https://github.com/supabase/supabase-js/tree/master/packages/core/auth-js). Most users use it through the [`supabase`](https://github.com/supabase/supabase-py/blob/main/src/supabase/README.md) package, as `client.auth`.

## Installation

The package needs an HTTP client adapter. The examples below use httpx:

### Pip

```bash
pip install supabase_auth "supabase_utils[httpx]"
```

### Uv

```bash
uv add supabase_auth "supabase_utils[httpx]"
```

### Poetry

```bash
poetry add supabase_auth "supabase_utils[httpx]"
```

Use `supabase_utils[aiohttp]` instead to run the async client on aiohttp.

## Features

- Support for both synchronous and asynchronous operations
- MFA (Multi-Factor Authentication) support
- OAuth and SSO integration
- Magic link and OTP authentication
- Phone number authentication
- Anonymous sign-in
- Session management with auto-refresh
- JWT token handling and verification
- User management and profile updates

## Differences to the JavaScript client

Methods and attributes follow the JavaScript client, but browser specific code is not ported.

Errors are raised where they originate instead of being returned next to the data, since that is the idiomatic way in Python. Where JavaScript returns the error:

```js
const { data, error } = await supabase.auth.signUp({ email, password })
```

Python raises a subclass of `AuthError`, which you catch with `try`/`except`.

Names use the Python snake_case convention instead of camelCase, and date-time strings are parsed into `datetime` objects.

## Supabase Service Compatibility

`supabase_auth` only guarantees compatibility with the [latest Supabase Auth release](https://github.com/supabase/auth/releases). Older Supabase Auth releases are supported on a best-effort basis, but compatibility is not guaranteed.

If you self-host Supabase Auth, we recommend upgrading to the latest release when upgrading this SDK.

## Usage

The client takes the URL of the auth service, `https://<project_ref>.supabase.co/auth/v1` for a Supabase project, and the HTTP session it sends its requests with. Leaving the client's context manager closes the session and stops the automatic token refresh.

### Synchronous Client

```python
from httpx import Client
from supabase_auth import (
    SignInWithPassword,
    SignInWithPasswordless,
    SignUpWithPassword,
    SyncSupabaseAuthClient,
    UserAttributes,
)
from supabase_utils.http.adapters.httpx import HttpxSession

with SyncSupabaseAuthClient(
    "https://<project_ref>.supabase.co/auth/v1",
    HttpxSession(Client()),
    headers={"apikey": "your-publishable-key"},
) as client:
    # Sign up with email and password
    response = client.sign_up(
        SignUpWithPassword.email("someone@example.com", "a-strong-password")
    )

    # Sign in with email and password
    response = client.sign_in_with_password(
        SignInWithPassword.email("someone@example.com", "a-strong-password")
    )

    # Sign in with magic link
    client.sign_in_with_otp(SignInWithPasswordless.email("someone@example.com"))

    # Sign in with phone number
    client.sign_in_with_otp(SignInWithPasswordless.phone("+1234567890"))

    # Sign in with OAuth: send the user to the returned URL
    oauth = client.sign_in_with_oauth("google")
    print(oauth.url)

    # Get current user
    user = client.get_user()

    # Update user profile
    user = client.update_user(UserAttributes(data={"name": "John Doe"}))

    # Sign out
    client.sign_out()
```

### Asynchronous Client

```python
import asyncio

from httpx import AsyncClient
from supabase_auth import (
    AsyncSupabaseAuthClient,
    SignInWithPassword,
    SignInWithPasswordless,
    SignUpWithPassword,
    UserAttributes,
)
from supabase_utils.http.adapters.httpx import AsyncHttpxSession


async def main() -> None:
    async with AsyncSupabaseAuthClient(
        "https://<project_ref>.supabase.co/auth/v1",
        AsyncHttpxSession(AsyncClient()),
        headers={"apikey": "your-publishable-key"},
    ) as client:
        # Sign up with email and password
        response = await client.sign_up(
            SignUpWithPassword.email("someone@example.com", "a-strong-password")
        )

        # Sign in with email and password
        response = await client.sign_in_with_password(
            SignInWithPassword.email("someone@example.com", "a-strong-password")
        )

        # Sign in with magic link
        await client.sign_in_with_otp(
            SignInWithPasswordless.email("someone@example.com")
        )

        # Sign in with phone number
        await client.sign_in_with_otp(SignInWithPasswordless.phone("+1234567890"))

        # Sign in with OAuth: send the user to the returned URL
        oauth = await client.sign_in_with_oauth("google")
        print(oauth.url)

        # Get current user
        user = await client.get_user()

        # Update user profile
        user = await client.update_user(UserAttributes(data={"name": "John Doe"}))

        # Sign out
        await client.sign_out()


asyncio.run(main())
```

### MFA Support

The library includes support for Multi-Factor Authentication:

```python
from supabase_auth import MFAEnroll

# List MFA factors
factors = client.mfa.list_factors()

# Enroll a new MFA factor
factor = client.mfa.enroll(MFAEnroll.totp(friendly_name="My phone"))

# Challenge and verify MFA
challenge = client.mfa.challenge(factor.id)
verified = client.mfa.verify(factor.id, "123456", challenge.id)

# Or both in one call
verified = client.mfa.challenge_and_verify(factor.id, "123456")

# Unenroll a factor
client.mfa.unenroll(factor.id)
```
