from __future__ import annotations

import os
from collections.abc import Generator

import pytest
from dotenv import load_dotenv
from httpx import Client
from supabase_utils.http.adapters.httpx import HttpxSession

from storage3 import SyncStorageClient


def pytest_configure(config: pytest.Config) -> None:
    load_dotenv(dotenv_path="tests/tests.env")


def httpx() -> HttpxSession:
    return HttpxSession(client=Client(http2=True, verify=True))


@pytest.fixture(params=[httpx])
def storage(request: pytest.FixtureRequest) -> Generator[SyncStorageClient]:
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
        http_session=request.param(),
    ) as client:
        yield client
