import pytest
from httpx import Client, MockTransport, Request, Response

from postgrest import SyncPostgrestClient


@pytest.mark.parametrize(
    "single, expected",
    [
        (False, "application/vnd.pgrst.array+json;nulls=stripped"),
        (True, "application/vnd.pgrst.object+json;nulls=stripped"),
    ],
)
def test_strip_nulls_sets_accept_header(single: bool, expected: str) -> None:
    def handler(request: Request) -> Response:
        assert request.headers["Accept"] == expected
        return Response(200, json=[])

    with Client(transport=MockTransport(handler)) as http:
        client = SyncPostgrestClient("https://example.com", http_client=http)
        query = client.from_("users").select("*").strip_nulls()
        (query.single() if single else query).execute()
