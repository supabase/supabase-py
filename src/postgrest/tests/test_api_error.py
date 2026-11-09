import pickle
from typing import Any

import pytest
from httpx import Client, MockTransport, Request, Response
from supabase_utils.errors import SupabaseError
from supabase_utils.http.adapters.httpx import HttpxSession
from supabase_utils.http.errors import SupabaseAPIError

from postgrest import APIError, SyncPostgrestClient


@pytest.mark.parametrize(
    ("body", "message", "details"),
    [
        (b'{"message": "JWT expired"}', "JWT expired", None),
        (
            b'{"code": "PGRST201", "details": [{"x": 1}], "hint": null, "message": "m"}',
            "m",
            [{"x": 1}],
        ),
    ],
)
def test_response_error_json_missing_or_non_string_fields(
    body: bytes, message: str, details: Any
) -> None:
    def handler(request: Request) -> Response:
        return Response(400, content=body)

    with Client(transport=MockTransport(handler)) as http:
        client = SyncPostgrestClient(
            "https://example.com", http_session=HttpxSession(client=http)
        )
        with pytest.raises(APIError) as exc_info:
            client.from_("test").select("a").execute()

    assert exc_info.value.message == message
    assert exc_info.value.details == details


def test_api_error_is_a_supabase_api_error() -> None:
    assert issubclass(APIError, SupabaseAPIError)
    assert issubclass(APIError, SupabaseError)


def test_api_error_carries_status_code_and_response() -> None:
    body = b'{"code": "PGRST116", "details": "0 rows", "hint": null, "message": "one row expected"}'

    def handler(request: Request) -> Response:
        return Response(406, content=body)

    with Client(transport=MockTransport(handler)) as http:
        client = SyncPostgrestClient(
            "https://example.com", http_session=HttpxSession(client=http)
        )
        with pytest.raises(APIError) as exc_info:
            client.from_("test").select("a").execute()

    error = exc_info.value
    assert str(error) == "one row expected"
    assert error.message == "one row expected"
    assert error.code == "PGRST116"
    assert error.hint is None
    assert error.details == "0 rows"
    assert error.status_code == 406
    assert error.response is not None
    assert error.response.content == body
    assert error.json() == {
        "code": "PGRST116",
        "details": "0 rows",
        "hint": None,
        "message": "one row expected",
    }


def test_api_error_without_json_body_keeps_the_status() -> None:
    def handler(request: Request) -> Response:
        return Response(502, content=b"<html>bad gateway</html>")

    with Client(transport=MockTransport(handler)) as http:
        client = SyncPostgrestClient(
            "https://example.com", http_session=HttpxSession(client=http)
        )
        with pytest.raises(APIError) as exc_info:
            client.from_("test").select("a").execute()

    error = exc_info.value
    assert error.status_code == 502
    assert error.code == "502"
    assert error.message == "JSON could not be generated"
    assert "bad gateway" in str(error.details)


def test_api_error_can_be_pickled() -> None:
    error = APIError({"message": "m", "code": "c", "hint": "h"}, status_code=400)
    clone = pickle.loads(pickle.dumps(error))
    assert isinstance(clone, APIError)
    assert str(clone) == "m"
    assert clone.code == "c"
    assert clone.hint == "h"
    assert clone.status_code == 400
    assert clone.json() == error.json()


def test_single_with_invalid_body_raises_api_error() -> None:
    def handler(request: Request) -> Response:
        return Response(200, content=b"not json")

    with Client(transport=MockTransport(handler)) as http:
        client = SyncPostgrestClient(
            "https://example.com", http_session=HttpxSession(client=http)
        )
        with pytest.raises(APIError) as exc_info:
            client.from_("test").select("a").single().execute()

    error = exc_info.value
    assert error.status_code == 200
    assert error.message == "JSON could not be generated"
    assert error.response is not None
    assert error.response.content == b"not json"
