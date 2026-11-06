import inspect
from types import SimpleNamespace, TracebackType

import pytest
from supabase_utils.http import io
from supabase_utils.http.headers import Headers
from supabase_utils.http.io import (
    AsyncHttpIO,
    HttpMethod,
    SyncHttpIO,
    handle_http_io,
)
from supabase_utils.http.request import EmptyRequest, Request, Response
from yarl import URL

BASE_URL = URL("https://example.com/api")
DEFAULT_HEADERS = Headers.from_mapping({"apikey": "key"})


class Responder:
    def __init__(self, statuses: list[int]) -> None:
        self.statuses = statuses
        self.requests: list[Request] = []

    def respond(self, request: Request) -> Response:
        self.requests.append(request)
        return Response(
            headers=Headers.empty(),
            content=str(len(self.requests)).encode(),
            status=self.statuses[len(self.requests) - 1],
            request=request,
        )


class FakeSession(Responder):
    def send(self, request: Request) -> Response:
        return self.respond(request)

    def __enter__(self) -> "FakeSession":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        pass


class AsyncFakeSession(Responder):
    async def send(self, request: Request) -> Response:
        return self.respond(request)

    async def __aenter__(self) -> "AsyncFakeSession":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        pass


def retry_until_success(attempts: int) -> HttpMethod[list[int]]:
    statuses = []
    for attempt in range(attempts):
        response = yield EmptyRequest(
            path=["items"], method="GET", delay=0.5 if attempt else None
        )
        statuses.append(response.status)
        if response.is_success:
            break
    return statuses


def no_requests(cached: bool = True) -> HttpMethod[str]:
    if not cached:
        yield EmptyRequest(path=["items"], method="GET")
    return "done"


def failing_method() -> HttpMethod[None]:
    response = yield EmptyRequest(path=["items"], method="GET")
    raise ValueError(f"status {response.status}")


def test_sync_communicate_sends_requests_until_return(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr(io, "time", SimpleNamespace(sleep=sleeps.append))
    session = FakeSession([500, 503, 200])
    result = SyncHttpIO(session).communicate(
        BASE_URL, DEFAULT_HEADERS, retry_until_success(5)
    )
    assert result == [500, 503, 200]
    assert sleeps == [0.5, 0.5]
    assert [str(r.url) for r in session.requests] == [
        "https://example.com/api/items"
    ] * 3
    assert all(r.headers.get("apikey") == "key" for r in session.requests)


async def test_async_communicate_sends_requests_until_return(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sleeps: list[float] = []

    async def fake_sleep(delay: float) -> None:
        sleeps.append(delay)

    monkeypatch.setattr(io, "asyncio", SimpleNamespace(sleep=fake_sleep))
    session = AsyncFakeSession([500, 200])
    result = await AsyncHttpIO(session).communicate(
        BASE_URL, DEFAULT_HEADERS, retry_until_success(5)
    )
    assert result == [500, 200]
    assert sleeps == [0.5]
    assert len(session.requests) == 2


def test_sync_communicate_without_requests() -> None:
    session = FakeSession([])
    result = SyncHttpIO(session).communicate(BASE_URL, DEFAULT_HEADERS, no_requests())
    assert result == "done"
    assert session.requests == []


async def test_async_communicate_without_requests() -> None:
    session = AsyncFakeSession([])
    result = await AsyncHttpIO(session).communicate(
        BASE_URL, DEFAULT_HEADERS, no_requests()
    )
    assert result == "done"
    assert session.requests == []


def test_sync_communicate_propagates_errors() -> None:
    with pytest.raises(ValueError, match="status 404"):
        SyncHttpIO(FakeSession([404])).communicate(
            BASE_URL, DEFAULT_HEADERS, failing_method()
        )


async def test_async_communicate_propagates_errors() -> None:
    with pytest.raises(ValueError, match="status 404"):
        await AsyncHttpIO(AsyncFakeSession([404])).communicate(
            BASE_URL, DEFAULT_HEADERS, failing_method()
        )


class Client[HttpIO: (SyncHttpIO, AsyncHttpIO)]:
    def __init__(self, executor: HttpIO) -> None:
        self.executor: HttpIO = executor
        self.base_url = BASE_URL
        self.default_headers = DEFAULT_HEADERS

    @handle_http_io
    def get_item(self, item_id: str, *, select: str = "*") -> HttpMethod[bytes]:
        """Fetches one item."""
        response = yield EmptyRequest(
            path=["items", item_id], method="GET", headers=Headers.empty()
        )
        return response.content + select.encode()


def test_handle_http_io_with_sync_executor() -> None:
    session = FakeSession([200])
    client = Client(SyncHttpIO(session))
    assert client.get_item("7", select="id") == b"1id"
    assert str(session.requests[0].url) == "https://example.com/api/items/7"


async def test_handle_http_io_with_async_executor() -> None:
    session = AsyncFakeSession([200])
    client = Client(AsyncHttpIO(session))
    assert await client.get_item("7") == b"1*"
    assert str(session.requests[0].url) == "https://example.com/api/items/7"


def test_handle_http_io_keeps_metadata() -> None:
    method = Client(SyncHttpIO(FakeSession([]))).get_item
    assert method.__name__ == "get_item"
    assert method.__doc__ == "Fetches one item."
    signature = inspect.signature(method)
    assert list(signature.parameters) == ["item_id", "select"]
    assert signature.return_annotation is inspect.Signature.empty
