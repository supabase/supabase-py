from types import SimpleNamespace

import pytest
from httpx import Client, MockTransport, ReadTimeout, Request, Response
from supabase_utils.http import io
from supabase_utils.http.adapters.httpx import HttpxSession
from supabase_utils.http.errors import RequestTimeoutError

from postgrest import SyncPostgrestClient


def recording_client(
    seen: list[Request], request_timeout: float | None = None
) -> SyncPostgrestClient:
    def handler(request: Request) -> Response:
        seen.append(request)
        return Response(200, json=[])

    return SyncPostgrestClient(
        "https://example.com",
        http_session=HttpxSession(client=Client(transport=MockTransport(handler))),
        request_timeout=request_timeout,
    )


def read_timeouts(seen: list[Request]) -> list[float | None]:
    return [request.extensions["timeout"]["read"] for request in seen]


def test_queries_use_client_request_timeout() -> None:
    seen: list[Request] = []
    client = recording_client(seen, request_timeout=12)
    client.from_("users").select("*").execute()
    client.rpc("hello", {}).execute()
    client.schema("private").from_("users").select("*").execute()
    assert read_timeouts(seen) == [12, 12, 12]


def test_query_request_timeout_overrides_client() -> None:
    seen: list[Request] = []
    client = recording_client(seen, request_timeout=12)
    client.from_("users").select("*").request_timeout(3).execute()
    client.rpc("hello", {}).request_timeout(4).execute()
    assert read_timeouts(seen) == [3, 4]


def test_without_request_timeout_the_http_client_decides() -> None:
    seen: list[Request] = []
    recording_client(seen).from_("users").select("*").execute()
    assert read_timeouts(seen) == [5]


def test_retries_keep_request_timeout(monkeypatch: pytest.MonkeyPatch) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr(io, "time", SimpleNamespace(sleep=sleeps.append))
    seen: list[Request] = []

    def handler(request: Request) -> Response:
        seen.append(request)
        return Response(503 if len(seen) == 1 else 200, json=[])

    client = SyncPostgrestClient(
        "https://example.com",
        http_session=HttpxSession(client=Client(transport=MockTransport(handler))),
    )
    client.from_("users").select("*").request_timeout(3).execute()
    assert read_timeouts(seen) == [3, 3]


def test_timeout_raises_request_timeout_error() -> None:
    def handler(request: Request) -> Response:
        raise ReadTimeout("timed out", request=request)

    client = SyncPostgrestClient(
        "https://example.com",
        http_session=HttpxSession(client=Client(transport=MockTransport(handler))),
        request_timeout=1,
    )
    with pytest.raises(RequestTimeoutError):
        client.from_("users").select("*").execute()


@pytest.mark.parametrize("timeout", [0, -2])
def test_invalid_request_timeout_is_rejected(timeout: float) -> None:
    with pytest.raises(ValueError, match="positive number of seconds"):
        recording_client([], request_timeout=timeout)
    with pytest.raises(ValueError, match="positive number of seconds"):
        recording_client([]).from_("users").select("*").request_timeout(timeout)
