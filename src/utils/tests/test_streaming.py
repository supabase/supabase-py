import io as stdlib_io
from collections.abc import AsyncIterator, Callable, Iterator
from types import SimpleNamespace
from typing import override

import aiohttp
import httpx
import pytest
from aiohttp import web
from aiohttp.test_utils import TestServer
from supabase_utils.http import io
from supabase_utils.http.adapters.aiohttp import AsyncAiohttpSession
from supabase_utils.http.adapters.httpx import AsyncHttpxSession, HttpxSession
from supabase_utils.http.body import (
    CHUNK_SIZE,
    FileContent,
    RequestContent,
    async_chunks,
)
from supabase_utils.http.errors import SupabaseTransportError
from supabase_utils.http.headers import Headers
from supabase_utils.http.io import AsyncHttpIO, HttpMethod, SyncHttpIO
from supabase_utils.http.request import (
    AsyncStreamedResponse,
    BytesRequest,
    EmptyRequest,
    Response,
    StreamedResponse,
)
from supabase_utils.http.retry import RetryPolicy
from yarl import URL

BASE_URL = URL("https://example.com/api")
NO_JITTER = RetryPolicy(jitter=0, retryable_methods={"GET", "POST"})


def chunks() -> Iterator[bytes]:
    yield b"hello "
    yield b"world"


async def async_body() -> AsyncIterator[bytes]:
    yield b"hello "
    yield b"world"


def upload(body: BytesRequest) -> HttpMethod[Response]:
    return (yield body)


def post(content: RequestContent) -> BytesRequest:
    return BytesRequest(path=["items"], method="POST", body=content)


def file_content() -> FileContent:
    return FileContent(stdlib_io.BytesIO(b"hello world"))


class FailingStream(httpx.SyncByteStream, httpx.AsyncByteStream):
    @override
    def __iter__(self) -> Iterator[bytes]:
        yield b"part"
        raise httpx.ReadError("connection dropped")

    @override
    async def __aiter__(self) -> AsyncIterator[bytes]:
        yield b"part"
        raise httpx.ReadError("connection dropped")


class Recorder:
    def __init__(self, statuses: list[int] | None = None) -> None:
        self.statuses = statuses or [200]
        self.requests: list[httpx.Request] = []
        self.bodies: list[bytes] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        self.bodies.append(request.read())
        status = self.statuses[min(len(self.requests), len(self.statuses)) - 1]
        if request.url.path.endswith("/broken"):
            return httpx.Response(status, stream=FailingStream())
        return httpx.Response(status, content=b"0123456789")


def sync_io(recorder: Recorder) -> SyncHttpIO:
    client = httpx.Client(transport=httpx.MockTransport(recorder))
    return SyncHttpIO(HttpxSession(client), retry=NO_JITTER)


def async_io(recorder: Recorder) -> AsyncHttpIO:
    client = httpx.AsyncClient(transport=httpx.MockTransport(recorder))
    return AsyncHttpIO(AsyncHttpxSession(client), retry=NO_JITTER)


