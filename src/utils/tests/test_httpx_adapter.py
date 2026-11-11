import pickle
from collections.abc import Callable

import httpx
import pytest
from supabase_utils.http.adapters.httpx import (
    AsyncHttpxSession,
    HttpxSession,
    to_httpx_request,
    to_supabase_response,
)
from supabase_utils.http.errors import RequestTimeoutError, SupabaseTransportError
from supabase_utils.http.headers import Headers
from supabase_utils.http.io import AsyncHttpIO, HttpMethod, SyncHttpIO
from supabase_utils.http.query import URLQuery
from supabase_utils.http.request import EmptyRequest, JSONRequest, Request, Response
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

    client = httpx.Client(transport=httpx.MockTransport(handler))
    with HttpxSession(client) as session:
        session.send(make_request())
    assert seen[0].headers.get_list("accept") == ["a", "b"]


def redirecting_handler(
    location: str, seen: list[httpx.Request]
) -> Callable[[httpx.Request], httpx.Response]:
    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if request.url.path == "/api/items":
            return httpx.Response(302, headers={"Location": location})
        return httpx.Response(200, content=b"done")

    return handler


def make_credential_request() -> Request:
    return Request(
        url=URL("https://project.supabase.co/api/items"),
        method="GET",
        headers=Headers.from_mapping(
            {"apikey": "service-role-key", "Authorization": "Bearer jwt"}
        ),
        content=None,
        delay=None,
    )


CROSS_ORIGIN_LOCATIONS = [
    "https://attacker.example/final",
    "http://project.supabase.co/final",
    "https://project.supabase.co:8443/final",
]


@pytest.mark.parametrize("location", CROSS_ORIGIN_LOCATIONS)
def test_sync_session_drops_credentials_on_cross_origin_redirect(
    location: str,
) -> None:
    seen: list[httpx.Request] = []
    client = httpx.Client(
        transport=httpx.MockTransport(redirecting_handler(location, seen)),
        follow_redirects=True,
    )
    with HttpxSession(client) as session:
        response = session.send(make_credential_request())
    assert response.status == 200
    assert str(seen[1].url) == location
    assert "apikey" not in seen[1].headers
    assert "authorization" not in seen[1].headers


@pytest.mark.parametrize("location", CROSS_ORIGIN_LOCATIONS)
async def test_async_session_drops_credentials_on_cross_origin_redirect(
    location: str,
) -> None:
    seen: list[httpx.Request] = []
    client = httpx.AsyncClient(
        transport=httpx.MockTransport(redirecting_handler(location, seen)),
        follow_redirects=True,
    )
    async with AsyncHttpxSession(client) as session:
        response = await session.send(make_credential_request())
    assert response.status == 200
    assert str(seen[1].url) == location
    assert "apikey" not in seen[1].headers
    assert "authorization" not in seen[1].headers


@pytest.mark.parametrize(
    "location",
    [
        "https://project.supabase.co/final",
        "https://PROJECT.supabase.co:443/final",
        "/final",
    ],
)
def test_sync_session_keeps_credentials_on_same_origin_redirect(
    location: str,
) -> None:
    seen: list[httpx.Request] = []
    client = httpx.Client(
        transport=httpx.MockTransport(redirecting_handler(location, seen)),
        follow_redirects=True,
    )
    with HttpxSession(client) as session:
        session.send(make_credential_request())
    assert seen[1].url.path == "/final"
    assert seen[1].headers.get("apikey") == "service-role-key"
    assert seen[1].headers.get("authorization") == "Bearer jwt"


async def test_async_session_keeps_credentials_on_same_origin_redirect() -> None:
    seen: list[httpx.Request] = []
    client = httpx.AsyncClient(
        transport=httpx.MockTransport(
            redirecting_handler("https://project.supabase.co/final", seen)
        ),
        follow_redirects=True,
    )
    async with AsyncHttpxSession(client) as session:
        await session.send(make_credential_request())
    assert seen[1].headers.get("apikey") == "service-role-key"
    assert seen[1].headers.get("authorization") == "Bearer jwt"


def test_sync_session_returns_redirect_when_client_does_not_follow() -> None:
    seen: list[httpx.Request] = []
    client = httpx.Client(
        transport=httpx.MockTransport(
            redirecting_handler("https://attacker.example/final", seen)
        )
    )
    with HttpxSession(client) as session:
        response = session.send(make_credential_request())
    assert response.status == 302
    assert len(seen) == 1


