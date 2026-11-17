import asyncio
from collections.abc import AsyncGenerator, AsyncIterator, Callable, Coroutine
from contextlib import AbstractAsyncContextManager, asynccontextmanager
from types import SimpleNamespace
from typing import Any, NoReturn

import aiohttp
import httpx
import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer
from supabase_utils.http import io
from supabase_utils.http.adapters.aiohttp import AsyncAiohttpSession
from supabase_utils.http.adapters.httpx import AsyncHttpxSession
from supabase_utils.http.io import AsyncHttpSession
from supabase_utils.http.request import HTTPRequestMethod
from supabase_utils.http.retry import RetryPolicy

from supabase_functions.client import AsyncFunctionsClient

WAIT = 5
RETRY_DELAY = 0.1


class FunctionsServer:
    def __init__(self) -> None:
        self.received = asyncio.Event()
        self.disconnected = asyncio.Event()
        self.flaky_requests = 0

    async def hang(self, request: web.Request) -> NoReturn:
        self.received.set()
        try:
            await asyncio.get_running_loop().create_future()
        finally:
            self.disconnected.set()
        raise AssertionError("the client never disconnected")

    async def flaky(self, request: web.Request) -> web.Response:
        self.flaky_requests += 1
        return web.Response(status=503)

    async def ok(self, request: web.Request) -> web.Response:
        return web.Response(text="ok")


@pytest.fixture
async def functions_server() -> AsyncIterator[tuple[FunctionsServer, TestServer]]:
    functions = FunctionsServer()
    app = web.Application()
    app.router.add_route("*", "/functions/v1/hang", functions.hang)
    app.router.add_route("*", "/functions/v1/flaky", functions.flaky)
    app.router.add_route("*", "/functions/v1/ok", functions.ok)
    server = TestServer(app, handler_cancellation=True)
    await server.start_server()
    yield functions, server
    await server.close()


@asynccontextmanager
async def aiohttp_session() -> AsyncGenerator[AsyncHttpSession]:
    async with AsyncAiohttpSession(
        aiohttp.ClientSession(connector=aiohttp.TCPConnector(limit=1))
    ) as session:
        yield session


@asynccontextmanager
async def httpx_session() -> AsyncGenerator[AsyncHttpSession]:
    async with AsyncHttpxSession(
        httpx.AsyncClient(limits=httpx.Limits(max_connections=1))
    ) as session:
        yield session


SessionFactory = Callable[[], AbstractAsyncContextManager[AsyncHttpSession]]


@pytest.fixture(params=[aiohttp_session, httpx_session], ids=["aiohttp", "httpx"])
async def client(
    request: pytest.FixtureRequest,
    functions_server: tuple[FunctionsServer, TestServer],
) -> AsyncIterator[AsyncFunctionsClient]:
    _, server = functions_server
    session_factory: SessionFactory = request.param
    async with session_factory() as session:
        yield AsyncFunctionsClient(
            url=str(server.make_url("/functions/v1")),
            headers={},
            http_session=session,
            retry=RetryPolicy(base_delay=RETRY_DELAY, jitter=0),
        )


async def invoke(
    client: AsyncFunctionsClient, name: str, method: HTTPRequestMethod
) -> None:
    await client.invoke(name, method=method)


async def invoke_stream(
    client: AsyncFunctionsClient, name: str, method: HTTPRequestMethod
) -> None:
    async with client.invoke_stream(name, method=method):
        pass


Invocation = Callable[
    [AsyncFunctionsClient, str, HTTPRequestMethod], Coroutine[Any, Any, None]
]
invocations = pytest.mark.parametrize("invocation", [invoke, invoke_stream])


async def assert_pool_has_a_free_connection(client: AsyncFunctionsClient) -> None:
    async with asyncio.timeout(WAIT):
        response = await client.invoke("ok")
    assert response.content == b"ok"


@invocations
async def test_cancelling_an_invocation_aborts_the_request(
    client: AsyncFunctionsClient,
    functions_server: tuple[FunctionsServer, TestServer],
    invocation: Invocation,
) -> None:
    functions, _ = functions_server
    task = asyncio.create_task(invocation(client, "hang", "POST"))
    async with asyncio.timeout(WAIT):
        await functions.received.wait()

    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task
    async with asyncio.timeout(WAIT):
        await functions.disconnected.wait()
    await assert_pool_has_a_free_connection(client)


@invocations
async def test_cancelling_an_invocation_waiting_to_retry_stops_retrying(
    client: AsyncFunctionsClient,
    functions_server: tuple[FunctionsServer, TestServer],
    invocation: Invocation,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    functions, _ = functions_server
    waiting = asyncio.Event()

    async def sleep(delay: float) -> None:
        waiting.set()
        await asyncio.sleep(delay)

    monkeypatch.setattr(
        io, "asyncio", SimpleNamespace(**vars(asyncio) | {"sleep": sleep})
    )
    task = asyncio.create_task(invocation(client, "flaky", "GET"))
    async with asyncio.timeout(WAIT):
        await waiting.wait()

    task.cancel()

    with pytest.raises(asyncio.CancelledError):
        await task
    await asyncio.sleep(RETRY_DELAY * 3)
    assert functions.flaky_requests == 1
    await assert_pool_has_a_free_connection(client)
