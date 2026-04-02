from typing import AsyncIterable

import pytest
from aiohttp import ClientSession
from httpx import AsyncClient, AsyncHTTPTransport, Limits
from supabase_utils.http.adapters.aiohttp import AsyncAiohttpSession
from supabase_utils.http.adapters.httpx import AsyncHttpxSession

from postgrest import AsyncPostgrestClient

REST_URL = "http://127.0.0.1:3000"


def httpx_client() -> AsyncClient:
    transport = AsyncHTTPTransport(
        retries=4,
        limits=Limits(
            max_connections=1,
            max_keepalive_connections=1,
            keepalive_expiry=None,
        ),
    )
    headers = {"x-user-agent": "my-app/0.0.1"}
    http_client = AsyncClient(
        transport=transport, headers=headers, http2=True, verify=True
    )
    return http_client


def httpx() -> AsyncHttpxSession:
    return AsyncHttpxSession(client=httpx_client())


def aiohttp() -> AsyncAiohttpSession:
    return AsyncAiohttpSession(client=ClientSession())


@pytest.fixture(params=[httpx, aiohttp])
async def postgrest_client(
    request: pytest.FixtureRequest,
) -> AsyncIterable[AsyncPostgrestClient]:
    async with AsyncPostgrestClient(
        base_url=REST_URL,
        http_session=request.param(),
    ) as client:
        yield client
