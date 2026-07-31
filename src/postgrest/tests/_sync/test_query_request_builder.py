from typing import Iterable

import pytest
from httpx import Client, Headers, QueryParams
from yarl import URL

from postgrest import SyncQueryRequestBuilder
from postgrest._sync.request_builder import (
    RequestConfig,
    SyncMaybeSingleRequestBuilder,
    SyncSingleRequestBuilder,
)


@pytest.fixture
def query_request_builder() -> Iterable[SyncQueryRequestBuilder]:
    with Client() as client:
        request = RequestConfig(
            client, URL("/example_table"), "GET", Headers(), QueryParams(), None, {}
        )
        yield SyncQueryRequestBuilder(request)


def test_constructor(query_request_builder: SyncQueryRequestBuilder):
    builder = query_request_builder

    assert str(builder.request.path) == "/example_table"
    assert len(builder.request.headers) == 0
    assert len(builder.request.params) == 0
    assert builder.request.http_method == "GET"
    assert builder.request.json is None


def test_select_single(query_request_builder: SyncQueryRequestBuilder):
    # insert()/upsert() return a SyncQueryRequestBuilder, so single() must be
    # reachable after select() to match the JS client's
    # insert(...).select().single() chain. See GH-1553.
    builder = query_request_builder.select("*").single()

    assert isinstance(builder, SyncSingleRequestBuilder)
    assert builder.request.headers["Accept"] == "application/vnd.pgrst.object+json"


def test_select_maybe_single(query_request_builder: SyncQueryRequestBuilder):
    builder = query_request_builder.select("*").maybe_single()

    assert isinstance(builder, SyncMaybeSingleRequestBuilder)
