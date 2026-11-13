from collections.abc import Callable

import pytest
from httpx import Client, MockTransport, Request, Response
from supabase_utils.http.adapters.httpx import HttpxSession

from postgrest import SyncPostgrestClient

Query = Callable[[SyncPostgrestClient], object]

BODYLESS: dict[str, Query] = {
    "select": lambda client: client.from_("items").select("*").execute(),
    "head select": lambda client: client.from_("items")
    .select("*", head=True)
    .execute(),
    "rpc get": lambda client: client.rpc("fn", {"x": 1}, get=True).execute(),
    "rpc head": lambda client: client.rpc("fn", {"x": 1}, head=True).execute(),
    "delete": lambda client: client.from_("items").delete().eq("id", 1).execute(),
}


def send(query: Query) -> Request:
    sent: list[Request] = []

    def handler(request: Request) -> Response:
        sent.append(request)
        return Response(200, json=[])

    with Client(transport=MockTransport(handler)) as http:
        query(
            SyncPostgrestClient(
                "https://example.com", http_session=HttpxSession(client=http)
            )
        )
    return sent[0]


@pytest.mark.parametrize("query", BODYLESS.values(), ids=BODYLESS.keys())
def test_a_request_without_a_payload_sends_no_body(query: Query) -> None:
    request = send(query)

    assert request.method in ("GET", "HEAD", "DELETE")
    assert request.content == b""
    assert "content-type" not in request.headers


def test_an_insert_still_sends_its_json_body() -> None:
    request = send(lambda client: client.from_("items").insert({"id": 1}).execute())

    assert request.content == b'{"id":1}'
    assert request.headers["content-type"] == "application/json"
