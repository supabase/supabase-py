from collections.abc import AsyncIterator

import aiohttp
import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer
from supabase_utils.http.adapters.aiohttp import AsyncAiohttpSession
from supabase_utils.http.headers import Headers
from supabase_utils.http.io import AsyncHttpIO, HttpMethod
from supabase_utils.http.query import URLQuery
from supabase_utils.http.request import EmptyRequest, JSONRequest, Response
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
        },
    )


async def not_found(request: web.Request) -> web.Response:
    return web.Response(status=404, text="missing")


@pytest.fixture
async def server() -> AsyncIterator[TestServer]:
    app = web.Application()
    app.router.add_route("*", "/api/items", echo)
    app.router.add_route("*", "/api/missing", not_found)
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
