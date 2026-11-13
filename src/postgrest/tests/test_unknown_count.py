import pytest
from httpx import Client, MockTransport, Request, Response
from supabase_utils.http.adapters.httpx import HttpxSession

from postgrest import SyncPostgrestClient
from postgrest.request_builder import APIResponse
from postgrest.types import CountMethod


@pytest.mark.parametrize("content_range", ["*/*", "0-0/*"])
def test_unknown_total_is_no_count(content_range: str) -> None:
    assert APIResponse._get_count_from_content_range_header(content_range) is None


@pytest.mark.parametrize("count", [CountMethod.planned, CountMethod.estimated])
def test_insert_with_an_unknown_total_returns_its_rows_without_a_count(
    count: CountMethod,
) -> None:
    def handler(request: Request) -> Response:
        return Response(201, json=[{"id": 1}], headers={"Content-Range": "*/*"})

    with Client(transport=MockTransport(handler)) as http:
        client = SyncPostgrestClient(
            "https://example.com", http_session=HttpxSession(client=http)
        )
        response = client.from_("items").insert({"id": 1}, count=count).execute()

    assert response.data == [{"id": 1}]
    assert response.count is None
