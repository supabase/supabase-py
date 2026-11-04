import httpx
from supabase_utils.http.adapters.httpx import (
    AsyncHttpxSession,
    HttpxSession,
    to_httpx_request,
    to_supabase_response,
)
from supabase_utils.http.headers import Headers
from supabase_utils.http.io import AsyncHttpIO, HttpMethod, SyncHttpIO
from supabase_utils.http.query import URLQuery
from supabase_utils.http.request import JSONRequest, Request, Response
from yarl import URL

BASE_URL = URL("https://example.com/api")


def make_request() -> Request:
    return Request(
        url=URL("https://example.com/api/items?select=id&order=id"),
        method="POST",
        headers=Headers.empty().set("Accept", "a").set("Accept", "b"),
        content=b'{"a":1}',
        delay=None,
    )


def echo(request: httpx.Request) -> httpx.Response:
    return httpx.Response(
        201,
        headers={"X-Method": request.method, "X-Url": str(request.url)},
        content=request.content,
    )


def create_item() -> HttpMethod[Response]:
    return (
        yield JSONRequest(
            path=["items"],
            method="POST",
            body={"name": "x"},
            query=URLQuery.from_mapping({"select": "id"}),
        )
    )


def test_to_httpx_request() -> None:
    request = to_httpx_request(make_request())
    assert request.method == "POST"
    assert str(request.url) == "https://example.com/api/items?select=id&order=id"
    assert request.headers.get_list("accept") == ["a", "b"]
    assert request.content == b'{"a":1}'


def test_to_httpx_request_without_content() -> None:
    request = to_httpx_request(
        Request(
            url=BASE_URL,
            method="GET",
            headers=Headers.empty(),
            content=None,
            delay=None,
        )
    )
    assert request.content == b""


def test_to_supabase_response() -> None:
    request = make_request()
    response = to_supabase_response(
        request,
        httpx.Response(404, headers={"Content-Type": "text/plain"}, content=b"nope"),
    )
    assert response.status == 404
    assert response.content == b"nope"
    assert response.headers.get("content-type") == "text/plain"
    assert response.request is request


def test_sync_session_round_trip() -> None:
    client = httpx.Client(transport=httpx.MockTransport(echo))
    with HttpxSession(client) as session:
        response = SyncHttpIO(session).communicate(
            BASE_URL, Headers.from_mapping({"apikey": "key"}), create_item()
        )
    assert client.is_closed
    assert response.status == 201
    assert response.content == b'{"name":"x"}'
    assert response.headers.get("x-method") == "POST"
    assert response.headers.get("x-url") == "https://example.com/api/items?select=id"


async def test_async_session_round_trip() -> None:
    client = httpx.AsyncClient(transport=httpx.MockTransport(echo))
    async with AsyncHttpxSession(client) as session:
        response = await AsyncHttpIO(session).communicate(
            BASE_URL, Headers.empty(), create_item()
        )
    assert client.is_closed
    assert response.status == 201
    assert response.content == b'{"name":"x"}'


def test_sync_session_sends_headers() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200)

    session = HttpxSession(httpx.Client(transport=httpx.MockTransport(handler)))
    session.send(make_request())
    assert seen[0].headers.get_list("accept") == ["a", "b"]
