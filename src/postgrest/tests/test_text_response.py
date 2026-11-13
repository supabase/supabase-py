from typing import assert_type

import pytest
from httpx import AsyncClient, Client, MockTransport, Request, Response
from supabase_utils.http.adapters.httpx import AsyncHttpxSession, HttpxSession
from supabase_utils.http.io import SyncHttpIO

from postgrest import (
    APIError,
    AsyncPostgrestClient,
    CountMethod,
    SyncPostgrestClient,
    TextAPIResponse,
)
from postgrest.request_builder import RPCCountRequestBuilder, RPCFilterRequestBuilder

CSV = "id,name\n1,Paris\n2,Lyon\n"


def csv_handler(request: Request) -> Response:
    assert request.headers["Accept"] == "text/csv"
    return Response(200, text=CSV, headers={"Content-Range": "0-1/2"})


def sync_client() -> SyncPostgrestClient:
    http = Client(transport=MockTransport(csv_handler))
    return SyncPostgrestClient(
        "https://example.com", http_session=HttpxSession(client=http)
    )


def async_client() -> AsyncPostgrestClient:
    http = AsyncClient(transport=MockTransport(csv_handler))
    return AsyncPostgrestClient(
        "https://example.com", http_session=AsyncHttpxSession(client=http)
    )


def test_table_csv_returns_a_text_response_with_the_count() -> None:
    client = sync_client()
    response = (
        client.from_("cities").select("*", count=CountMethod.exact).csv().execute()
    )
    assert response == TextAPIResponse(data=CSV, count=2)


def test_rpc_csv_returns_a_text_response() -> None:
    client = sync_client()
    response = client.rpc("cities", {}).csv().execute()
    assert response == TextAPIResponse(data=CSV, count=None)


async def test_async_rpc_csv_returns_a_text_response() -> None:
    client = async_client()
    response = await client.rpc("cities", {}).csv().execute()
    assert response == TextAPIResponse(data=CSV, count=None)


def test_csv_that_is_not_utf8_raises_api_error() -> None:
    http = Client(transport=MockTransport(lambda _: Response(200, content=b"\xff")))
    client = SyncPostgrestClient(
        "https://example.com", http_session=HttpxSession(client=http)
    )
    with pytest.raises(APIError):
        client.from_("cities").select("*").csv().execute()


def test_rpc_with_head_has_no_csv() -> None:
    client = sync_client()
    builder = client.rpc("cities", {}, count=CountMethod.exact, head=True)
    assert_type(builder, RPCCountRequestBuilder[SyncHttpIO])
    assert not hasattr(builder, "csv")


def test_rpc_with_count_and_without_head_has_csv() -> None:
    client = sync_client()
    builder = client.rpc("cities", {}, count=CountMethod.exact, get=False)
    assert_type(builder, RPCFilterRequestBuilder[SyncHttpIO])
    response = builder.csv().execute()
    assert response == TextAPIResponse(data=CSV, count=2)
