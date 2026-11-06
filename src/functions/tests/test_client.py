import inspect
import re
from types import TracebackType
from typing import Self

import pytest
from supabase_utils.http.headers import Headers
from supabase_utils.http.io import AsyncHttpSession, HttpSession
from supabase_utils.http.request import JSONRequest, Request, Response
from supabase_utils.types import JSON
from yarl import URL

from supabase_functions import AsyncFunctionsClient, SyncFunctionsClient, create_client

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
