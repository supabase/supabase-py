import json
import re

import pytest
from pydantic import BaseModel
from supabase_utils.http.headers import Headers
from supabase_utils.http.query import URLQuery
from supabase_utils.http.request import (
    BytesRequest,
    DataField,
    EmptyRequest,
    FileField,
    JSONRequest,
    MultipartFormDataRequest,
    PartField,
    Request,
    Response,
    TextRequest,
    encode_multipart_formdata,
)
from yarl import URL

BASE_URL = URL("https://example.com/rest/v1")
DEFAULT_HEADERS = Headers.from_mapping({"apikey": "key", "Accept": "*/*"})


class Item(BaseModel):
    name: str
    description: str | None = None


def make_response(status: int) -> Response:
    request = Request(
        url=BASE_URL,
        method="GET",
        headers=Headers.empty(),
        content=None,
        delay=None,
    )
    return Response(
        headers=Headers.empty(), content=b"", status=status, request=request
    )


@pytest.mark.parametrize(
    ("status", "is_success", "is_error"),
    [
        (199, False, False),
        (200, True, False),
        (204, True, False),
        (299, True, False),
        (300, False, False),
        (399, False, False),
        (400, False, True),
        (404, False, True),
        (500, False, True),
        (599, False, True),
        (600, False, False),
    ],
)
def test_response_status(status: int, is_success: bool, is_error: bool) -> None:
    response = make_response(status)
    assert response.is_success is is_success
    assert response.is_error is is_error


def test_empty_request_finalize() -> None:
    request = EmptyRequest(
        path=["users", "42"],
        method="GET",
        headers=Headers.from_mapping({"Accept": "application/json"}),
        query=URLQuery.from_mapping({"select": "id,name"}),
        delay=1.5,
    ).finalize(BASE_URL, DEFAULT_HEADERS)
    assert request.method == "GET"
    assert str(request.url) == "https://example.com/rest/v1/users/42?select=id,name"
    assert request.headers.get("apikey") == "key"
    assert request.headers.get("accept") == "application/json"
    assert request.content is None
    assert request.delay == 1.5


def test_empty_request_defaults() -> None:
    request = EmptyRequest(path=[], method="HEAD").finalize(BASE_URL, Headers.empty())
    assert request.url == BASE_URL
    assert len(request.headers) == 0
    assert request.delay is None
    assert request.timeout is None


@pytest.mark.parametrize(
    "to_request",
    [
        EmptyRequest(path=[], method="GET", timeout=3),
        BytesRequest(path=[], method="POST", body=b"x", timeout=3),
        JSONRequest(path=[], method="POST", body={}, timeout=3),
        TextRequest(path=[], method="POST", text="x", timeout=3),
        MultipartFormDataRequest(path=[], method="POST", fields=[], timeout=3),
    ],
)
def test_finalize_keeps_timeout(to_request: EmptyRequest) -> None:
    assert to_request.finalize(BASE_URL, Headers.empty()).timeout == 3


def test_path_segments_are_encoded() -> None:
    request = EmptyRequest(path=["a b", "c"], method="GET").finalize(
        BASE_URL, Headers.empty()
    )
    assert request.url.raw_path == "/rest/v1/a%20b/c"


def test_bytes_request_sets_content_type() -> None:
    request = BytesRequest(path=["upload"], method="PUT", body=b"\x00\x01").finalize(
        BASE_URL, DEFAULT_HEADERS
    )
    assert request.content == b"\x00\x01"
    assert request.headers.get("content-type") == "application/octet-stream"
    assert request.headers.get("apikey") == "key"


def test_explicit_content_type_is_kept() -> None:
    request = BytesRequest(
        path=["upload"],
        method="PUT",
        body=b"<svg/>",
        headers=Headers.from_mapping({"Content-Type": "image/svg+xml"}),
    ).finalize(BASE_URL, DEFAULT_HEADERS)
    assert request.headers.get_list("content-type") == ["image/svg+xml"]


