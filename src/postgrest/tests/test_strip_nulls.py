import pytest
from httpx import Client, MockTransport, Request, Response
from supabase_utils.http.adapters.httpx import HttpxSession

from postgrest import ResponseShape, SyncPostgrestClient
from postgrest.request_builder import PostgrestRequest


@pytest.mark.parametrize(
    ("single", "expected"),
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
        query = client.rpc("f", {}).csv()
        with pytest.raises(ValueError, match=r"cannot be used with csv\(\)"):
            query.strip_nulls()


def test_strip_nulls_rejects_csv_set_after_strip_nulls() -> None:
    with Client() as http:
        client = SyncPostgrestClient(
            "https://example.com", http_session=HttpxSession(client=http)
        )
        query = client.from_("users").select("*").strip_nulls()
        rpc = client.rpc("f", {}).strip_nulls()
        with pytest.raises(ValueError, match=r"cannot be used with csv\(\)"):
            query.csv()
        with pytest.raises(ValueError, match=r"cannot be used with csv\(\)"):
            rpc.csv()


def test_strip_nulls_rejects_explain() -> None:
    with Client() as http:
        client = SyncPostgrestClient(
            "https://example.com", http_session=HttpxSession(client=http)
        )
        query = client.from_("users").select("*").strip_nulls()
        with pytest.raises(ValueError, match=r"cannot be used with explain\(\)"):
            query.explain()


def test_strip_nulls_rejects_a_request_built_with_csv() -> None:
    with pytest.raises(ValueError, match=r"cannot be used with csv\(\)"):
        PostgrestRequest(
            path=[], method="GET", body={}, shape=ResponseShape.CSV, strip_nulls=True
        )


def test_strip_nulls_rejects_a_custom_accept_header() -> None:
    with Client() as http:
        client = SyncPostgrestClient(
            "https://example.com",
            headers={"Accept": "application/geo+json"},
            http_session=HttpxSession(client=http),
        )
        query = client.from_("users").select("*").strip_nulls()
        with pytest.raises(
            ValueError, match="cannot be used with Accept: application/geo\\+json"
        ):
            query.execute()


def test_a_custom_accept_header_is_kept_without_strip_nulls() -> None:
    def handler(request: Request) -> Response:
        assert request.headers["Accept"] == "application/geo+json"
        return Response(200, json=[])

    with Client(transport=MockTransport(handler)) as http:
        client = SyncPostgrestClient(
            "https://example.com",
            headers={"Accept": "application/geo+json"},
            http_session=HttpxSession(client=http),
        )
        client.from_("users").select("*").execute()
