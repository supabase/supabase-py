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
def test_rpc_query_params_quote_array_elements(head: bool) -> None:
    with Client() as http:
        client = SyncPostgrestClient(
            "https://example.com", http_session=HttpxSession(client=http)
        )
        params: Any = {"tags": ["a,b", "c d", "", 'say "hi"', "x}", "null", None]}
        builder = client.rpc("tag_fn", params, head=head, get=not head)

        assert builder.request.query.get_list("tags") == [
            '{"a,b","c d","","say \\"hi\\"","x}","null",NULL}'
        ]


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


def test_rpc_query_params_serialize_scalars_like_postgrest_expects() -> None:
    with Client() as http:
        client = SyncPostgrestClient(
            "https://example.com", http_session=HttpxSession(client=http)
        )
        builder = client.rpc(
            "fn", {"flag": True, "off": False, "x": None, "obj": {"a": 1}}, get=True
        )

        assert builder.request.query["flag"] == "true"
        assert builder.request.query["off"] == "false"
        assert builder.request.query.get_list("x") == [""]
        assert builder.request.query["obj"] == '{"a":1}'


def test_rpc_retry_can_be_disabled() -> None:
    attempts: list[Request] = []

    def handler(request: Request) -> Response:
        attempts.append(request)
        return Response(503, json={"message": "unavailable"})

    with Client(transport=MockTransport(handler)) as http:
        client = SyncPostgrestClient(
            "https://example.com", http_session=HttpxSession(client=http)
        )
        with pytest.raises(APIError):
            client.rpc("fn", {}, get=True).retry(False).execute()

    assert len(attempts) == 1


def test_retry_backoff_and_state_do_not_leak_between_executions() -> None:
    retry_counts: list[str | None] = []

    def handler(request: Request) -> Response:
        retry_counts.append(request.headers.get("X-Retry-Count"))
        return Response(503, json={"message": "unavailable"})

    with Client(transport=MockTransport(handler)) as http:
        client = SyncPostgrestClient(
            "https://example.com", http_session=HttpxSession(client=http)
        )
        builder = client.rpc("fn", {}, get=True)
        with patch("supabase_utils.http.io.time.sleep") as sleep:
            for _ in range(2):
                with pytest.raises(APIError):
                    builder.execute()

    assert retry_counts == [None, "1", "2", "3"] * 2
    assert [call.args[0] for call in sleep.call_args_list] == [1, 2, 4] * 2


def test_head_select_with_empty_body_returns_count() -> None:
    def handler(request: Request) -> Response:
        return Response(200, content=b"", headers={"Content-Range": "*/42"})

    with Client(transport=MockTransport(handler)) as http:
        client = SyncPostgrestClient(
            "https://example.com", http_session=HttpxSession(client=http)
        )
        response = (
            client.from_("users")
            .select("*", count=CountMethod.exact, head=True)
            .execute()
        )

    assert response.data == []
    assert response.count == 42