def test_sync_session_respects_max_redirects() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(302, headers={"Location": "/again"})

    client = httpx.Client(
        transport=httpx.MockTransport(handler),
        follow_redirects=True,
        max_redirects=2,
    )
    with (
        HttpxSession(client) as session,
        pytest.raises(SupabaseTransportError) as error,
    ):
        session.send(make_credential_request())
    assert isinstance(error.value.__cause__, httpx.TooManyRedirects)


async def test_async_session_respects_max_redirects() -> None:
    sent: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        sent.append(request)
        return httpx.Response(302, headers={"Location": "/again"})

    client = httpx.AsyncClient(
        transport=httpx.MockTransport(handler),
        follow_redirects=True,
        max_redirects=2,
    )
    async with AsyncHttpxSession(client) as session:
        with pytest.raises(SupabaseTransportError) as error:
            await session.send(make_credential_request())
    assert isinstance(error.value.__cause__, httpx.TooManyRedirects)
    assert len(sent) == 3


def test_sync_session_does_not_reapply_client_auth_on_cross_origin_redirect() -> None:
    seen: list[httpx.Request] = []
    client = httpx.Client(
        transport=httpx.MockTransport(
            redirecting_handler("https://attacker.example/final", seen)
        ),
        auth=httpx.BasicAuth("user", "secret"),
        follow_redirects=True,
    )
    with HttpxSession(client) as session:
        session.send(make_credential_request())
    assert "authorization" in seen[0].headers
    assert "authorization" not in seen[1].headers


async def test_async_session_keeps_client_auth_on_same_origin_redirect() -> None:
    seen: list[httpx.Request] = []
    client = httpx.AsyncClient(
        transport=httpx.MockTransport(
            redirecting_handler("https://project.supabase.co/final", seen)
        ),
        auth=httpx.BasicAuth("user", "secret"),
        follow_redirects=True,
    )
    async with AsyncHttpxSession(client) as session:
        await session.send(make_credential_request())
    assert seen[1].headers.get("authorization") == seen[0].headers.get("authorization")


def test_sync_session_does_not_resend_credentials_after_leaving_origin() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        if request.url.host == "attacker.example":
            return httpx.Response(
                302, headers={"Location": "https://project.supabase.co/chosen"}
            )
        if request.url.path == "/api/items":
            return httpx.Response(
                302, headers={"Location": "https://attacker.example/bounce"}
            )
        return httpx.Response(200)

    client = httpx.Client(transport=httpx.MockTransport(handler), follow_redirects=True)
    with HttpxSession(client) as session:
        session.send(make_credential_request())
    assert str(seen[2].url) == "https://project.supabase.co/chosen"
    assert "apikey" not in seen[2].headers
    assert "authorization" not in seen[2].headers


def request_with_headers(headers: Headers, url: URL = BASE_URL) -> Request:
    return Request(url=url, method="GET", headers=headers, content=None, delay=None)


def test_sync_session_keeps_request_authorization_over_client_auth() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200)

    client = httpx.Client(
        auth=httpx.BasicAuth("transport", "secret"),
        transport=httpx.MockTransport(handler),
    )
    with HttpxSession(client) as session:
        session.send(
            request_with_headers(
                Headers.from_mapping({"Authorization": "Bearer user-jwt"})
            )
        )
        session.send(request_with_headers(Headers.empty()))
    assert seen[0].headers.get_list("authorization") == ["Bearer user-jwt"]
    assert seen[1].headers["authorization"] == "Basic dHJhbnNwb3J0OnNlY3JldA=="


async def test_async_session_keeps_request_authorization_over_client_auth() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200)

    client = httpx.AsyncClient(
        auth=httpx.BasicAuth("transport", "secret"),
        transport=httpx.MockTransport(handler),
    )
    async with AsyncHttpxSession(client) as session:
        await session.send(
            request_with_headers(
                Headers.from_mapping({"authorization": "Bearer user-jwt"})
            )
        )
        await session.send(request_with_headers(Headers.empty()))
    assert seen[0].headers.get_list("authorization") == ["Bearer user-jwt"]
    assert seen[1].headers["authorization"] == "Basic dHJhbnNwb3J0OnNlY3JldA=="


