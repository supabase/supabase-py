import asyncio
from collections.abc import AsyncIterator

import aiohttp
import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer
from supabase_utils.http.adapters.aiohttp import AsyncAiohttpSession
from supabase_utils.http.errors import RequestTimeoutError, SupabaseTransportError
from supabase_utils.http.headers import Headers
from supabase_utils.http.io import AsyncHttpIO, HttpMethod
from supabase_utils.http.query import URLQuery
from supabase_utils.http.request import EmptyRequest, JSONRequest, Request, Response
from yarl import URL


async def echo(request: web.Request) -> web.Response:
    return web.Response(
        status=201,
        body=await request.read(),
        headers={
            "X-Method": request.method,
            "X-Query": request.query_string,
            "X-Apikey": request.headers.get("apikey", ""),
            "X-Content-Type": request.headers.get("Content-Type", ""),
            "X-Accept": repr(request.headers.getall("Accept", [])),
        },
    )


async def not_found(request: web.Request) -> web.Response:
    return web.Response(status=404, text="missing")


async def slow(request: web.Request) -> web.Response:
    await asyncio.sleep(1)
    return web.Response()


@pytest.fixture
async def server() -> AsyncIterator[TestServer]:
    app = web.Application()
    app.router.add_route("*", "/api/items", echo)
    app.router.add_route("*", "/api/missing", not_found)
    app.router.add_route("*", "/api/slow", slow)
    test_server = TestServer(app)
    await test_server.start_server()
    yield test_server
    await test_server.close()


def base_url(server: TestServer) -> URL:
    return server.make_url("/api")


def create_item() -> HttpMethod[Response]:
    return (
        yield JSONRequest(
            path=["items"],
            method="POST",
            body={"name": "x"},
            query=URLQuery.from_mapping({"select": "id"}),
        )
    )


def get_missing() -> HttpMethod[Response]:
    return (yield EmptyRequest(path=["missing"], method="GET"))


async def test_round_trip(server: TestServer) -> None:
    async with AsyncAiohttpSession(aiohttp.ClientSession()) as session:
        response = await AsyncHttpIO(session).communicate(
            base_url(server), Headers.from_mapping({"apikey": "key"}), create_item()
        )
    assert session.client.closed
    assert response.status == 201
    assert response.content == b'{"name":"x"}'
    assert response.headers.get("x-method") == "POST"
    assert response.headers.get("x-query") == "select=id"
    assert response.headers.get("x-apikey") == "key"
    assert response.headers.get("x-content-type") == "application/json"
    assert str(response.request.url) == str(base_url(server) / "items") + "?select=id"


async def test_error_status_is_returned(server: TestServer) -> None:
    async with AsyncAiohttpSession(aiohttp.ClientSession()) as session:
        response = await AsyncHttpIO(session).communicate(
            base_url(server), Headers.empty(), get_missing()
        )
    assert response.status == 404
    assert response.is_error
    assert response.content == b"missing"
    assert response.headers.get("content-type") == "text/plain; charset=utf-8"


def get_items_with_repeated_accept() -> HttpMethod[Response]:
    headers = Headers.empty().set("Accept", "a").set("Accept", "b")
    return (yield EmptyRequest(path=["items"], method="GET", headers=headers))


async def test_repeated_request_headers_are_joined(server: TestServer) -> None:
    async with AsyncAiohttpSession(aiohttp.ClientSession()) as session:
        response = await AsyncHttpIO(session).communicate(
            base_url(server), Headers.empty(), get_items_with_repeated_accept()
        )
    assert response.headers.get("x-accept") == "['a, b']"


async def record_credentials(request: web.Request) -> web.Response:
    return web.Response(
        headers={
            "X-Apikey": request.headers.get("apikey", ""),
            "X-Authorization": request.headers.get("Authorization", ""),
        },
    )


BOUNCE_TARGETS = web.AppKey("bounce_targets", list[URL])


@pytest.fixture
async def other_origin() -> AsyncIterator[TestServer]:
    async def bounce(request: web.Request) -> web.Response:
        raise web.HTTPFound(request.app[BOUNCE_TARGETS][0])

    app = web.Application()
    app.router.add_route("*", "/final", record_credentials)
    app.router.add_route("*", "/bounce", bounce)
    app[BOUNCE_TARGETS] = []
    test_server = TestServer(app)
    await test_server.start_server()
    yield test_server
    await test_server.close()


@pytest.fixture
async def redirect_server(other_origin: TestServer) -> AsyncIterator[TestServer]:
    async def cross_origin(request: web.Request) -> web.Response:
        raise web.HTTPFound(other_origin.make_url("/final"))

    async def same_origin(request: web.Request) -> web.Response:
        raise web.HTTPFound("/final")

    async def bounce_back(request: web.Request) -> web.Response:
        raise web.HTTPFound(other_origin.make_url("/bounce"))

    app = web.Application()
    app.router.add_route("*", "/cross-origin", cross_origin)
    app.router.add_route("*", "/same-origin", same_origin)
    app.router.add_route("*", "/bounce-back", bounce_back)
    app.router.add_route("*", "/final", record_credentials)
    test_server = TestServer(app)
    await test_server.start_server()
    other_origin.app[BOUNCE_TARGETS].append(test_server.make_url("/final"))
    yield test_server
    await test_server.close()


