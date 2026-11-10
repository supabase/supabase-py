from dataclasses import FrozenInstanceError
from types import SimpleNamespace

import pytest
from httpx import AsyncClient, Client, MockTransport, Request, Response
from supabase_utils.http import io
from supabase_utils.http.adapters.httpx import AsyncHttpxSession, HttpxSession

from postgrest import AsyncPostgrestClient, SyncPostgrestClient

OBJECT_ACCEPT = "application/vnd.pgrst.object+json"


def transport_for(seen: list[Request], *, fail_first: bool = False) -> MockTransport:
    def handler(request: Request) -> Response:
        seen.append(request)
        if fail_first and len(seen) == 1:
            return Response(503, json=[])
        return Response(200, json=[])

    return MockTransport(handler)


def recording_client(
    seen: list[Request], *, fail_first: bool = False
) -> SyncPostgrestClient:
    http_client = Client(transport=transport_for(seen, fail_first=fail_first))
    return SyncPostgrestClient(
        "https://example.com", http_session=HttpxSession(client=http_client)
    )


def query_parameters(request: Request) -> list[tuple[str, str]]:
    return sorted(request.url.params.multi_items())


def test_queries_branched_from_one_base_send_only_their_own_filters() -> None:
    seen: list[Request] = []
    with recording_client(seen) as client:
        base = client.table("items").select("*").eq("account_id", "abc")

        base.in_("id", ["1", "2", "3"]).execute()
        base.in_("id", ["4", "5", "6"]).execute()

    assert [query_parameters(request) for request in seen] == [
        [("account_id", "eq.abc"), ("id", "in.(1,2,3)"), ("select", "*")],
        [("account_id", "eq.abc"), ("id", "in.(4,5,6)"), ("select", "*")],
    ]


async def test_async_queries_branched_from_one_base_send_only_their_own_filters() -> (
    None
):
    seen: list[Request] = []
    async with AsyncClient(transport=transport_for(seen)) as http_client:
        client = AsyncPostgrestClient(
            "https://example.com", http_session=AsyncHttpxSession(client=http_client)
        )
        base = client.table("items").select("*").eq("account_id", "abc")

        await base.in_("id", ["1", "2", "3"]).execute()
        await base.in_("id", ["4", "5", "6"]).execute()

    assert [query_parameters(request) for request in seen] == [
        [("account_id", "eq.abc"), ("id", "in.(1,2,3)"), ("select", "*")],
        [("account_id", "eq.abc"), ("id", "in.(4,5,6)"), ("select", "*")],
    ]


def test_range_in_a_loop_sends_one_offset_and_limit_pair_per_request() -> None:
    seen: list[Request] = []
    with recording_client(seen) as client:
        base = client.table("items").select("*").order("id")

        for page in range(3):
            base.range(page * 10, page * 10 + 9).execute()

    assert [query_parameters(request) for request in seen] == [
        [("limit", "10"), ("offset", "0"), ("order", "id.asc"), ("select", "*")],
        [("limit", "10"), ("offset", "10"), ("order", "id.asc"), ("select", "*")],
        [("limit", "10"), ("offset", "20"), ("order", "id.asc"), ("select", "*")],
    ]


def test_not_leaves_the_query_unchanged() -> None:
    seen: list[Request] = []
    with recording_client(seen) as client:
        query = client.table("items").select("*")
        negated = query.not_

        query.eq("done", True).execute()
        negated.eq("done", True).execute()
        query.execute()

    assert [query_parameters(request) for request in seen] == [
        [("done", "eq.true"), ("select", "*")],
        [("done", "not.eq.true"), ("select", "*")],
        [("select", "*")],
    ]


def test_single_leaves_the_accept_header_unchanged() -> None:
    seen: list[Request] = []
    with recording_client(seen) as client:
        query = client.table("items").select("*")
        single = query.single()

        assert query.execute().data == []

    assert "accept" not in query.request.headers
    assert single.request.headers.get("accept") == OBJECT_ACCEPT
    assert seen[0].headers.get("accept") != OBJECT_ACCEPT


def test_executing_one_builder_twice_sends_identical_requests(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sleeps: list[float] = []
    monkeypatch.setattr(io, "time", SimpleNamespace(sleep=sleeps.append))
    seen: list[Request] = []
    with recording_client(seen, fail_first=True) as client:
        query = client.table("items").select("*").eq("id", 1).request_timeout(3)

        query.execute()
        query.execute()

    first_attempt, retried_attempt, second_execution = seen
    assert retried_attempt.headers.get("x-retry-count") == "1"
    assert "x-retry-count" not in first_attempt.headers
    assert second_execution.method == first_attempt.method
    assert second_execution.url == first_attempt.url
    assert dict(second_execution.headers) == dict(first_attempt.headers)
    assert "x-retry-count" not in query.request.headers
    assert query.request.delay is None
    assert sleeps == [1]


@pytest.mark.parametrize(
    ("method", "accept"),
    [
        ("csv", "text/csv"),
        ("explain", "application/vnd.pgrst.plan+text; options="),
        ("single", OBJECT_ACCEPT),
    ],
)
def test_result_shaping_methods_leave_the_receiver_unchanged(
    method: str, accept: str
) -> None:
    with recording_client([]) as client:
        query = client.table("items").select("*")

        shaped = getattr(query, method)()

    assert shaped.request.headers.get("accept") == accept
    assert "accept" not in query.request.headers


def test_strip_nulls_leaves_the_receiver_unchanged() -> None:
    with recording_client([]) as client:
        query = client.table("items").select("*")

    assert query.strip_nulls().request.strip_nulls is True
    assert query.request.strip_nulls is False


def test_retry_and_request_timeout_return_copies() -> None:
    with recording_client([]) as client:
        query = client.table("items").select("*")

    assert query.request_timeout(3).request.timeout == 3
    assert query.retry(False).request.retry is False
    assert query.request.timeout is None
    assert query.request.retry is True


def test_mutation_builders_return_copies() -> None:
    with recording_client([]) as client:
        insert = client.table("items").insert({"name": "x"})
        update = client.table("items").update({"name": "x"})

    assert insert.select("id").request.query.get("select") == "id"
    assert update.max_affected(1).request.headers.get_list("prefer") == [
        "return=representation",
        "handling=strict",
        "max-affected=1",
    ]
    assert "select" not in insert.request.query
    assert update.request.headers.get_list("prefer") == ["return=representation"]


def test_rpc_builders_return_copies() -> None:
    with recording_client([]) as client:
        rpc = client.rpc("hello", {})

    assert rpc.select("id").request.query.get("select") == "id"
    assert rpc.csv().request.headers.get("accept") == "text/csv"
    assert rpc.single().request.headers.get("accept") == OBJECT_ACCEPT
    assert rpc.limit(1).request.query.get("limit") == "1"
    assert "select" not in rpc.request.query
    assert "limit" not in rpc.request.query
    assert "accept" not in rpc.request.headers
    assert "prefer" not in rpc.request.headers


def test_builders_reject_assignment() -> None:
    with recording_client([]) as client:
        query = client.table("items").select("*")

    with pytest.raises(FrozenInstanceError):
        query.request = query.single().request  # pyrefly: ignore[read-only]
    with pytest.raises(FrozenInstanceError):
        query.request.timeout = 3  # pyrefly: ignore[read-only]
