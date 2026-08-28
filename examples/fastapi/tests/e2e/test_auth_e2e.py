"""E2E tests for authentication endpoints against a real Supabase instance."""

import random
import string

import httpx
import pytest


def _rand_email() -> str:
    suffix = "".join(random.choices(string.ascii_lowercase, k=8))
    return f"e2e_signup_{suffix}@example.com"


async def test_signup_returns_session(running_app, service_client):
    """POST /auth/signup creates a real user and returns an access token."""
    email = _rand_email()
    async with httpx.AsyncClient(base_url=running_app, timeout=10) as client:
        r = await client.post("/auth/signup", json={"email": email, "password": "Password123!"})

    assert r.status_code == 200
    body = r.json()
    assert body["session"]["access_token"]
    assert body["user"]["email"] == email

    # Cleanup — delete the created user via service role.
    users_resp = await service_client.auth.admin.list_users()
    for u in users_resp:
        if u.email == email:
            await service_client.auth.admin.delete_user(u.id)
            break


async def test_signin_returns_session(running_app, user_a):
    """POST /auth/signin returns a valid session for an existing user."""
    async with httpx.AsyncClient(base_url=running_app, timeout=10) as client:
        r = await client.post(
            "/auth/signin", json={"email": user_a["email"], "password": "Password123!"}
        )

    assert r.status_code == 200
    body = r.json()
    assert body["session"]["access_token"]
    assert body["user"]["email"] == user_a["email"]


async def test_signin_wrong_password_returns_400(running_app):
    """POST /auth/signin with wrong credentials returns 400."""
    async with httpx.AsyncClient(base_url=running_app, timeout=10) as client:
        r = await client.post(
            "/auth/signin",
            json={"email": "nobody@example.com", "password": "WrongPassword!"},
        )

    assert r.status_code == 400


async def test_signout_returns_ok(running_app, user_a):
    """POST /auth/signout always returns {status: ok}."""
    async with httpx.AsyncClient(base_url=running_app, timeout=10) as client:
        r = await client.post("/auth/signout")

    assert r.status_code == 200
    assert r.json()["status"] == "ok"


async def test_tasks_endpoint_requires_auth(running_app):
    """GET /tasks/ without Authorization header returns 401."""
    async with httpx.AsyncClient(base_url=running_app, timeout=10) as client:
        r = await client.get("/tasks/")

    assert r.status_code == 401
