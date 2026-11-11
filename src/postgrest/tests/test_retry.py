from types import SimpleNamespace

import pytest
from httpx import AsyncClient, Client, ConnectError, MockTransport, Request, Response
from supabase_utils.http import io
from supabase_utils.http.adapters.httpx import AsyncHttpxSession, HttpxSession
from supabase_utils.http.errors import SupabaseTransportError
from supabase_utils.http.retry import RetryPolicy

from postgrest import APIError, AsyncPostgrestClient, SyncPostgrestClient

NO_JITTER = RetryPolicy(jitter=0)


def flaky_transport(
    seen: list[Request], failures: int, status: int = 503, **headers: str
) -> MockTransport:
    def handler(request: Request) -> Response:
        seen.append(request)
        if len(seen) <= failures:
            return Response(status, json={"message": "unavailable"}, headers=headers)
        return Response(200, json=[])

    return MockTransport(handler)


def sync_client(
    transport: MockTransport, retry: RetryPolicy | None = None
) -> SyncPostgrestClient:
    return SyncPostgrestClient(
        "https://example.com",
        http_session=HttpxSession(client=Client(transport=transport)),
        retry=retry,
    )


@pytest.fixture
def sleeps(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    sleeps: list[float] = []
    monkeypatch.setattr(io, "time", SimpleNamespace(sleep=sleeps.append))
    return sleeps


def retry_counts(seen: list[Request]) -> list[str | None]:
    return [request.headers.get("X-Retry-Count") for request in seen]


def test_select_is_retried_with_the_policy_of_the_client(sleeps: list[float]) -> None:
    seen: list[Request] = []
    client = sync_client(flaky_transport(seen, 2), retry=NO_JITTER)
    client.from_("users").select("*").execute()
    assert retry_counts(seen) == [None, "1", "2"]
    assert sleeps == [0.5, 1]


def test_select_is_retried_on_a_rate_limit_after_retry_after(
    sleeps: list[float],
) -> None:
    seen: list[Request] = []
    transport = flaky_transport(seen, 1, status=429, **{"Retry-After": "4"})
    sync_client(transport, retry=NO_JITTER).from_("users").select("*").execute()
    assert len(seen) == 2
    assert sleeps == [4]


def test_select_is_retried_on_a_network_error(sleeps: list[float]) -> None:
    seen: list[Request] = []

    def handler(request: Request) -> Response:
        seen.append(request)
        if len(seen) == 1:
            raise ConnectError("refused", request=request)
        return Response(200, json=[])

    client = sync_client(MockTransport(handler), retry=NO_JITTER)
    client.from_("users").select("*").execute()
    assert retry_counts(seen) == [None, "1"]
    assert sleeps == [0.5]


def test_insert_is_not_retried(sleeps: list[float]) -> None:
    seen: list[Request] = []
    client = sync_client(flaky_transport(seen, 1), retry=NO_JITTER)
    with pytest.raises(APIError):
        client.from_("users").insert({"name": "x"}).execute()
    assert len(seen) == 1
    assert sleeps == []


def test_insert_opted_in_with_retry_true_is_retried(sleeps: list[float]) -> None:
    seen: list[Request] = []
    client = sync_client(flaky_transport(seen, 1), retry=NO_JITTER)
    client.from_("users").insert({"name": "x"}).retry(True).execute()
    assert retry_counts(seen) == [None, "1"]
    assert seen[1].content == seen[0].content
    assert sleeps == [0.5]


def test_rpc_post_is_not_retried_on_a_network_error() -> None:
    seen: list[Request] = []

    def handler(request: Request) -> Response:
        seen.append(request)
        raise ConnectError("refused", request=request)

    with pytest.raises(SupabaseTransportError):
        sync_client(MockTransport(handler)).rpc("fn", {}).execute()
    assert len(seen) == 1


def test_query_retry_policy_replaces_the_one_of_the_client(
    sleeps: list[float],
) -> None:
    seen: list[Request] = []
    client = sync_client(flaky_transport(seen, 5), retry=NO_JITTER)
    query = client.from_("users").select("*")
    own = RetryPolicy(max_retries=1, base_delay=2, jitter=0)
    with pytest.raises(APIError):
        query.retry(own).execute()
    assert retry_counts(seen) == [None, "1"]
    assert sleeps == [2]


def test_a_disabled_client_policy_sends_every_query_once(sleeps: list[float]) -> None:
    seen: list[Request] = []
    client = sync_client(flaky_transport(seen, 2), retry=RetryPolicy(max_retries=0))
    with pytest.raises(APIError):
        client.from_("users").select("*").execute()
    with pytest.raises(APIError):
        client.from_("users").select("*").retry(True).execute()
    assert len(seen) == 2
    assert sleeps == []


def test_schema_keeps_the_retry_policy() -> None:
    policy = RetryPolicy(max_retries=7)
    client = sync_client(flaky_transport([], 0), retry=policy)
    assert client.schema("private").executor.retry_policy is policy


async def test_async_client_takes_a_retry_policy(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sleeps: list[float] = []

    async def fake_sleep(delay: float) -> None:
        sleeps.append(delay)

    monkeypatch.setattr(io, "asyncio", SimpleNamespace(sleep=fake_sleep))
    seen: list[Request] = []
    async with AsyncClient(transport=flaky_transport(seen, 1)) as http_client:
        client = AsyncPostgrestClient(
            "https://example.com",
            http_session=AsyncHttpxSession(client=http_client),
            retry=RetryPolicy(base_delay=0.1, jitter=0),
        )
        assert client.schema("private").executor.retry_policy is (
            client.executor.retry_policy
        )
        await client.from_("users").select("*").execute()
    assert retry_counts(seen) == [None, "1"]
    assert sleeps == [0.1]
