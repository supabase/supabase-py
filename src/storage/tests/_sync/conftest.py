from __future__ import annotations

import asyncio
import os
from collections.abc import Generator

import pytest
from dotenv import load_dotenv

from storage3 import SyncStorageClient


def pytest_configure(config) -> None:
    load_dotenv(dotenv_path="tests/tests.env")


@pytest.fixture(scope="package")
def event_loop() -> Generator[asyncio.AbstractEventLoop]:
    """Returns an event loop for the current thread"""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="package")
def storage() -> Generator[SyncStorageClient]:
    url = os.environ.get("SUPABASE_TEST_URL")
    assert url is not None, "Must provide SUPABASE_TEST_URL environment variable"
    key = os.environ.get("SUPABASE_TEST_KEY")
    assert key is not None, "Must provide SUPABASE_TEST_KEY environment variable"
    with SyncStorageClient(
        url,
        {
            "apiKey": key,
            "Authorization": f"Bearer {key}",
        },
    ) as client:
        client.session.timeout = None
        yield client
