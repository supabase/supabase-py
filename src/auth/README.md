# Auth-py

[![CI](https://github.com/supabase-community/gotrue-py/actions/workflows/ci.yml/badge.svg)](https://github.com/supabase-community/gotrue-py/actions/workflows/ci.yml)
[![Python](https://img.shields.io/pypi/pyversions/gotrue)](https://pypi.org/project/gotrue)
[![Version](https://img.shields.io/pypi/v/gotrue?color=%2334D058)](https://pypi.org/project/gotrue)

This is a Python port of the [supabase js gotrue client](https://github.com/supabase/gotrue-js). The current state is that there is a features parity but with small differences that are mentioned in the section **Differences to the JS client**. As of December 14th, we renamed to repo from `gotrue-py` to `auth-py` to mirror the changes in the JavaScript library.

## Installation

The package can be installed using pip, uv or poetry:

### Pip

```bash
pip install supabase_auth
```


### Uv

```bash
uv add supabase_auth
```

### Poetry

```bash
poetry add supabase_auth
```

## Features

- Full feature parity with the JavaScript client
- Support for both synchronous and asynchronous operations
- MFA (Multi-Factor Authentication) support
- OAuth and SSO integration
- Magic link and OTP authentication
- Phone number authentication
- Anonymous sign-in
- Session management with auto-refresh
- JWT token handling and verification
- User management and profile updates

## Differences to the JS client

It should be noted there are differences to the [JS client](https://github.com/supabase/gotrue-js). If you feel particulaly strongly about them and want to motivate a change, feel free to make a GitHub issue and we can discuss it there.

Firstly, feature pairity is not 100% with the [JS client](https://github.com/supabase/gotrue-js). In most cases we match the methods and attributes of the [JS client](https://github.com/supabase/gotrue-js) and api classes, but is some places (e.g for browser specific code) it didn't make sense to port the code line for line.

There is also a divergence in terms of how errors are raised. In the [JS client](https://github.com/supabase/gotrue-js), the errors are returned as part of the object, which the user can choose to process in whatever way they see fit. In this Python client, we raise the errors directly where they originate, as it was felt this was more Pythonic and adhered to the idioms of the language more directly.

In JS we return the error, but in Python we just raise it.

```js
const { data, error } = client.sign_up(...)
```

The other key difference is we do not use pascalCase to encode variable and method names. Instead we use the snake_case convention adopted in the Python language.

Also, the `supabase_auth` library for Python parses the date-time string into `datetime` Python objects. The [JS client](https://github.com/supabase/gotrue-js) keeps the date-time as strings.

## Usage

The library provides both synchronous and asynchronous clients. Here are some examples:

### Synchronous Client

```python
from supabase_auth import SyncGoTrueClient

headers = {
    "apiKey": "my-mega-awesome-api-key",
    # ... any other headers you might need.
}
client: SyncGoTrueClient = SyncGoTrueClient(url="www.genericauthwebsite.com", headers=headers)

# Sign up with email and password
user = client.sign_up(email="example@gmail.com", password="*********")

# Sign in with email and password
user = client.sign_in_with_password(email="example@gmail.com", password="*********")

# Sign in with magic link
user = client.sign_in_with_otp(email="example@gmail.com")

# Sign in with phone number
user = client.sign_in_with_otp(phone="+1234567890")

# Sign in with OAuth
user = client.sign_in_with_oauth(provider="google")

# Sign out
client.sign_out()

# Get current user
user = client.get_user()

# Update user profile
user = client.update_user({"data": {"name": "John Doe"}})
```

### Asynchronous Client

```python
from supabase_auth import AsyncGoTrueClient

headers = {
    "apiKey": "my-mega-awesome-api-key",
    # ... any other headers you might need.
}
client: AsyncGoTrueClient = AsyncGoTrueClient(url="www.genericauthwebsite.com", headers=headers)

async def main():
    # Sign up with email and password
    user = await client.sign_up(email="example@gmail.com", password="*********")

    # Sign in with email and password
    user = await client.sign_in_with_password(email="example@gmail.com", password="*********")

    # Sign in with magic link
    user = await client.sign_in_with_otp(email="example@gmail.com")

    # Sign in with phone number
    user = await client.sign_in_with_otp(phone="+1234567890")

    # Sign in with OAuth
    user = await client.sign_in_with_oauth(provider="google")

    # Sign out
    await client.sign_out()

    # Get current user
    user = await client.get_user()

    # Update user profile
    user = await client.update_user({"data": {"name": "John Doe"}})

# Run the async code
import asyncio
asyncio.run(main())
```

### MFA Support

The library includes support for Multi-Factor Authentication:

```python
# List MFA factors
factors = client.mfa.list_factors()

# Enroll a new MFA factor
enrolled_factor = client.mfa.enroll({"factor_type": "totp"})

# Challenge and verify MFA
challenge = client.mfa.challenge({"factor_id": "factor_id"})
verified = client.mfa.verify({"factor_id": "factor_id", "code": "123456"})

# Unenroll a factor
client.mfa.unenroll({"factor_id": "factor_id"})
```

## Contributions

We would be immensely grateful for any contributions to this project.
