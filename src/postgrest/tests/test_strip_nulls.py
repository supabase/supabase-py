import pytest
from httpx import Client, MockTransport, Request, Response
from supabase_utils.http.adapters.httpx import HttpxSession

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
        return Response(200, json={} if single else [])

    with Client(transport=MockTransport(handler)) as http:
        client = SyncPostgrestClient(
            "https://example.com", http_session=HttpxSession(client=http)
        )
        query = client.from_("users").select("*").strip_nulls()
        if single:
            query.single().execute()
        else:
            query.execute()


def test_strip_nulls_rejects_csv() -> None:
    with Client() as http:
        client = SyncPostgrestClient(
            "https://example.com", http_session=HttpxSession(client=http)
        )
        query = client.from_("users").select("*")
        query.request.headers = query.request.headers.set("Accept", "text/csv")
        with pytest.raises(ValueError):
            query.strip_nulls()


def test_strip_nulls_rejects_csv_set_after_strip_nulls() -> None:
    with Client() as http:
        client = SyncPostgrestClient(
            "https://example.com", http_session=HttpxSession(client=http)
        )
        query = client.from_("users").select("*").strip_nulls().csv()
        with pytest.raises(ValueError):
            query.execute()
