import inspect
import re
from types import SimpleNamespace, TracebackType
from typing import Self, override

import pytest
from supabase_utils.http import io
from supabase_utils.http.headers import Headers
from supabase_utils.http.io import AsyncHttpSession, HttpSession
from supabase_utils.http.request import JSONRequest, Request, Response
from supabase_utils.http.retry import RetryPolicy
from supabase_utils.types import JSON
from yarl import URL

from supabase_functions import (
    AsyncFunctionsClient,
    FunctionsHttpError,
    SyncFunctionsClient,
    create_client,
)

from ._async.test_function_client import MockHttpClient as AsyncMockHttpClient
from ._sync.test_function_client import MockHttpClient as SyncMockHttpClient


@pytest.fixture
def valid_url() -> str:
    return "https://example.com"


@pytest.fixture
def valid_headers() -> dict[str, str]:
    return {"Authorization": "Bearer test_token", "Content-Type": "application/json"}


_X_CLIENT_INFO_PATTERN = re.compile(
    r"^supabase-py/supabase_functions v\S+; platform=.+; platform-version=.+; runtime=python; runtime-version=\S+$"
)


def test_async_x_client_info_structured_format(
    valid_url: str, valid_headers: dict[str, str]
) -> None:
    client = AsyncFunctionsClient(
        url=valid_url,
        headers=valid_headers,
        http_session=AsyncMockHttpClient(b"", 200),
    )
    x_client_info = client.default_headers.get("X-Client-Info")
    assert x_client_info is not None
    assert _X_CLIENT_INFO_PATTERN.match(x_client_info), (
        f"X-Client-Info format is wrong: {x_client_info}"
    )


def test_sync_x_client_info_structured_format(
    valid_url: str, valid_headers: dict[str, str]
) -> None:
    client = SyncFunctionsClient(
        url=valid_url,
        headers=valid_headers,
        http_session=SyncMockHttpClient(b"", 200),
    )
    x_client_info = client.default_headers.get("X-Client-Info")
    assert x_client_info is not None
    assert _X_CLIENT_INFO_PATTERN.match(x_client_info), (
        f"X-Client-Info format is wrong: {x_client_info}"
    )


def test_create_async_client(valid_url: str, valid_headers: dict[str, str]) -> None:
    client = create_client(
        url=valid_url,
        headers=valid_headers,
        http_session=AsyncMockHttpClient(b"", 200),
        is_async=True,
    )

    assert isinstance(client, AsyncFunctionsClient)
    assert str(client.base_url) == valid_url
    assert all(
        client.default_headers[key] == value for key, value in valid_headers.items()
    )


def test_create_sync_client(valid_url: str, valid_headers: dict[str, str]) -> None:
    client = create_client(
        url=valid_url,
        headers=valid_headers,
        http_session=SyncMockHttpClient(b"", 200),
        is_async=False,
    )

    assert isinstance(client, SyncFunctionsClient)
    assert str(client.base_url) == valid_url
    assert all(
        client.default_headers[key] == value for key, value in valid_headers.items()
    )


def test_type_hints() -> None:
    from typing import get_type_hints

    hints = get_type_hints(create_client)

    assert hints["url"] is str
    assert hints["headers"] == dict[str, str]
    assert hints["http_session"] == AsyncHttpSession | HttpSession
    assert hints["is_async"] is bool
    assert hints["return"] == AsyncFunctionsClient | SyncFunctionsClient


def test_json_request_body_type_wins_over_client_default_content_type() -> None:
    request = JSONRequest(path=["x"], method="POST", body={"a": 1}).finalize(
        URL("https://example.com"), Headers.from_mapping({"Content-Type": "text/plain"})
    )
    assert request.headers.get_list("Content-Type") == ["application/json"]


def test_json_request_keeps_request_content_type() -> None:
    request = JSONRequest(
        path=["x"],
        method="POST",
        body={"a": 1},
        headers=Headers.from_mapping({"Content-Type": "application/merge-patch+json"}),
    ).finalize(URL("https://example.com"), Headers.empty())
    assert request.headers.get_list("Content-Type") == ["application/merge-patch+json"]


@pytest.mark.parametrize("is_async", [False, True])
def test_invoke_keeps_wrapped_method_metadata(
    is_async: bool,
    valid_url: str,
    valid_headers: dict[str, str],
) -> None:
    client = (
        AsyncFunctionsClient(
            url=valid_url,
            headers=valid_headers,
            http_session=AsyncMockHttpClient(b"", 200),
        )
        if is_async
        else SyncFunctionsClient(
            url=valid_url,
            headers=valid_headers,
            http_session=SyncMockHttpClient(b"", 200),
        )
    )
    invoke = client.invoke

    assert invoke.__name__ == "invoke"
    assert invoke.__doc__ is not None
    assert invoke.__doc__.startswith("Invokes a function")
    assert inspect.unwrap(invoke) is not invoke
    assert list(inspect.signature(invoke).parameters) == [
        "function_name",
        "body",
        "region",
        "headers",
        "method",
        "request_timeout",
        "retry",
    ]


