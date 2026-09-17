from typing import AsyncIterable

import pytest
from httpx import AsyncClient, Headers, QueryParams
from yarl import URL

from postgrest import AsyncQueryRequestBuilder
from postgrest._async.request_builder import (
    AsyncMaybeSingleRequestBuilder,
    AsyncSingleRequestBuilder,
    RequestConfig,
)


@pytest.fixture
async def query_request_builder() -> AsyncIterable[AsyncQueryRequestBuilder]:
    async with AsyncClient() as client:
        request = RequestConfig(
            client, URL("/example_table"), "GET", Headers(), QueryParams(), None, {}
        )
        yield AsyncQueryRequestBuilder(request)


def test_constructor(query_request_builder: AsyncQueryRequestBuilder):
    builder = query_request_builder

    assert str(builder.request.path) == "/example_table"
    assert len(builder.request.headers) == 0
    assert len(builder.request.params) == 0
    assert builder.request.http_method == "GET"
    assert builder.request.json is None


def test_select_single(query_request_builder: AsyncQueryRequestBuilder):
    # insert()/upsert() return an AsyncQueryRequestBuilder, so single() must be
    # reachable after select() to match the JS client's
    # insert(...).select().single() chain. See GH-1553.
    builder = query_request_builder.select("*").single()

    assert isinstance(builder, AsyncSingleRequestBuilder)
    assert builder.request.headers["Accept"] == "application/vnd.pgrst.object+json"


def test_select_maybe_single(query_request_builder: AsyncQueryRequestBuilder):
    builder = query_request_builder.select("*").maybe_single()

    assert isinstance(builder, AsyncMaybeSingleRequestBuilder)
