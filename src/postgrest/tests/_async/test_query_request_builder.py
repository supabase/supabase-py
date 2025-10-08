from typing import AsyncIterable

import pytest
from httpx import AsyncClient, Headers, QueryParams
from yarl import URL

from postgrest import AsyncQueryRequestBuilder
from postgrest._async.request_builder import RequestConfig


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
