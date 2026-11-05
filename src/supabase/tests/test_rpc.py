from typing import assert_type

from postgrest.request_builder import RPCCountRequestBuilder, RPCFilterRequestBuilder
from postgrest.types import CountMethod
from supabase_utils.http.io import AsyncHttpIO, SyncHttpIO

from supabase.httpx import create_aclient, create_client

URL = "https://example.supabase.co"
KEY = "publishable-key"


def test_sync_rpc_call_shapes() -> None:
    with create_client(URL, KEY) as client:
        no_params = client.rpc("fn")
        assert_type(no_params, RPCFilterRequestBuilder[SyncHttpIO])
        assert no_params.request.method == "POST"
        assert no_params.request.body == {}

        positional_params = client.rpc("fn", {"a": 1})
        assert_type(positional_params, RPCFilterRequestBuilder[SyncHttpIO])
        assert positional_params.request.method == "POST"
        assert positional_params.request.body == {"a": 1}

        read_only = client.rpc("fn", params={"a": 1}, get=True)
        assert_type(read_only, RPCFilterRequestBuilder[SyncHttpIO])
        assert read_only.request.method == "GET"

        counted = client.rpc("fn", count=CountMethod.exact)
        assert_type(counted, RPCFilterRequestBuilder[SyncHttpIO])
        assert counted.request.headers.get("Prefer") == "count=exact"

        head = client.rpc("fn", head=True, count=CountMethod.exact)
        assert_type(head, RPCCountRequestBuilder[SyncHttpIO])
        assert isinstance(head, RPCCountRequestBuilder)
        assert head.request.method == "HEAD"


async def test_async_rpc_call_shapes() -> None:
    async with create_aclient(URL, KEY) as client:
        no_params = client.rpc("fn")
        assert_type(no_params, RPCFilterRequestBuilder[AsyncHttpIO])
        assert no_params.request.method == "POST"
        assert no_params.request.body == {}

        positional_params = client.rpc("fn", {"a": 1})
        assert_type(positional_params, RPCFilterRequestBuilder[AsyncHttpIO])
        assert positional_params.request.method == "POST"
        assert positional_params.request.body == {"a": 1}

        read_only = client.rpc("fn", params={"a": 1}, get=True)
        assert_type(read_only, RPCFilterRequestBuilder[AsyncHttpIO])
        assert read_only.request.method == "GET"

        counted = client.rpc("fn", count=CountMethod.exact)
        assert_type(counted, RPCFilterRequestBuilder[AsyncHttpIO])
        assert counted.request.headers.get("Prefer") == "count=exact"

        head = client.rpc("fn", head=True, count=CountMethod.exact)
        assert_type(head, RPCCountRequestBuilder[AsyncHttpIO])
        assert isinstance(head, RPCCountRequestBuilder)
        assert head.request.method == "HEAD"
