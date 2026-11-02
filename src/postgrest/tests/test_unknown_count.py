import pytest
from httpx import Client, MockTransport, Request, Response

from postgrest import SyncPostgrestClient
from postgrest.types import JSON, CountMethod


@pytest.mark.parametrize(
    "operation, status, content_range",
    [
        ("insert", 201, "*/*"),
        ("upsert", 201, "*/*"),
        ("update", 200, "0-0/*"),
        ("delete", 200, "*/*"),
        ("rpc", 200, "0-0/*"),
    ],
)
def test_planned_count_with_unknown_total_is_none(
    operation: str, status: int, content_range: str
) -> None:
    row: JSON = {"id": 1, "name": "todo"}

    def handler(request: Request) -> Response:
        assert "count=planned" in request.headers["Prefer"]
        return Response(status, json=[row], headers={"Content-Range": content_range})

    with Client(transport=MockTransport(handler)) as http:
        client = SyncPostgrestClient("https://example.com", http_client=http)
        table = client.from_("todos")
        planned = CountMethod.planned
        response = {
            "insert": lambda: table.insert(row, count=planned).execute(),
            "upsert": lambda: table.upsert(row, count=planned).execute(),
            "update": lambda: table.update(row, count=planned).eq("id", 1).execute(),
            "delete": lambda: table.delete(count=planned).eq("id", 1).execute(),
            "rpc": lambda: client.rpc("list_todos", {}, count=planned).execute(),
        }[operation]()

    assert response.data == [row]
    assert response.count is None
