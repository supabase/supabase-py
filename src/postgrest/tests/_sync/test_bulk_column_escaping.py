import json

import pytest
from httpx import Client, MockTransport, Request, Response

from postgrest import SyncPostgrestClient


@pytest.mark.parametrize("method", ["insert", "upsert"])
@pytest.mark.parametrize("as_tuple", [False, True], ids=["list", "tuple"])
@pytest.mark.parametrize(
    "column, expected_columns",
    [
        ('a"b', r'"a\"b"'),
        (r"c\d", r'"c\\d"'),
        (r"a\"b", r'"a\\\"b"'),
        ("plain", '"plain"'),
        ("a,b", '"a,b"'),
    ],
)
def test_bulk_write_escapes_column_names(
    method: str, as_tuple: bool, column: str, expected_columns: str
) -> None:
    row = {column: "value"}
    rows = (row,) if as_tuple else [row]

    def handler(request: Request) -> Response:
        assert request.url.params["columns"] == expected_columns
        assert json.loads(request.content) == [{column: "value"}]
        return Response(201, json=[{column: "value"}])

    with Client(transport=MockTransport(handler)) as http_client:
        client = SyncPostgrestClient("https://example.com", http_client=http_client)
        builder = client.table("items")
        query = builder.insert(rows) if method == "insert" else builder.upsert(rows)
        response = query.execute()

    assert response.data == [{column: "value"}]
