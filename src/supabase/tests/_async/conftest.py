from typing import Any, Protocol

import pytest

from supabase import AsyncClient as AsyncSupabaseClient
from supabase.aiohttp import create_async_client as create_aiohttp_client
from supabase.httpx import create_async_client as create_httpx_client


def pytest_configure(config: pytest.Config) -> None:
    from dotenv import load_dotenv

    load_dotenv(dotenv_path="tests/tests.env")


REST_URL = "http://127.0.0.1:3000"


def httpx(supabase_url: str, supabase_key: str, **kwargs: Any) -> AsyncSupabaseClient:
    return create_httpx_client(supabase_url, supabase_key, **kwargs)


def aiohttp(supabase_url: str, supabase_key: str, **kwargs: Any) -> AsyncSupabaseClient:
    return create_aiohttp_client(supabase_url, supabase_key, **kwargs)


class AsyncClientCallable(Protocol):
    def __call__(
        self, supabase_url: str, supabase_key: str, **kwargs: Any
    ) -> AsyncSupabaseClient: ...


@pytest.fixture(params=[httpx, aiohttp])
def create_async_client(
    request: pytest.FixtureRequest,
) -> AsyncClientCallable:
    client_factory: AsyncClientCallable = request.param
    return client_factory
