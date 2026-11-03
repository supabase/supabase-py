from typing import Iterable, Protocol

import pytest

from supabase import AsyncClient as AsyncSupabaseClient
from supabase import AsyncClientOptions
from supabase.aiohttp import create_aclient as create_asyncio_client
from supabase.httpx import create_aclient as create_httpx_client


def pytest_configure(config) -> None:
    from dotenv import load_dotenv

    load_dotenv(dotenv_path="tests/tests.env")


REST_URL = "http://127.0.0.1:3000"


def httpx(
    supabase_key: str, supabase_url: str, options: AsyncClientOptions | None = None
) -> AsyncSupabaseClient:
    return create_httpx_client(supabase_key, supabase_url, options=options)


def aiohttp(
    supabase_key: str, supabase_url: str, options: AsyncClientOptions | None = None
) -> AsyncSupabaseClient:
    return create_asyncio_client(supabase_key, supabase_url, options=options)


class AsyncClientCallable(Protocol):
    def __call__(
        self,
        supabase_key: str,
        supabase_url: str,
        options: AsyncClientOptions | None = None,
    ) -> AsyncSupabaseClient: ...


@pytest.fixture(params=[httpx, aiohttp])
def create_async_client(
    request: pytest.FixtureRequest,
) -> Iterable[AsyncClientCallable]:
    yield request.param  # just immediatly yield the `create_client` function
