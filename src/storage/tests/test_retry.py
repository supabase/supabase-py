from types import SimpleNamespace

import pytest
from httpx import AsyncClient, Client, MockTransport, Request, Response
from supabase_utils.http import io
from supabase_utils.http.adapters.httpx import AsyncHttpxSession, HttpxSession
from supabase_utils.http.retry import RetryPolicy

from storage3 import AsyncStorageClient, StorageApiError, SyncStorageClient

from .utils import STORAGE_URL

NO_JITTER = RetryPolicy(jitter=0)


def flaky_transport(seen: list[Request], failures: int) -> MockTransport:
    def handler(request: Request) -> Response:
        seen.append(request)
        if len(seen) <= failures:
            return Response(
                503, json={"statusCode": "503", "error": "x", "message": "down"}
            )
        if request.method == "GET":
            return Response(200, content=b"file")
        return Response(200, json={"Key": "photos/a.png", "Id": "1"})

    return MockTransport(handler)


def sync_client(
    transport: MockTransport, retry: RetryPolicy | None = None
) -> SyncStorageClient:
    return SyncStorageClient(
        STORAGE_URL,
        {},
        http_session=HttpxSession(Client(transport=transport)),
        retry=retry,
    )


@pytest.fixture
def sleeps(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    sleeps: list[float] = []
    monkeypatch.setattr(io, "time", SimpleNamespace(sleep=sleeps.append))
    return sleeps


def test_download_is_retried(sleeps: list[float]) -> None:
    seen: list[Request] = []
    client = sync_client(flaky_transport(seen, 2), retry=NO_JITTER)
    assert client.from_("photos").download("a.png") == b"file"
    assert [r.headers.get("X-Retry-Count") for r in seen] == [None, "1", "2"]
    assert sleeps == [0.5, 1]


def test_upload_is_not_retried_by_default(sleeps: list[float]) -> None:
    seen: list[Request] = []
    client = sync_client(flaky_transport(seen, 1), retry=NO_JITTER)
    with pytest.raises(StorageApiError):
        client.from_("photos").upload("a.png", b"bytes")
    assert len(seen) == 1
    assert sleeps == []


def test_upload_is_retried_when_the_policy_lists_its_method(
    sleeps: list[float],
) -> None:
    seen: list[Request] = []
    policy = RetryPolicy(retryable_methods={"GET", "HEAD", "POST", "PUT"}, jitter=0)
    client = sync_client(flaky_transport(seen, 1), retry=policy)
    client.from_("photos").upload("a.png", b"bytes")
    assert [r.method for r in seen] == ["POST", "POST"]
    assert seen[1].content == seen[0].content
    assert sleeps == [0.5]


def test_a_disabled_policy_sends_every_request_once(sleeps: list[float]) -> None:
    seen: list[Request] = []
    client = sync_client(flaky_transport(seen, 1), retry=RetryPolicy(max_retries=0))
    with pytest.raises(StorageApiError):
        client.from_("photos").download("a.png")
    assert len(seen) == 1
    assert sleeps == []


async def test_async_client_takes_a_retry_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sleeps: list[float] = []

    async def fake_sleep(delay: float) -> None:
        sleeps.append(delay)

    monkeypatch.setattr(io, "asyncio", SimpleNamespace(sleep=fake_sleep))
    seen: list[Request] = []
    policy = RetryPolicy(max_retries=1, base_delay=0.1, jitter=0)
    async with AsyncClient(transport=flaky_transport(seen, 1)) as http_client:
        client = AsyncStorageClient(
            STORAGE_URL,
            {},
            http_session=AsyncHttpxSession(http_client),
            retry=policy,
        )
        assert client.executor.retry_policy is policy
        assert await client.from_("photos").download("a.png") == b"file"
    assert len(seen) == 2
    assert sleeps == [0.1]
