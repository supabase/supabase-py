from typing import AsyncIterable

import pytest
from httpx import AsyncClient, Headers, QueryParams
from supabase_utils.http import AsyncHttpIO, JSONRequest
from yarl import URL

from postgrest.request_builder import QueryRequestBuilder


@pytest.fixture
async def query_request_builder() -> AsyncIterable[QueryRequestBuilder[AsyncHttpIO]]:
    async with AsyncClient() as client:
        request = JSONRequest(
            method="GET",
            path=["example_table"],
            headers=Headers(),
            query_params=QueryParams(),
            body={},
        )
        yield QueryRequestBuilder(
            executor=AsyncHttpIO(session=client),
            base_url=URL("/"),
            default_headers=Headers(),
            request=request,
        )
