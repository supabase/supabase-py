from collections.abc import Callable

import pytest
from httpx import AsyncClient, Client, MockTransport, Request, Response
from supabase_utils.http.adapters.httpx import AsyncHttpxSession, HttpxSession
from supabase_utils.http.io import SyncHttpIO

from postgrest import AsyncPostgrestClient, SyncPostgrestClient
from postgrest.request_builder import MutationRequestBuilder, RequestBuilder

type Mutation = MutationRequestBuilder[SyncHttpIO]
type Write = Callable[[RequestBuilder[SyncHttpIO]], Mutation]
type Scope = Callable[[Mutation], Mutation]
type Finish = Callable[[Mutation], object]
type QueryParameters = list[tuple[str, str]]


def transport_for(seen: list[Request]) -> MockTransport:
    def handler(request: Request) -> Response:
        seen.append(request)
        return Response(200, json=[])

    return MockTransport(handler)


def recording_client(seen: list[Request]) -> SyncPostgrestClient:
    http_client = Client(transport=transport_for(seen))
    return SyncPostgrestClient(
        "https://example.com", http_session=HttpxSession(client=http_client)
    )


def query_parameters(request: Request) -> QueryParameters:
    return sorted(request.url.params.multi_items())


WRITES: dict[str, tuple[Write, str]] = {
    "update": (lambda table: table.update({"name": "x"}), "PATCH"),
    "delete": (lambda table: table.delete(), "DELETE"),
}

FINISHES: dict[str, Finish] = {
    "execute": lambda query: query.execute(),
    "select": lambda query: query.select("id").execute(),
    "single": lambda query: query.single().execute(),
    "maybe_single": lambda query: query.maybe_single().execute(),
    "csv": lambda query: query.csv().execute(),
    "explain": lambda query: query.explain().execute(),
    "limit": lambda query: query.order("id").limit(1).execute(),
    "max_affected": lambda query: query.max_affected(1).execute(),
    "request_timeout": lambda query: query.request_timeout(3).execute(),
}

SCOPES: dict[str, tuple[Scope, QueryParameters]] = {
    "eq": (lambda query: query.eq("id", 1), [("id", "eq.1")]),
    "not_eq": (lambda query: query.not_.eq("id", 1), [("id", "not.eq.1")]),
    "match": (lambda query: query.match({"id": 1}), [("id", "eq.1")]),
    "in_": (lambda query: query.in_("id", ["1", "2"]), [("id", "in.(1,2)")]),
    "or_": (lambda query: query.or_("id.eq.1,id.eq.2"), [("or", "(id.eq.1,id.eq.2)")]),
    "all": (lambda query: query.all(), []),
    "all_then_eq": (lambda query: query.all().eq("id", 1), [("id", "eq.1")]),
    "eq_then_all": (lambda query: query.eq("id", 1).all(), [("id", "eq.1")]),
}


@pytest.mark.parametrize(("write", "method"), WRITES.values(), ids=WRITES)
@pytest.mark.parametrize("finish", FINISHES.values(), ids=FINISHES)
def test_write_without_filter_raises_before_sending(
    write: Write, method: str, finish: Finish
) -> None:
    seen: list[Request] = []
    operation = "update" if method == "PATCH" else "delete"
    with recording_client(seen) as client:
        query = write(client.table("items"))

        with pytest.raises(ValueError, match=rf"^{operation}\(\) has no filter"):
            finish(query)

    assert seen == []


@pytest.mark.parametrize(("write", "method"), WRITES.values(), ids=WRITES)
@pytest.mark.parametrize(("scope", "expected"), SCOPES.values(), ids=SCOPES)
def test_scoped_write_is_sent(
    write: Write, method: str, scope: Scope, expected: QueryParameters
) -> None:
    seen: list[Request] = []
    with recording_client(seen) as client:
        scope(write(client.table("items"))).execute()

    assert [(request.method, query_parameters(request)) for request in seen] == [
        (method, expected)
    ]


def test_all_leaves_the_receiver_unchanged() -> None:
    with recording_client([]) as client:
        unfiltered = client.table("items").delete()
        every_row = unfiltered.all()

    assert unfiltered.request.requires_filter is True
    assert every_row.request.requires_filter is False
    assert len(every_row.request.query) == 0


def test_reads_inserts_and_rpc_need_no_filter() -> None:
    seen: list[Request] = []
    with recording_client(seen) as client:
        client.table("items").select("*").execute()
        client.table("items").insert({"name": "x"}).execute()
        client.table("items").upsert({"name": "x"}).execute()
        client.rpc("hello", {}).execute()

    assert [request.method for request in seen] == ["GET", "POST", "POST", "POST"]


async def test_async_write_without_filter_raises_before_sending() -> None:
    seen: list[Request] = []
    async with AsyncClient(transport=transport_for(seen)) as http_client:
        client = AsyncPostgrestClient(
            "https://example.com", http_session=AsyncHttpxSession(client=http_client)
        )
        unfiltered = client.table("items").delete()

        with pytest.raises(ValueError, match=r"^delete\(\) has no filter"):
            await unfiltered.execute()
        await unfiltered.eq("id", 1).execute()
        await unfiltered.all().execute()

    assert [(request.method, query_parameters(request)) for request in seen] == [
        ("DELETE", [("id", "eq.1")]),
        ("DELETE", []),
    ]
