import pytest
from supabase_utils.http.headers import Headers
from supabase_utils.http.request import Request, Response
from yarl import URL

from storage3.exceptions import StorageApiError, parse_api_error


def _response(content: bytes, status: int = 502) -> Response:
    return Response(
        headers=Headers.empty(),
        content=content,
        status=status,
        request=Request(
            url=URL("https://example.com"),
            method="GET",
            headers=Headers.empty(),
            content=None,
            delay=None,
        ),
    )


def test_parse_api_error_reads_wire_format() -> None:
    """The API sends statusCode/error/message, not status/code/message."""
    err = parse_api_error(
        _response(
            b'{"statusCode":"404","error":"not_found","message":"Object not found"}',
            status=400,
        )
    )
    assert err.message == "Object not found"
    assert err.code == "not_found"
    assert err.status == "404"


def test_parse_api_error_prefers_explicit_code() -> None:
    err = parse_api_error(
        _response(
            b'{"statusCode":413,"error":"Payload too large","message":"nope","code":"PayloadTooLarge"}'
        )
    )
    assert err.code == "PayloadTooLarge"
    assert err.status == 413


@pytest.mark.parametrize(
    "body",
    [
        b'{"code":"PayloadTooLarge"}',
        b"<html>502 Bad Gateway</html>",
        b"[]",
        b"null",
        b'"Service Unavailable"',
        b"",
        b"\xff\xfe not utf-8",
    ],
)
def test_parse_api_error_falls_back_with_real_status(body: bytes) -> None:
    """Unparsable bodies must not crash, and must keep the response status."""
    err = parse_api_error(_response(body, status=502))
    assert isinstance(err, StorageApiError)
    assert err.code == "InternalError"
    assert err.status == 502