class RecordingSession:
    def __init__(self) -> None:
        self.requests: list[Request] = []

    def send(self, request: Request) -> Response:
        self.requests.append(request)
        return Response(
            headers=Headers.empty(), content=b"", status=200, request=request
        )

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        pass


@pytest.mark.parametrize("body", [None, "text", b"bytes", {"json": True}])
def test_invoke_uses_client_request_timeout(
    body: str | bytes | dict[str, JSON] | None, valid_url: str
) -> None:
    session = RecordingSession()
    client = create_client(
        url=valid_url,
        headers={},
        http_session=session,
        is_async=False,
        request_timeout=30,
    )
    client.invoke("hello", body=body)
    client.invoke("hello", body=body, request_timeout=90)
    assert [request.timeout for request in session.requests] == [30, 90]


def test_invoke_without_request_timeout_leaves_it_to_the_http_client(
    valid_url: str,
) -> None:
    session = RecordingSession()
    SyncFunctionsClient(url=valid_url, headers={}, http_session=session).invoke("hello")
    assert session.requests[0].timeout is None


def test_invalid_request_timeout_is_rejected(valid_url: str) -> None:
    with pytest.raises(ValueError, match="positive number of seconds"):
        SyncFunctionsClient(
            url=valid_url,
            headers={},
            http_session=RecordingSession(),
            request_timeout=0,
        )


class FlakySession(RecordingSession):
    def __init__(self, failures: int) -> None:
        super().__init__()
        self.failures = failures

    @override
    def send(self, request: Request) -> Response:
        response = super().send(request)
        if len(self.requests) <= self.failures:
            return Response(
                headers=Headers.empty(), content=b"", status=503, request=request
            )
        return response


@pytest.fixture
def sleeps(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    sleeps: list[float] = []
    monkeypatch.setattr(io, "time", SimpleNamespace(sleep=sleeps.append))
    return sleeps


def test_clients_pass_the_retry_policy_to_their_executor(valid_url: str) -> None:
    policy = RetryPolicy(max_retries=1)
    sync_client = SyncFunctionsClient(
        url=valid_url, headers={}, http_session=RecordingSession(), retry=policy
    )
    async_client = AsyncFunctionsClient(
        url=valid_url,
        headers={},
        http_session=AsyncMockHttpClient(b"", 200),
        retry=policy,
    )
    created = create_client(
        url=valid_url,
        headers={},
        http_session=RecordingSession(),
        is_async=False,
        retry=policy,
    )
    assert sync_client.executor.retry_policy is policy
    assert async_client.executor.retry_policy is policy
    assert created.executor.retry_policy is policy
    assert (
        SyncFunctionsClient(
            url=valid_url, headers={}, http_session=RecordingSession()
        ).executor.retry_policy
        == RetryPolicy()
    )


def test_post_invocation_is_not_retried_by_default(
    valid_url: str, sleeps: list[float]
) -> None:
    session = FlakySession(failures=1)
    client = SyncFunctionsClient(
        url=valid_url, headers={}, http_session=session, retry=RetryPolicy(jitter=0)
    )
    with pytest.raises(FunctionsHttpError):
        client.invoke("hello")
    assert len(session.requests) == 1
    assert sleeps == []


def test_get_invocation_is_retried(valid_url: str, sleeps: list[float]) -> None:
    session = FlakySession(failures=2)
    client = SyncFunctionsClient(
        url=valid_url, headers={}, http_session=session, retry=RetryPolicy(jitter=0)
    )
    response = client.invoke("hello", method="GET")
    assert response.status == 200
    assert [r.headers.get("X-Retry-Count") for r in session.requests] == [
        None,
        "1",
        "2",
    ]
    assert sleeps == [0.5, 1]


def test_invocation_opted_in_with_retry_true_is_retried(
    valid_url: str, sleeps: list[float]
) -> None:
    session = FlakySession(failures=1)
    client = SyncFunctionsClient(
        url=valid_url, headers={}, http_session=session, retry=RetryPolicy(jitter=0)
    )
    client.invoke("hello", body={"n": 1}, retry=True)
    assert [r.method for r in session.requests] == ["POST", "POST"]
    assert session.requests[1].content == session.requests[0].content
    assert sleeps == [0.5]


def test_invocation_with_retry_false_is_not_retried(
    valid_url: str, sleeps: list[float]
) -> None:
    session = FlakySession(failures=1)
    client = SyncFunctionsClient(url=valid_url, headers={}, http_session=session)
    with pytest.raises(FunctionsHttpError):
        client.invoke("hello", method="GET", retry=False)
    assert len(session.requests) == 1
    assert sleeps == []


def test_invocation_retry_policy_replaces_the_one_of_the_client(
    valid_url: str, sleeps: list[float]
) -> None:
    session = FlakySession(failures=3)
    client = SyncFunctionsClient(
        url=valid_url, headers={}, http_session=session, retry=RetryPolicy(jitter=0)
    )
    own = RetryPolicy(max_retries=1, base_delay=3, jitter=0)
    with pytest.raises(FunctionsHttpError):
        client.invoke("hello", method="GET", retry=own)
    assert len(session.requests) == 2
    assert sleeps == [3]
