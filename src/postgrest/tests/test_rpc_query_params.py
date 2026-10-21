from typing import Any
from unittest.mock import patch

import pytest
from httpx import Client, MockTransport, Request, Response
from supabase_utils.http.adapters.httpx import HttpxSession

from postgrest import APIError, SyncPostgrestClient
from postgrest.types import CountMethod


@pytest.mark.parametrize("head", [False, True])
def test_rpc_query_params_send_lists_as_array_literals(head: bool) -> None:
    with Client() as http:
        client = SyncPostgrestClient(
            "https://example.com", http_session=HttpxSession(client=http)
        )
        params: Any = {"ids": [1, 2, 3], "name": "x"}
        builder = client.rpc("sum_ids", params, head=head, get=not head)

        assert builder.request.query.get_list("ids") == ["{1,2,3}"]
        assert builder.request.query["name"] == "x"


def test_rpc_query_params_escape_array_elements() -> None:
    with Client() as http:
        client = SyncPostgrestClient(
            "https://example.com", http_session=HttpxSession(client=http)
        )
        builder = client.rpc("fn", {"tags": ["a,b", None, 'x"y']}, get=True)

        assert builder.request.query.get_list("tags") == ['{"a,b",NULL,"x\\"y"}']


@pytest.mark.parametrize("head", [False, True])
def test_rpc_get_and_head_retry_on_503(head: bool) -> None:
    attempts: list[str | None] = []

    def handler(request: Request) -> Response:
        attempts.append(request.headers.get("X-Retry-Count"))
        if len(attempts) == 1:
            return Response(503, json={"message": "unavailable"})
        return Response(200, json=[], headers={"Content-Range": "0-0/1"})

    with Client(transport=MockTransport(handler)) as http:
        client = SyncPostgrestClient(
            "https://example.com", http_session=HttpxSession(client=http)
        )
        with patch("supabase_utils.http.io.time.sleep"):
            if head:
                client.rpc(
                    "fn", {}, head=True, count=CountMethod.exact, get=False
                ).execute()
            else:
                client.rpc("fn", {}, get=True).execute()

    assert attempts == [None, "1"]


def test_rpc_maybe_single_wraps_invalid_json_in_api_error() -> None:
    def handler(request: Request) -> Response:
        return Response(502, content=b"<html>bad gateway</html>")

    with Client(transport=MockTransport(handler)) as http:
        client = SyncPostgrestClient(
            "https://example.com", http_session=HttpxSession(client=http)
        )
        with pytest.raises(APIError):
            client.rpc("fn", {}).maybe_single().execute()


def test_rpc_maybe_single_wraps_non_list_response_in_api_error() -> None:
    def handler(request: Request) -> Response:
        return Response(200, json={"id": 1})

    with Client(transport=MockTransport(handler)) as http:
        client = SyncPostgrestClient(
            "https://example.com", http_session=HttpxSession(client=http)
        )
        with pytest.raises(APIError):
            client.rpc("fn", {}).maybe_single().execute()