def test_default_content_type_is_overridden() -> None:
    defaults = DEFAULT_HEADERS.set("Content-Type", "text/html")
    request = JSONRequest(path=[], method="POST", body={"a": 1}).finalize(
        BASE_URL, defaults
    )
    assert request.headers.get_list("content-type") == ["application/json"]


def test_json_request_with_json_body() -> None:
    body = {"name": "x", "tags": ["a", "b"], "count": 1, "nested": {"ok": None}}
    request = JSONRequest(path=["items"], method="POST", body=body).finalize(
        BASE_URL, DEFAULT_HEADERS
    )
    assert request.content is not None
    assert json.loads(request.content) == body
    assert request.headers.get("content-type") == "application/json"


def test_json_request_with_model_excludes_none() -> None:
    request = JSONRequest(path=["items"], method="POST", body=Item(name="x")).finalize(
        BASE_URL, Headers.empty()
    )
    assert request.content is not None
    assert json.loads(request.content) == {"name": "x"}


def test_json_request_with_model_keeps_none_when_asked() -> None:
    request = JSONRequest(
        path=["items"], method="PATCH", body=Item(name="x"), exclude_none=False
    ).finalize(BASE_URL, Headers.empty())
    assert request.content is not None
    assert json.loads(request.content) == {"name": "x", "description": None}


def test_text_request() -> None:
    request = TextRequest(path=["echo"], method="POST", text="héllo").finalize(
        BASE_URL, Headers.empty()
    )
    assert request.content == "héllo".encode()
    assert request.headers.get("content-type") == "text/plain; charset=utf-8"


def test_data_field_render_headers() -> None:
    field = DataField(
        name="metadata",
        data=b"{}",
        headers={"X-Custom": "1", "X-Empty": ""},
    )
    assert field.render_headers() == (
        b'Content-Disposition: form-data; name="metadata"\r\nX-Custom: 1\r\n\r\n'
    )


def test_file_field_render_headers() -> None:
    field = FileField(
        name="file",
        data=b"content",
        filename="a.txt",
        content_type="text/plain",
        content_location="/files/a.txt",
        content_disposition="attachment",
        headers={"Cache-Control": "max-age=3600"},
    )
    assert field.render_headers() == (
        b"Content-Type: text/plain\r\n"
        b'Content-Disposition: attachment; name="file"; filename="a.txt"\r\n'
        b"Content-Location: /files/a.txt\r\n"
        b"Cache-Control: max-age=3600\r\n"
        b"\r\n"
    )


def test_encode_multipart_formdata() -> None:
    fields: list[PartField] = [
        DataField(name="cacheControl", data=b"3600"),
        FileField(
            name="file", data=b"hello", filename="a.txt", content_type="text/plain"
        ),
    ]
    body, content_type = encode_multipart_formdata(fields)
    match = re.fullmatch(r"multipart/form-data; boundary=([0-9a-f]{32})", content_type)
    assert match is not None
    boundary = match.group(1).encode()
    assert body == (
        b"--" + boundary + b"\r\n"
        b'Content-Disposition: form-data; name="cacheControl"\r\n\r\n'
        b"3600\r\n"
        b"--" + boundary + b"\r\n"
        b"Content-Type: text/plain\r\n"
        b'Content-Disposition: form-data; name="file"; filename="a.txt"\r\n\r\n'
        b"hello\r\n"
        b"--" + boundary + b"--\r\n"
    )


def test_multipart_boundary_is_random() -> None:
    _, first = encode_multipart_formdata([])
    _, second = encode_multipart_formdata([])
    assert first != second


def test_multipart_request_overrides_content_type() -> None:
    request = MultipartFormDataRequest(
        path=["object", "bucket", "a.txt"],
        method="POST",
        fields=[DataField(name="a", data=b"1")],
        headers=Headers.from_mapping({"Content-Type": "application/json"}),
    ).finalize(BASE_URL, DEFAULT_HEADERS)
    content_type = request.headers.get_list("content-type")
    assert content_type is not None
    assert len(content_type) == 1
    assert content_type[0].startswith("multipart/form-data; boundary=")
    assert request.content is not None
    assert b'name="a"' in request.content