def credential_request(server: TestServer, path: str) -> Request:
    return Request(
        url=server.make_url(path),
        method="GET",
        headers=Headers.from_mapping(
            {"apikey": "service-role-key", "Authorization": "Bearer jwt"}
        ),
        content=None,
        delay=None,
    )


async def test_drops_credentials_on_cross_origin_redirect(
    redirect_server: TestServer, other_origin: TestServer
) -> None:
    async with AsyncAiohttpSession(aiohttp.ClientSession()) as session:
        response = await session.send(
            credential_request(redirect_server, "/cross-origin")
        )
    assert response.status == 200
    assert response.headers.get("x-apikey") == ""
    assert response.headers.get("x-authorization") == ""


async def test_keeps_credentials_on_same_origin_redirect(
    redirect_server: TestServer,
) -> None:
    async with AsyncAiohttpSession(aiohttp.ClientSession()) as session:
        response = await session.send(
            credential_request(redirect_server, "/same-origin")
        )
    assert response.status == 200
    assert response.headers.get("x-apikey") == "service-role-key"
    assert response.headers.get("x-authorization") == "Bearer jwt"


async def test_keeps_session_middlewares(redirect_server: TestServer) -> None:
    seen: list[URL] = []

    async def record(
        request: aiohttp.ClientRequest, handler: aiohttp.ClientHandlerType
    ) -> aiohttp.ClientResponse:
        seen.append(request.url)
        return await handler(request)

    client = aiohttp.ClientSession(middlewares=(record,))
    async with AsyncAiohttpSession(client) as session:
        await session.send(credential_request(redirect_server, "/same-origin"))
    assert [url.path for url in seen] == ["/same-origin", "/final"]


async def test_does_not_resend_credentials_after_leaving_origin(
    redirect_server: TestServer,
) -> None:
    async with AsyncAiohttpSession(aiohttp.ClientSession()) as session:
        response = await session.send(
            credential_request(redirect_server, "/bounce-back")
        )
    assert response.status == 200
    assert response.headers.get("x-apikey") == ""
    assert response.headers.get("x-authorization") == ""


def get_slow(timeout: float | None) -> HttpMethod[Response]:
    return (yield EmptyRequest(path=["slow"], method="GET", timeout=timeout))


async def test_request_timeout_raises_request_timeout_error(
    server: TestServer,
) -> None:
    async with AsyncAiohttpSession(aiohttp.ClientSession()) as session:
        with pytest.raises(RequestTimeoutError) as error:
            await AsyncHttpIO(session).communicate(
                base_url(server), Headers.empty(), get_slow(0.05)
            )
    assert isinstance(error.value.__cause__, TimeoutError)
    assert error.value.request.timeout == 0.05


async def test_session_timeout_raises_request_timeout_error(
    server: TestServer,
) -> None:
    client = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=0.05))
    async with AsyncAiohttpSession(client) as session:
        with pytest.raises(RequestTimeoutError):
            await AsyncHttpIO(session).communicate(
                base_url(server), Headers.empty(), get_slow(None)
            )


async def test_error_status_is_returned_on_a_session_that_raises(
    server: TestServer,
) -> None:
    client = aiohttp.ClientSession(raise_for_status=True)
    async with AsyncAiohttpSession(client) as session:
        response = await AsyncHttpIO(session).communicate(
            base_url(server), Headers.empty(), get_missing()
        )
    assert response.status == 404
    assert response.content == b"missing"


async def test_connection_failure_raises_transport_error(server: TestServer) -> None:
    unreachable = server.make_url("/api").with_port(1)
    async with AsyncAiohttpSession(aiohttp.ClientSession()) as session:
        with pytest.raises(SupabaseTransportError) as error:
            await AsyncHttpIO(session).communicate(
                unreachable, Headers.empty(), get_missing()
            )
    assert not isinstance(error.value, RequestTimeoutError)
    assert isinstance(error.value.__cause__, aiohttp.ClientConnectorError)
    assert str(error.value).startswith(f"GET {unreachable}/missing failed: ")
    assert error.value.request.method == "GET"


async def test_request_timeout_overrides_session_read_timeout(
    server: TestServer,
) -> None:
    client = aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(sock_read=0.05))
    async with AsyncAiohttpSession(client) as session:
        response = await AsyncHttpIO(session, request_timeout=5).communicate(
            base_url(server), Headers.empty(), get_slow(None)
        )
    assert response.status == 200


async def test_request_timeout_keeps_session_total() -> None:
    client = aiohttp.ClientSession(
        timeout=aiohttp.ClientTimeout(total=30, ceil_threshold=2)
    )
    async with AsyncAiohttpSession(client) as session:
        assert session._timeout(None) is client.timeout
        assert session._timeout(4) == aiohttp.ClientTimeout(
            total=30, connect=4, sock_connect=4, sock_read=4, ceil_threshold=2
        )
