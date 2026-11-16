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
    assert error.message == "Bad Gateway"
    assert str(error) == "Bad Gateway"
    assert error.hint is None
    assert error.details == "<html>bad gateway</html>"


@pytest.mark.parametrize(
    ("headers", "code"),
    [
        ([("Proxy-Status", "PostgREST; error=PGRST108")], "PGRST108"),
        ([("Proxy-Status", 'PostgREST; error="42703"')], "42703"),
        ([("Proxy-Status", 'PostgREST; error="a\\"b"')], 'a"b'),
        (
            [
                (
                    "Proxy-Status",
                    "PostgREST; error=PGRST108, cdn; error=http_request_error",
                )
            ],
            "PGRST108",
        ),
        (
            [("Proxy-Status", "cdn; error=connection_timeout, PostgREST; error=57014")],
            "57014",
        ),
        (
            [
                ("Proxy-Status", "cdn; error=connection_timeout"),
                ("Proxy-Status", "PostgREST; error=PGRST301"),
            ],
            "PGRST301",
        ),
        (
            [("Proxy-Status", 'PostgREST; details="a; b, error=x"; error=PGRST116')],
            "PGRST116",
        ),
        ([("Proxy-Status", "cdn; error=connection_timeout")], "400"),
        ([("Proxy-Status", "PostgREST; error=")], "400"),
        ([("Proxy-Status", "PostgREST")], "400"),
        ([], "400"),
    ],
)
def test_api_error_without_body_reads_the_proxy_status_code(
    headers: list[tuple[str, str]], code: str
) -> None:
    def handler(request: Request) -> Response:
        assert request.method == "HEAD"
        return Response(400, headers=headers)

    with Client(transport=MockTransport(handler)) as http:
        client = SyncPostgrestClient(
            "https://example.com", http_session=HttpxSession(client=http)
        )
        with pytest.raises(APIError) as exc_info:
            client.from_("test").select("*", head=True).execute()

    error = exc_info.value
    assert error.code == code
    assert error.message == "Bad Request"
    assert error.hint is None
    assert error.details is None
    assert error.status_code == 400


@pytest.mark.parametrize(
    ("headers", "code"),
    [
        ([("Proxy-Status", "PostgREST; error=PGRST301")], "PGRST301"),
        ([("Proxy-Status", "cdn; error=connection_timeout")], "502"),
        ([], "502"),
    ],
)
def test_api_error_with_non_json_body_keeps_the_decoded_body(
    headers: list[tuple[str, str]], code: str
) -> None:
    body = "<html><body>Bad gateway ü</body></html>"

    def handler(request: Request) -> Response:
        return Response(
            502,
            headers=[*headers, ("Content-Type", "text/html; charset=utf-8")],
            content=body.encode(),
        )

    with Client(transport=MockTransport(handler)) as http:
        client = SyncPostgrestClient(
            "https://example.com", http_session=HttpxSession(client=http)
        )
        with pytest.raises(APIError) as exc_info:
            client.from_("test").select("a").execute()

    error = exc_info.value
    assert error.message == "Bad Gateway"
    assert error.code == code
    assert error.hint is None
    assert error.details == body


@pytest.mark.parametrize(
    ("content_type", "body", "details"),
    [
        ("text/plain; charset=iso-8859-1", "caf\xe9".encode("latin-1"), "café"),
        ('text/plain; charset="ISO-8859-1"', "caf\xe9".encode("latin-1"), "café"),
        ("text/plain; charset=no-such-codec", "café".encode(), "café"),
        ("text/plain", b"caf\xe9", "caf\ufffd"),
        (None, "café".encode(), "café"),
    ],
)
def test_api_error_decodes_the_body_in_its_charset(
    content_type: str | None, body: bytes, details: str
) -> None:
    def handler(request: Request) -> Response:
        headers = [("Content-Type", content_type)] if content_type else []
        return Response(500, headers=headers, content=body)

    with Client(transport=MockTransport(handler)) as http:
        client = SyncPostgrestClient(
            "https://example.com", http_session=HttpxSession(client=http)
        )
        with pytest.raises(APIError) as exc_info:
            client.from_("test").select("a").execute()

    assert exc_info.value.message == "Internal Server Error"
    assert exc_info.value.details == details


def test_api_error_with_an_unknown_status_describes_it() -> None:
    def handler(request: Request) -> Response:
        return Response(599)

    with Client(transport=MockTransport(handler)) as http:
        client = SyncPostgrestClient(
            "https://example.com", http_session=HttpxSession(client=http)
        )
        with pytest.raises(APIError) as exc_info:
            client.from_("test").select("a").execute()

    error = exc_info.value
    assert error.message == "Request failed with status 599"
    assert error.code == "599"
    assert error.status_code == 599
    assert error.details is None


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
    assert error.message == "The response body is not the JSON the query asked for"
    assert error.code == "200"
    assert error.hint is None
    assert error.details == "not json"
    assert error.response is not None
    assert error.response.content == b"not json"
