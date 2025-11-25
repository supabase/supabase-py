from __future__ import annotations

import os
from collections.abc import AsyncGenerator
from pathlib import Path

import pytest
from dotenv import load_dotenv
from storage3 import AsyncStorageClient


def pytest_configure(config) -> None:
    # Get the path to tests.env relative to this conftest file
    # Try tests.env.local first (git-ignored), then fall back to tests.env
    tests_dir = Path(__file__).parent.parent
    tests_env_local = tests_dir / "tests.env.local"
    tests_env = tests_dir / "tests.env"
    
    if tests_env_local.exists():
        load_dotenv(dotenv_path=str(tests_env_local))
    elif tests_env.exists():
        load_dotenv(dotenv_path=str(tests_env))


@pytest.fixture
async def storage() -> AsyncGenerator[AsyncStorageClient]:
    url = os.environ.get("SUPABASE_TEST_URL")
    assert url is not None, "Must provide SUPABASE_TEST_URL environment variable"
    key = os.environ.get("SUPABASE_TEST_KEY")
    assert key is not None, "Must provide SUPABASE_TEST_KEY environment variable"
    async with AsyncStorageClient(
        url,
        {
            "apiKey": key,
            "Authorization": f"Bearer {key}",
        },
    ) as client:
        client.session.timeout = None
        yield client
