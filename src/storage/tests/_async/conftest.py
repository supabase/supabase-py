from __future__ import annotations

import os
from collections.abc import AsyncGenerator

import pytest
from aiohttp import ClientSession
from dotenv import load_dotenv
from httpx import AsyncClient
from supabase_utils.http.adapters.aiohttp import AsyncAiohttpSession
from supabase_utils.http.adapters.httpx import AsyncHttpxSession

from storage3 import AsyncStorageClient


def pytest_configure(config: pytest.Config) -> None:
    load_dotenv(dotenv_path="tests/tests.env")


def httpx() -> AsyncHttpxSession:
    return AsyncHttpxSession(client=AsyncClient(http2=True, verify=True))


def aiohttp() -> AsyncAiohttpSession:
    return AsyncAiohttpSession(client=ClientSession())


@pytest.fixture(params=[httpx, aiohttp])
async def storage(request: pytest.FixtureRequest) -> AsyncGenerator[AsyncStorageClient]:
    url = os.environ.get("SUPABASE_TEST_URL")
    assert url is not None, "Must provide SUPABASE_TEST_URL environment variable"
    key = os.environ.get("SUPABASE_TEST_KEY")
    assert key is not None, "Must provide SUPABASE_TEST_KEY environment variable"
    async with AsyncStorageClient(
        url,
        headers={
            "apiKey": key,
            "Authorization": f"Bearer {key}",
        },
        http_session=request.param(),
    ) as client:
        yield client
