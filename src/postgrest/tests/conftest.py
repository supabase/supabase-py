from collections.abc import Iterable

import pytest
from httpx import Client
from supabase_utils.http.adapters.httpx import HttpxSession
from supabase_utils.http.headers import Headers
from supabase_utils.http.io import SyncHttpIO
from supabase_utils.http.query import URLQuery
from yarl import URL

from postgrest.request_builder import (
    BaseFilterRequestBuilder,
    PostgrestRequest,
    RequestBuilder,
    SelectRequestBuilder,
)


@pytest.fixture
def builder() -> BaseFilterRequestBuilder:
    """A string builder with no filters, to compare the typed rendering
    against."""
    request = PostgrestRequest(
        path=["todos"],
        method="GET",
        headers=Headers.empty(),
        query=URLQuery.empty(),
        body={},
    )
    return BaseFilterRequestBuilder(request=request)


@pytest.fixture
def select_builder() -> Iterable[SelectRequestBuilder[SyncHttpIO]]:
    """A string select builder, for the methods a filter builder lacks."""
    with Client() as client:
        yield RequestBuilder(
            executor=SyncHttpIO(session=HttpxSession(client=client)),
            base_url=URL("/todos"),
            default_headers=Headers.empty(),
        ).select("*")