@pytest.fixture
def sleeps(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    sleeps: list[float] = []
    monkeypatch.setattr(io, "time", SimpleNamespace(sleep=sleeps.append))
    return sleeps


def test_file_content_reads_from_the_initial_position_every_time() -> None:
    file = stdlib_io.BytesIO(b"skip-hello")
    file.seek(5)
    content = FileContent(file)
    assert content.length == 5
    assert b"".join(content) == b"hello"
    assert b"".join(content) == b"hello"
    assert content.replayable


async def test_async_chunks_reads_sync_and_async_iterables() -> None:
    assert [chunk async for chunk in async_chunks(chunks())] == [b"hello ", b"world"]
    assert [chunk async for chunk in async_chunks(async_body())] == [
        b"hello ",
        b"world",
    ]


def test_sync_session_streams_a_file_with_its_length() -> None:
    recorder = Recorder()
    content = file_content()
    sync_io(recorder).communicate(BASE_URL, Headers.empty(), upload(post(content)))
    assert recorder.bodies == [b"hello world"]
    assert recorder.requests[0].headers["content-length"] == "11"
    assert "transfer-encoding" not in recorder.requests[0].headers


def test_sync_session_streams_an_iterator_in_chunks() -> None:
    recorder = Recorder()
    sync_io(recorder).communicate(BASE_URL, Headers.empty(), upload(post(chunks())))
    assert recorder.bodies == [b"hello world"]
    assert recorder.requests[0].headers["transfer-encoding"] == "chunked"


def test_sync_executor_rejects_an_async_iterable() -> None:
    with pytest.raises(TypeError, match="async iterable"):
        sync_io(Recorder()).communicate(
            BASE_URL, Headers.empty(), upload(post(async_body()))
        )


@pytest.mark.parametrize("content", [chunks, async_body, file_content])
async def test_async_session_streams_every_body(
    content: Callable[[], RequestContent],
) -> None:
    recorder = Recorder()
    await async_io(recorder).communicate(
        BASE_URL, Headers.empty(), upload(post(content()))
    )
    assert recorder.bodies == [b"hello world"]


def test_a_seekable_file_is_sent_whole_on_every_retry(sleeps: list[float]) -> None:
    recorder = Recorder([503, 200])
    content = file_content()
    sync_io(recorder).communicate(BASE_URL, Headers.empty(), upload(post(content)))
    assert recorder.bodies == [b"hello world", b"hello world"]
    assert sleeps == [0.5]


def test_an_iterator_body_is_never_retried(sleeps: list[float]) -> None:
    recorder = Recorder([503, 200])
    response = sync_io(recorder).communicate(
        BASE_URL, Headers.empty(), upload(post(chunks()))
    )
    assert response.status == 503
    assert len(recorder.requests) == 1
    assert sleeps == []


def test_sync_stream_returns_the_head_before_the_body() -> None:
    recorder = Recorder()
    executor = sync_io(recorder)
    with executor.stream(
        BASE_URL, Headers.empty(), EmptyRequest(path=["file"], method="GET")
    ) as response:
        assert response.status == 200
        assert response.headers.get("content-length") == "10"
        assert b"".join(response.body) == b"0123456789"


async def test_async_stream_returns_the_head_before_the_body() -> None:
    recorder = Recorder()
    async with async_io(recorder).stream(
        BASE_URL, Headers.empty(), EmptyRequest(path=["file"], method="GET")
    ) as response:
        assert response.is_success
        assert (await response.read()).content == b"0123456789"


def test_sync_stream_retries_before_the_head(sleeps: list[float]) -> None:
    recorder = Recorder([503, 200])
    with sync_io(recorder).stream(
        BASE_URL, Headers.empty(), EmptyRequest(path=["file"], method="GET")
    ) as response:
        assert response.status == 200
    assert [r.headers.get("x-retry-count") for r in recorder.requests] == [None, "1"]
    assert sleeps == [0.5]


def test_sync_stream_failure_in_the_body_is_a_transport_error_and_not_retried(
    sleeps: list[float],
) -> None:
    recorder = Recorder()
    with (
        pytest.raises(SupabaseTransportError),
        sync_io(recorder).stream(
            BASE_URL, Headers.empty(), EmptyRequest(path=["broken"], method="GET")
        ) as response,
    ):
        for _ in response.body:
            pass
    assert len(recorder.requests) == 1
    assert sleeps == []


async def read_all(executor: AsyncHttpIO, base_url: URL, path: str) -> bytes:
    async with executor.stream(
        base_url, Headers.empty(), EmptyRequest(path=[path], method="GET")
    ) as response:
        return b"".join([chunk async for chunk in response.body])


async def test_async_stream_failure_in_the_body_is_a_transport_error() -> None:
    recorder = Recorder()
    with pytest.raises(SupabaseTransportError):
        await read_all(async_io(recorder), BASE_URL, "broken")
    assert len(recorder.requests) == 1


class DropsFirstBody:
    """Serves a body that drops halfway the first time, then a whole one."""

    def __init__(self) -> None:
        self.requests: list[httpx.Request] = []

    def __call__(self, request: httpx.Request) -> httpx.Response:
        self.requests.append(request)
        if len(self.requests) == 1:
            return httpx.Response(200, stream=FailingStream())
        return httpx.Response(200, content=b"0123456789")


def test_sync_receive_retries_a_failure_in_the_body(sleeps: list[float]) -> None:
    server = DropsFirstBody()
    client = httpx.Client(transport=httpx.MockTransport(server))
    seen: list[bytes] = []

    def observe(response: StreamedResponse) -> Iterator[bytes]:
        for chunk in response.body:
            seen.append(chunk)
            yield chunk

    response = SyncHttpIO(HttpxSession(client), retry=NO_JITTER).receive(
        BASE_URL, Headers.empty(), EmptyRequest(path=["file"], method="GET"), observe
    )
    assert response.content == b"0123456789"
    assert seen == [b"part", b"0123456789"]
    assert [r.headers.get("x-retry-count") for r in server.requests] == [None, "1"]
    assert sleeps == [0.5]


def test_sync_receive_reads_an_error_body_without_observing_it(
    sleeps: list[float],
) -> None:
    recorder = Recorder([503, 404])

    def observe(response: StreamedResponse) -> Iterator[bytes]:
        pytest.fail("an error body must not be observed")

    response = sync_io(recorder).receive(
        BASE_URL, Headers.empty(), EmptyRequest(path=["file"], method="GET"), observe
    )
    assert response.status == 404
    assert response.content == b"0123456789"
    assert len(recorder.requests) == 2


async def test_async_receive_retries_a_failure_in_the_body(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sleeps: list[float] = []

    async def fake_sleep(delay: float) -> None:
        sleeps.append(delay)

    monkeypatch.setattr(io, "asyncio", SimpleNamespace(sleep=fake_sleep))
    server = DropsFirstBody()
    client = httpx.AsyncClient(transport=httpx.MockTransport(server))
    seen: list[bytes] = []

    async def observe(response: AsyncStreamedResponse) -> AsyncIterator[bytes]:
        async for chunk in response.body:
            seen.append(chunk)
            yield chunk

    response = await AsyncHttpIO(AsyncHttpxSession(client), retry=NO_JITTER).receive(
        BASE_URL, Headers.empty(), EmptyRequest(path=["file"], method="GET"), observe
    )
    assert response.content == b"0123456789"
    assert seen == [b"part", b"0123456789"]
    assert sleeps == [0.5]


async def echo(request: web.Request) -> web.Response:
    return web.Response(
        body=await request.read(),
        headers={"X-Transfer-Encoding": request.headers.get("Transfer-Encoding", "")},
    )


async def truncated(request: web.Request) -> web.StreamResponse:
    response = web.StreamResponse(headers={"Content-Length": "100"})
    await response.prepare(request)
    await response.write(b"part")
    assert request.transport is not None
    request.transport.close()
    return response


@pytest.fixture
async def server() -> AsyncIterator[TestServer]:
    app = web.Application()
    app.router.add_route("*", "/api/items", echo)
    app.router.add_route("*", "/api/truncated", truncated)
    test_server = TestServer(app)
    await test_server.start_server()
    yield test_server
    await test_server.close()


async def test_aiohttp_streams_an_upload_and_a_download(server: TestServer) -> None:
    async with (
        AsyncAiohttpSession(aiohttp.ClientSession()) as session,
        AsyncHttpIO(session).stream(
            server.make_url("/api"), Headers.empty(), post(async_body())
        ) as response,
    ):
        assert response.headers.get("x-transfer-encoding") == "chunked"
        assert b"".join([c async for c in response.body]) == b"hello world"


async def test_aiohttp_failure_in_the_body_is_a_transport_error(
    server: TestServer,
) -> None:
    async with AsyncAiohttpSession(aiohttp.ClientSession()) as session:
        with pytest.raises(SupabaseTransportError):
            await read_all(AsyncHttpIO(session), server.make_url("/api"), "truncated")


def test_file_content_iterations_keep_their_own_position() -> None:
    content = FileContent(stdlib_io.BytesIO(b"a" * CHUNK_SIZE + b"b"))
    abandoned = iter(content)
    retried = iter(content)
    assert next(abandoned) == b"a" * CHUNK_SIZE
    assert next(retried) == b"a" * CHUNK_SIZE
    assert next(abandoned) == b"b"
    assert next(retried) == b"b"


def redirecting(bodies: list[bytes], status: int = 308) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        bodies.append(request.read())
        if request.url.path.endswith("/items"):
            return httpx.Response(status, headers={"Location": "/api/moved"})
        return httpx.Response(200)

    return httpx.MockTransport(handler)


@pytest.mark.parametrize(
    ("content", "status", "sent"),
    [(file_content, 200, [b"hello world"] * 2), (chunks, 308, [b"hello world"])],
)
def test_sync_session_follows_a_body_keeping_redirect_only_with_a_replayable_body(
    content: Callable[[], RequestContent], status: int, sent: list[bytes]
) -> None:
    bodies: list[bytes] = []
    client = httpx.Client(transport=redirecting(bodies), follow_redirects=True)
    response = SyncHttpIO(HttpxSession(client)).communicate(
        BASE_URL, Headers.empty(), upload(post(content()))
    )
    assert response.status == status
    assert bodies == sent


@pytest.mark.parametrize(
    ("content", "status", "sent"),
    [
        (file_content, 200, [b"hello world"] * 2),
        (async_body, 308, [b"hello world"]),
    ],
)
async def test_async_session_follows_a_body_keeping_redirect_only_with_a_replayable_body(
    content: Callable[[], RequestContent], status: int, sent: list[bytes]
) -> None:
    bodies: list[bytes] = []
    client = httpx.AsyncClient(transport=redirecting(bodies), follow_redirects=True)
    response = await AsyncHttpIO(AsyncHttpxSession(client)).communicate(
        BASE_URL, Headers.empty(), upload(post(content()))
    )
    assert response.status == status
    assert bodies == sent


def test_sync_session_does_not_follow_a_method_keeping_301_with_a_one_shot_body() -> (
    None
):
    bodies: list[bytes] = []
    client = httpx.Client(transport=redirecting(bodies, 301), follow_redirects=True)
    request = BytesRequest(path=["items"], method="PUT", body=chunks())
    response = SyncHttpIO(HttpxSession(client)).communicate(
        BASE_URL, Headers.empty(), upload(request)
    )
    assert response.status == 301
    assert bodies == [b"hello world"]


def test_sync_session_follows_a_301_that_turns_a_post_into_a_get() -> None:
    bodies: list[bytes] = []
    client = httpx.Client(transport=redirecting(bodies, 301), follow_redirects=True)
    response = SyncHttpIO(HttpxSession(client)).communicate(
        BASE_URL, Headers.empty(), upload(post(chunks()))
    )
    assert response.status == 200
    assert bodies == [b"hello world", b""]
