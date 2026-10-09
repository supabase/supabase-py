"""
E2E test fixtures.

Requires a running local Supabase instance and the following env vars:
  SUPABASE_URL        — from `supabase status -o env` → API_URL
  SUPABASE_SERVICE_KEY — SERVICE_ROLE_KEY
  SUPABASE_ANON_KEY    — ANON_KEY

Start infrastructure: make start-infra (from examples/fastapi/)
"""

import os
import random
import string
import subprocess
import time
from pathlib import Path

import httpx
import pytest
from supabase import acreate_client
from supabase.lib.client_options import AsyncClientOptions

SUPABASE_URL = os.environ.get("SUPABASE_URL", "http://127.0.0.1:54341")
SUPABASE_SERVICE_KEY = os.environ["SUPABASE_SERVICE_KEY"]
SUPABASE_ANON_KEY = os.environ["SUPABASE_ANON_KEY"]

FASTAPI_DIR = Path(__file__).parent.parent.parent
APP_PORT = 8877
APP_BASE_URL = f"http://127.0.0.1:{APP_PORT}"


def _random_suffix(n: int = 8) -> str:
    return "".join(random.choices(string.ascii_lowercase, k=n))


async def _delete_user_and_data(user_id: str) -> None:
    """
    Delete a test user and all their FK-referenced rows.

    GoTrue's admin.delete_user() deletes from auth.users but cannot cascade to
    application tables that REFERENCE auth.users without ON DELETE CASCADE.
    We must delete the application rows first, then the user.
    """
    admin_client = await acreate_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    try:
        # rules cascade to rule_events via ON DELETE CASCADE in the FK.
        await admin_client.table("rules").delete().eq("user_id", user_id).execute()
        # tasks may reference the user in both assigned_to and created_by.
        await admin_client.table("tasks").delete().eq("created_by", user_id).execute()
        await admin_client.table("tasks").delete().eq("assigned_to", user_id).execute()
        await admin_client.auth.admin.delete_user(user_id)
    finally:
        await admin_client.realtime.close()


@pytest.fixture(scope="session", autouse=True)
def _wipe_tables():
    """Delete all rows from test tables at session start for a clean slate."""
    headers = {
        "apikey": SUPABASE_SERVICE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_KEY}",
        "Prefer": "return=minimal",
    }
    for table in ("rule_events", "rules", "tasks"):
        httpx.delete(
            f"{SUPABASE_URL}/rest/v1/{table}",
            headers=headers,
            params={"id": "not.is.null"},
            timeout=10,
        )


@pytest.fixture(scope="session")
def running_app():
    """Start the FastAPI app (including engine) as a uvicorn subprocess."""
    env = {
        **os.environ,
        "SUPABASE_URL": SUPABASE_URL,
        "SUPABASE_SERVICE_KEY": SUPABASE_SERVICE_KEY,
        "SUPABASE_ANON_KEY": SUPABASE_ANON_KEY,
    }
    proc = subprocess.Popen(
        [
            "uv",
            "run",
            "uvicorn",
            "main:app",
            "--host",
            "127.0.0.1",
            "--port",
            str(APP_PORT),
            "--log-level",
            "warning",
        ],
        cwd=FASTAPI_DIR,
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
    )

    deadline = time.time() + 60
    started = False
    while time.time() < deadline:
        # Fail fast if the process exited unexpectedly.
        if proc.poll() is not None:
            break
        try:
            r = httpx.get(f"{APP_BASE_URL}/health", timeout=2)
            if r.status_code == 200:
                started = True
                break
        except Exception:
            pass
        time.sleep(0.4)

    if not started:
        proc.terminate()
        stderr_out = "(unavailable)"
        try:
            proc.wait(timeout=5)
            if proc.stderr:
                stderr_out = proc.stderr.read().decode("utf-8", errors="replace")
        except Exception:
            pass
        pytest.fail(
            f"FastAPI app did not start on port {APP_PORT} "
            f"(exit code: {proc.returncode}).\n"
            f"Ensure SUPABASE_URL / SUPABASE_SERVICE_KEY / SUPABASE_ANON_KEY are set "
            f"and `supabase start` is running in examples/fastapi/.\n"
            f"stderr:\n{stderr_out}"
        )

    yield APP_BASE_URL

    proc.terminate()
    try:
        proc.wait(timeout=10)
    except subprocess.TimeoutExpired:
        proc.kill()


@pytest.fixture
async def service_client():
    """Service-role AsyncClient — bypasses RLS. Created fresh per test."""
    client = await acreate_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    yield client
    await client.realtime.close()


@pytest.fixture
async def user_a():
    """Create a real Supabase user and return credentials. Cleaned up after the test."""
    email = f"e2e_a_{_random_suffix()}@example.com"
    password = "Password123!"

    # Use a dedicated anon client for sign_up to avoid corrupting a shared
    # service-role client's internal auth state.
    signup_client = await acreate_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    resp = await signup_client.auth.sign_up({"email": email, "password": password})
    await signup_client.realtime.close()
    assert resp.session, f"sign_up returned no session for {email}"
    token = resp.session.access_token
    user_id = resp.user.id

    options = AsyncClientOptions()
    options.headers["Authorization"] = f"Bearer {token}"
    anon_client = await acreate_client(SUPABASE_URL, SUPABASE_ANON_KEY, options=options)

    yield {"token": token, "user_id": user_id, "email": email, "client": anon_client}

    await anon_client.realtime.close()
    await _delete_user_and_data(user_id)


@pytest.fixture
async def user_b():
    """A second user for RLS isolation tests. Cleaned up after the test."""
    email = f"e2e_b_{_random_suffix()}@example.com"
    password = "Password123!"

    signup_client = await acreate_client(SUPABASE_URL, SUPABASE_ANON_KEY)
    resp = await signup_client.auth.sign_up({"email": email, "password": password})
    await signup_client.realtime.close()
    assert resp.session, f"sign_up returned no session for {email}"
    token = resp.session.access_token
    user_id = resp.user.id

    options = AsyncClientOptions()
    options.headers["Authorization"] = f"Bearer {token}"
    anon_client = await acreate_client(SUPABASE_URL, SUPABASE_ANON_KEY, options=options)

    yield {"token": token, "user_id": user_id, "email": email, "client": anon_client}

    await anon_client.realtime.close()
    await _delete_user_and_data(user_id)


@pytest.fixture
async def client_a(running_app, user_a):
    """httpx.AsyncClient pre-configured with user A's auth token."""
    async with httpx.AsyncClient(
        base_url=running_app,
        headers={"Authorization": f"Bearer {user_a['token']}"},
        timeout=10,
    ) as client:
        yield client


@pytest.fixture
async def client_b(running_app, user_b):
    """httpx.AsyncClient pre-configured with user B's auth token."""
    async with httpx.AsyncClient(
        base_url=running_app,
        headers={"Authorization": f"Bearer {user_b['token']}"},
        timeout=10,
    ) as client:
        yield client