def test_sync_session_keeps_request_authorization_over_url_credentials() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200)

    client = httpx.Client(transport=httpx.MockTransport(handler))
    with HttpxSession(client) as session:
        session.send(
            request_with_headers(
                Headers.from_mapping({"Authorization": "Bearer user-jwt"}),
                URL("https://user:password@example.com/api"),
            )
        )
    assert seen[0].headers.get_list("authorization") == ["Bearer user-jwt"]


def test_to_httpx_request_sets_timeout() -> None:
    request = make_request()
    request.timeout = 2.5
    assert to_httpx_request(request).extensions["timeout"] == {
        "connect": 2.5,
        "read": 2.5,
        "write": 2.5,
        "pool": 2.5,
    }


def test_sync_session_without_timeout_uses_client_timeout() -> None:
    seen: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        seen.append(request)
        return httpx.Response(200)

    client = httpx.Client(transport=httpx.MockTransport(handler), timeout=7)
    with HttpxSession(client) as session:
        session.send(make_request())
    assert seen[0].extensions["timeout"]["read"] == 7


def get_items() -> HttpMethod[Response]:
    return (yield EmptyRequest(path=["items"], method="GET"))


def time_out(request: httpx.Request) -> httpx.Response:
    raise httpx.ReadTimeout("timed out", request=request)


def test_sync_session_raises_request_timeout_error() -> None:
    client = httpx.Client(transport=httpx.MockTransport(time_out))
    with (
        HttpxSession(client) as session,
        pytest.raises(RequestTimeoutError) as error,
    ):
        SyncHttpIO(session, request_timeout=1).communicate(
            BASE_URL, Headers.empty(), get_items()
        )
    assert isinstance(error.value, TimeoutError)
    assert isinstance(error.value.__cause__, httpx.ReadTimeout)
    assert str(error.value) == "GET https://example.com/api/items timed out"
    assert error.value.request.timeout == 1


async def test_async_session_raises_request_timeout_error() -> None:
    client = httpx.AsyncClient(transport=httpx.MockTransport(time_out))
    async with AsyncHttpxSession(client) as session:
        with pytest.raises(RequestTimeoutError) as error:
            await AsyncHttpIO(session).communicate(
                BASE_URL, Headers.empty(), get_items()
            )
    assert isinstance(error.value.__cause__, httpx.ReadTimeout)


def test_request_timeout_error_can_be_pickled() -> None:
    error = RequestTimeoutError(make_request())
    copy = pickle.loads(pickle.dumps(error))
    assert str(copy) == str(error)
    assert copy.request.url == error.request.url
    assert copy.request.method == error.request.method


def refuse(request: httpx.Request) -> httpx.Response:
    raise httpx.ConnectError("[Errno 61] Connection refused", request=request)


def test_sync_session_wraps_transport_errors() -> None:
    client = httpx.Client(transport=httpx.MockTransport(refuse))
    with (
        HttpxSession(client) as session,
        pytest.raises(SupabaseTransportError) as error,
    ):
        SyncHttpIO(session).communicate(BASE_URL, Headers.empty(), get_items())
    assert not isinstance(error.value, RequestTimeoutError)
    assert isinstance(error.value.__cause__, httpx.ConnectError)
    assert str(error.value) == "GET https://example.com/api/items failed"
    assert error.value.request.method == "GET"


async def test_async_session_wraps_transport_errors() -> None:
    client = httpx.AsyncClient(transport=httpx.MockTransport(refuse))
    async with AsyncHttpxSession(client) as session:
        with pytest.raises(SupabaseTransportError) as error:
            await AsyncHttpIO(session).communicate(
                BASE_URL, Headers.empty(), get_items()
            )
    assert isinstance(error.value.__cause__, httpx.ConnectError)


@pytest.mark.parametrize("owns_client", [True, False])
def test_sync_session_closes_the_client_it_owns(owns_client: bool) -> None:
    client = httpx.Client()
    with HttpxSession(client=client, owns_client=owns_client):
        pass
    assert client.is_closed is owns_client
    client.close()


@pytest.mark.parametrize("owns_client", [True, False])
async def test_async_session_closes_the_client_it_owns(owns_client: bool) -> None:
    client = httpx.AsyncClient()
    async with AsyncHttpxSession(client=client, owns_client=owns_client):
        pass
    assert client.is_closed is owns_client
    await client.aclose()
