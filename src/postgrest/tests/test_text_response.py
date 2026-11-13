from httpx import AsyncClient, Client, MockTransport, Request, Response
from supabase_utils.http.adapters.httpx import AsyncHttpxSession, HttpxSession

from postgrest import (
    AsyncPostgrestClient,
    CountMethod,
    SyncPostgrestClient,
    TextAPIResponse,
)

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
