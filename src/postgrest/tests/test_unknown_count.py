import pytest
from httpx import Client, MockTransport, Request, Response

from postgrest import SyncPostgrestClient
from postgrest.types import JSON, CountMethod


@pytest.mark.parametrize(
    "operation, content_range",
    [
        ("insert", "*/*"),
        ("update", "0-0/*"),
        ("delete", "*/*"),
        ("rpc", "0-0/*"),
    ],
)
def test_planned_count_with_unknown_total_is_none(
    operation: str, content_range: str
) -> None:
    row: JSON = {"id": 1, "name": "todo"}

    def handler(request: Request) -> Response:
        assert "count=planned" in request.headers["Prefer"]
        return Response(200, json=[row], headers={"Content-Range": content_range})

    with Client(transport=MockTransport(handler)) as http:
        client = SyncPostgrestClient("https://example.com", http_client=http)
        table = client.from_("todos")
        planned = CountMethod.planned
        response = {
            "insert": lambda: table.insert(row, count=planned).execute(),
            "update": lambda: table.update(row, count=planned).eq("id", 1).execute(),
            "delete": lambda: table.delete(count=planned).eq("id", 1).execute(),
            "rpc": lambda: client.rpc("list_todos", {}, count=planned).execute(),
        }[operation]()

    assert response.data == [row]
    assert response.count is None
