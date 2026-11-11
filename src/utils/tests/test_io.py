import inspect
from types import SimpleNamespace, TracebackType

import pytest
from supabase_utils.http import io
from supabase_utils.http.errors import RequestTimeoutError, SupabaseTransportError
from supabase_utils.http.headers import Headers
from supabase_utils.http.io import (
    AsyncHttpIO,
    HttpMethod,
    SyncHttpIO,
    handle_http_io,
)
from supabase_utils.http.request import EmptyRequest, JSONRequest, Request, Response
from supabase_utils.http.retry import RetryPolicy
from yarl import URL

BASE_URL = URL("https://example.com/api")
DEFAULT_HEADERS = Headers.from_mapping({"apikey": "key"})


type Outcome = int | type[SupabaseTransportError]


class Responder:
    """Answers each request with the next outcome: a status to respond with,
    or a transport error class to raise."""

    def __init__(self, outcomes: list[Outcome], headers: Headers | None = None) -> None:
        self.outcomes = outcomes
        self.headers = headers or Headers.empty()
        self.requests: list[Request] = []

    def respond(self, request: Request) -> Response:
        self.requests.append(request)
        outcome = self.outcomes[len(self.requests) - 1]
        if not isinstance(outcome, int):
            raise outcome(request)
        return Response(
            headers=self.headers,
            content=str(len(self.requests)).encode(),
            status=outcome,
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
    result = SyncHttpIO(session, retry=RetryPolicy(max_retries=0)).communicate(
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
    result = await AsyncHttpIO(session, retry=RetryPolicy(max_retries=0)).communicate(
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


def two_requests() -> HttpMethod[None]:
    yield EmptyRequest(path=["items"], method="GET")
    yield EmptyRequest(path=["items"], method="GET", timeout=2.5)


def test_sync_communicate_applies_request_timeout() -> None:
    session = FakeSession([200, 200])
    SyncHttpIO(session, request_timeout=10).communicate(
        BASE_URL, DEFAULT_HEADERS, two_requests()
    )
    assert [r.timeout for r in session.requests] == [10, 2.5]


async def test_async_communicate_applies_request_timeout() -> None:
    session = AsyncFakeSession([200, 200])
    await AsyncHttpIO(session, request_timeout=10).communicate(
        BASE_URL, DEFAULT_HEADERS, two_requests()
    )
    assert [r.timeout for r in session.requests] == [10, 2.5]


def test_communicate_without_request_timeout_leaves_it_to_the_session() -> None:
    session = FakeSession([200, 200])
    SyncHttpIO(session).communicate(BASE_URL, DEFAULT_HEADERS, two_requests())
    assert [r.timeout for r in session.requests] == [None, 2.5]


@pytest.mark.parametrize("timeout", [0, -1, float("nan"), float("inf")])
def test_invalid_request_timeout_is_rejected(timeout: float) -> None:
    with pytest.raises(ValueError, match="positive number of seconds"):
        SyncHttpIO(FakeSession([]), request_timeout=timeout)
    with pytest.raises(ValueError, match="positive number of seconds"):
        AsyncHttpIO(AsyncFakeSession([]), request_timeout=timeout)
    with pytest.raises(ValueError, match="positive number of seconds"):
        EmptyRequest(path=[], method="GET", timeout=timeout)
    with pytest.raises(ValueError, match="positive number of seconds"):
        Request(
            url=BASE_URL,
            method="GET",
            headers=Headers.empty(),
            content=None,
            delay=None,
            timeout=timeout,
        )


class SharedRequest:
    def __init__(self) -> None:
        self.request = Request(
            url=BASE_URL,
            method="GET",
            headers=Headers.empty(),
            content=None,
            delay=None,
        )

    def finalize(self, base_url: URL, default_headers: Headers) -> Request:
        return self.request


def test_communicate_does_not_change_the_finalized_request() -> None:
    shared = SharedRequest()

    def send_shared() -> HttpMethod[None]:
        yield shared

    first = FakeSession([200])
    second = FakeSession([200])
    SyncHttpIO(first, request_timeout=10).communicate(
        BASE_URL, DEFAULT_HEADERS, send_shared()
    )
    SyncHttpIO(second, request_timeout=20).communicate(
        BASE_URL, DEFAULT_HEADERS, send_shared()
    )
    assert shared.request.timeout is None
    assert [first.requests[0].timeout, second.requests[0].timeout] == [10, 20]


NO_JITTER = RetryPolicy(jitter=0)


def get_items(retry: RetryPolicy | bool | None = None) -> HttpMethod[int]:
    response = yield EmptyRequest(path=["items"], method="GET", retry=retry)
    return response.status


def create_item(retry: RetryPolicy | bool | None = None) -> HttpMethod[int]:
    response = yield JSONRequest(
        path=["items"], method="POST", body={"name": "x"}, retry=retry
    )
    return response.status


def retry_counts(session: Responder) -> list[str | None]:
    return [request.headers.get("X-Retry-Count") for request in session.requests]


@pytest.fixture
def sync_sleeps(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    sleeps: list[float] = []
    monkeypatch.setattr(io, "time", SimpleNamespace(sleep=sleeps.append))
    return sleeps


@pytest.fixture
def async_sleeps(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    sleeps: list[float] = []

    async def fake_sleep(delay: float) -> None:
        sleeps.append(delay)

    monkeypatch.setattr(io, "asyncio", SimpleNamespace(sleep=fake_sleep))
    return sleeps


def test_executors_default_to_the_default_retry_policy() -> None:
    assert SyncHttpIO(FakeSession([])).retry_policy == RetryPolicy()
    assert AsyncHttpIO(AsyncFakeSession([])).retry_policy == RetryPolicy()
    policy = RetryPolicy(max_retries=5)
    assert SyncHttpIO(FakeSession([]), retry=policy).retry_policy is policy
    assert AsyncHttpIO(AsyncFakeSession([]), retry=policy).retry_policy is policy


def test_sync_executor_retries_a_get_with_backoff(sync_sleeps: list[float]) -> None:
    session = FakeSession([503, 429, 200])
    executor = SyncHttpIO(session, retry=NO_JITTER)
    assert executor.communicate(BASE_URL, DEFAULT_HEADERS, get_items()) == 200
    assert sync_sleeps == [0.5, 1]
    assert retry_counts(session) == [None, "1", "2"]
    assert all(r.url == session.requests[0].url for r in session.requests)


async def test_async_executor_retries_a_get_with_backoff(
    async_sleeps: list[float],
) -> None:
    session = AsyncFakeSession([503, 429, 200])
    executor = AsyncHttpIO(session, retry=NO_JITTER)
    assert await executor.communicate(BASE_URL, DEFAULT_HEADERS, get_items()) == 200
    assert async_sleeps == [0.5, 1]
    assert retry_counts(session) == [None, "1", "2"]


def test_sync_executor_returns_the_last_response_when_retries_run_out(
    sync_sleeps: list[float],
) -> None:
    session = FakeSession([503, 503, 503, 503, 200])
    executor = SyncHttpIO(session, retry=NO_JITTER)
    assert executor.communicate(BASE_URL, DEFAULT_HEADERS, get_items()) == 503
    assert sync_sleeps == [0.5, 1, 2]
    assert len(session.requests) == 4


async def test_async_executor_returns_the_last_response_when_retries_run_out(
    async_sleeps: list[float],
) -> None:
    session = AsyncFakeSession([503, 503])
    executor = AsyncHttpIO(session, retry=RetryPolicy(max_retries=1, jitter=0))
    assert await executor.communicate(BASE_URL, DEFAULT_HEADERS, get_items()) == 503
    assert async_sleeps == [0.5]
    assert len(session.requests) == 2


def test_sync_executor_retries_a_network_error(sync_sleeps: list[float]) -> None:
    session = FakeSession([SupabaseTransportError, RequestTimeoutError, 200])
    executor = SyncHttpIO(session, retry=NO_JITTER)
    assert executor.communicate(BASE_URL, DEFAULT_HEADERS, get_items()) == 200
    assert sync_sleeps == [0.5, 1]
    assert retry_counts(session) == [None, "1", "2"]


async def test_async_executor_retries_a_network_error(
    async_sleeps: list[float],
) -> None:
    session = AsyncFakeSession([RequestTimeoutError, 200])
    executor = AsyncHttpIO(session, retry=NO_JITTER)
    assert await executor.communicate(BASE_URL, DEFAULT_HEADERS, get_items()) == 200
    assert async_sleeps == [0.5]


def test_sync_executor_raises_the_last_network_error(
    sync_sleeps: list[float],
) -> None:
    session = FakeSession([SupabaseTransportError, RequestTimeoutError])
    executor = SyncHttpIO(session, retry=RetryPolicy(max_retries=1, jitter=0))
    with pytest.raises(RequestTimeoutError):
        executor.communicate(BASE_URL, DEFAULT_HEADERS, get_items())
    assert sync_sleeps == [0.5]
    assert len(session.requests) == 2


async def test_async_executor_raises_the_last_network_error(
    async_sleeps: list[float],
) -> None:
    session = AsyncFakeSession([SupabaseTransportError, SupabaseTransportError])
    executor = AsyncHttpIO(session, retry=RetryPolicy(max_retries=1, jitter=0))
    with pytest.raises(SupabaseTransportError):
        await executor.communicate(BASE_URL, DEFAULT_HEADERS, get_items())
    assert async_sleeps == [0.5]


def test_network_errors_are_not_retried_when_the_policy_says_so(
    sync_sleeps: list[float],
) -> None:
    session = FakeSession([SupabaseTransportError])
    executor = SyncHttpIO(session, retry=RetryPolicy(retry_network_errors=False))
    with pytest.raises(SupabaseTransportError):
        executor.communicate(BASE_URL, DEFAULT_HEADERS, get_items())
    assert sync_sleeps == []


def test_sync_executor_waits_the_retry_after_of_the_response(
    sync_sleeps: list[float],
) -> None:
    session = FakeSession(
        [429, 200], headers=Headers.from_mapping({"Retry-After": "3"})
    )
    executor = SyncHttpIO(session, retry=NO_JITTER)
    assert executor.communicate(BASE_URL, DEFAULT_HEADERS, get_items()) == 200
    assert sync_sleeps == [3]


async def test_async_executor_waits_the_retry_after_of_the_response(
    async_sleeps: list[float],
) -> None:
    session = AsyncFakeSession(
        [503, 200], headers=Headers.from_mapping({"Retry-After": "2"})
    )
    executor = AsyncHttpIO(session, retry=NO_JITTER)
    assert await executor.communicate(BASE_URL, DEFAULT_HEADERS, get_items()) == 200
    assert async_sleeps == [2]


def test_a_retry_after_beyond_the_max_delay_is_not_retried(
    sync_sleeps: list[float],
) -> None:
    session = FakeSession(
        [429, 200], headers=Headers.from_mapping({"Retry-After": "31"})
    )
    executor = SyncHttpIO(session, retry=NO_JITTER)
    assert executor.communicate(BASE_URL, DEFAULT_HEADERS, get_items()) == 429
    assert sync_sleeps == []
    assert len(session.requests) == 1


def test_a_post_is_not_retried_by_default(sync_sleeps: list[float]) -> None:
    session = FakeSession([503, 200])
    executor = SyncHttpIO(session, retry=NO_JITTER)
    assert executor.communicate(BASE_URL, DEFAULT_HEADERS, create_item()) == 503
    assert sync_sleeps == []
    assert retry_counts(session) == [None]


def test_a_post_sent_with_retry_true_is_retried(sync_sleeps: list[float]) -> None:
    session = FakeSession([503, 200])
    executor = SyncHttpIO(session, retry=NO_JITTER)
    assert executor.communicate(BASE_URL, DEFAULT_HEADERS, create_item(True)) == 200
    assert sync_sleeps == [0.5]
    assert session.requests[1].content == session.requests[0].content


async def test_a_post_the_policy_lists_is_retried(async_sleeps: list[float]) -> None:
    session = AsyncFakeSession([SupabaseTransportError, 201])
    policy = RetryPolicy(retryable_methods={"GET", "HEAD", "POST"}, jitter=0)
    executor = AsyncHttpIO(session, retry=policy)
    assert await executor.communicate(BASE_URL, DEFAULT_HEADERS, create_item()) == 201
    assert async_sleeps == [0.5]


def test_a_get_sent_with_retry_false_is_not_retried(sync_sleeps: list[float]) -> None:
    session = FakeSession([503, 200])
    executor = SyncHttpIO(session, retry=NO_JITTER)
    assert executor.communicate(BASE_URL, DEFAULT_HEADERS, get_items(False)) == 503
    assert sync_sleeps == []


async def test_a_get_sent_with_retry_false_raises_its_network_error() -> None:
    session = AsyncFakeSession([SupabaseTransportError, 200])
    executor = AsyncHttpIO(session, retry=NO_JITTER)
    with pytest.raises(SupabaseTransportError):
        await executor.communicate(BASE_URL, DEFAULT_HEADERS, get_items(False))
    assert len(session.requests) == 1


def test_the_policy_of_the_request_replaces_the_one_of_the_executor(
    sync_sleeps: list[float],
) -> None:
    session = FakeSession([503, 503, 503])
    executor = SyncHttpIO(session, retry=NO_JITTER)
    own = RetryPolicy(max_retries=1, base_delay=4, jitter=0)
    assert executor.communicate(BASE_URL, DEFAULT_HEADERS, get_items(own)) == 503
    assert sync_sleeps == [4]
    assert len(session.requests) == 2


def test_a_post_with_its_own_policy_is_retried(sync_sleeps: list[float]) -> None:
    session = FakeSession([503, 201])
    executor = SyncHttpIO(session, retry=NO_JITTER)
    own = RetryPolicy(max_retries=1, base_delay=2, jitter=0)
    assert executor.communicate(BASE_URL, DEFAULT_HEADERS, create_item(own)) == 201
    assert sync_sleeps == [2]


def test_a_disabled_policy_sends_every_request_once(sync_sleeps: list[float]) -> None:
    session = FakeSession([503, 200])
    executor = SyncHttpIO(session, retry=RetryPolicy(max_retries=0))
    assert executor.communicate(BASE_URL, DEFAULT_HEADERS, get_items()) == 503
    assert sync_sleeps == []
    assert len(session.requests) == 1


def test_the_request_delay_is_waited_once_before_the_first_attempt(
    sync_sleeps: list[float],
) -> None:
    def delayed_get() -> HttpMethod[int]:
        response = yield EmptyRequest(path=["items"], method="GET", delay=0.3)
        return response.status

    session = FakeSession([503, 200])
    executor = SyncHttpIO(session, retry=NO_JITTER)
    assert executor.communicate(BASE_URL, DEFAULT_HEADERS, delayed_get()) == 200
    assert sync_sleeps == [0.3, 0.5]


def test_retries_keep_the_timeout_of_the_request(sync_sleeps: list[float]) -> None:
    session = FakeSession([503, 200])
    executor = SyncHttpIO(session, request_timeout=7, retry=NO_JITTER)
    executor.communicate(BASE_URL, DEFAULT_HEADERS, get_items())
    assert [r.timeout for r in session.requests] == [7, 7]


def test_the_generator_only_sees_the_final_response(sync_sleeps: list[float]) -> None:
    session = FakeSession([503, 503, 200])
    executor = SyncHttpIO(session, retry=NO_JITTER)
    assert executor.communicate(BASE_URL, DEFAULT_HEADERS, retry_until_success(5)) == [
        200
    ]
