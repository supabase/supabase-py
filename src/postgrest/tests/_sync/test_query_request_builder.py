from typing import Iterable

import pytest
from httpx import Client, Headers, QueryParams
from supabase_utils.http import JSONRequest, SyncHttpIO
from yarl import URL

from postgrest.request_builder import QueryRequestBuilder


@pytest.fixture
def query_request_builder() -> Iterable[QueryRequestBuilder[SyncHttpIO]]:
    with Client() as client:
        request = JSONRequest(
            method="GET",
            path=["example_table"],
            headers=Headers(),
            query_params=QueryParams(),
            body={},
        )
        yield QueryRequestBuilder(
            executor=SyncHttpIO(session=client),
            base_url=URL("/"),
            default_headers=Headers(),
            request=request,
        )
