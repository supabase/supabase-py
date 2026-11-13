from collections.abc import Callable
from dataclasses import dataclass, field, replace
from types import SimpleNamespace
from typing import Any

import pytest
from httpx import AsyncClient, Client, MockTransport
from httpx import Request as HttpxRequest
from httpx import Response as HttpxResponse
from supabase_utils.http import io
from supabase_utils.http.adapters.httpx import AsyncHttpxSession, HttpxSession
from supabase_utils.http.io import SyncHttpIO
from supabase_utils.http.request import Request
from supabase_utils.http.retry import RetryPolicy

from postgrest import (
    APIError,
    AsyncHttpTableExecutor,
    AsyncPostgrestClient,
    AsyncTableExecutor,
    Column,
    CountMethod,
    ExplainOptions,
    HttpTableExecutor,
    NullableColumn,
    RequestOptions,
    ResultShape,
    ReturnMethod,
    SyncPostgrestClient,
    Table,
    TableExecutor,
    TableOperation,
    TableRequest,
    TableResult,
)
from postgrest.request_builder import BaseRequestClient
from postgrest.table_executor import _render

REST_URL = "https://example.com/rest/v1"
ROW = {"title": "a"}
ROWS = [{"title": "a"}, {"title": "b", "id": 2}]


class BookRow:
    pass


class Books:
    id = Column[BookRow, int]("id")
    title = Column[BookRow, str]("title")
    author_name = Column[BookRow, str]("author.name")
    deleted_at = NullableColumn[BookRow, str]("deleted_at")
    table = Table("books", BookRow, primary_key=(id,))


SEARCH = Table("search_books", BookRow)


def books(operation: TableOperation, **fields: Any) -> TableRequest:
    return TableRequest(table=Books.table, operation=operation, **fields)


def search(**fields: Any) -> TableRequest:
    return TableRequest(table=SEARCH, operation=TableOperation.RPC, **fields)


@dataclass
class Transport:
    """Answers every request with the status, content and headers it is
    given, and keeps what it was sent."""

    status: int = 200
    content: bytes = b"[]"
    headers: dict[str, str] = field(default_factory=dict)
    seen: list[HttpxRequest] = field(default_factory=list)

    def handler(self, request: HttpxRequest) -> HttpxResponse:
        self.seen.append(request)
        return HttpxResponse(self.status, content=self.content, headers=self.headers)

    @property
    def only_request(self) -> HttpxRequest:
        (request,) = self.seen
        return request


def sync_client(
    transport: Transport,
    *,
    headers: dict[str, str] | None = None,
    schema: str = "public",
    retry: RetryPolicy | None = None,
    request_timeout: float | None = None,
) -> SyncPostgrestClient:
    return SyncPostgrestClient(
        REST_URL,
        http_session=HttpxSession(
            client=Client(transport=MockTransport(transport.handler))
        ),
        headers={"apikey": "key", **(headers or {})},
        schema=schema,
        retry=retry,
        request_timeout=request_timeout,
    )


def async_client(transport: Transport) -> AsyncPostgrestClient:
    return AsyncPostgrestClient(
        REST_URL,
        http_session=AsyncHttpxSession(
            client=AsyncClient(transport=MockTransport(transport.handler))
        ),
        headers={"apikey": "key"},
    )


@pytest.fixture
def sleeps(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    sleeps: list[float] = []
    monkeypatch.setattr(io, "time", SimpleNamespace(sleep=sleeps.append))
    return sleeps


@dataclass(frozen=True)
class Wire:
    """A finalized request as it goes on the wire, in a form that compares."""

    method: str
    path: str
    query: list[tuple[str, str]]
    headers: list[tuple[str, str]]
    content: bytes | None
    timeout: float | None
    retry: RetryPolicy | bool | None


def wire(request: Request) -> Wire:
    return Wire(
        method=request.method,
        path=request.url.path,
        query=sorted(request.url.query.items()),
        headers=sorted(request.headers.iter_items()),
        content=request.content,
        timeout=request.timeout,
        retry=request.retry,
    )


def typed(client: SyncPostgrestClient, request: TableRequest) -> Wire:
    """What the typed executor sends for `request` through `client`."""
    return wire(_render(request).finalize(client.base_url, client.default_headers))


def untyped(builder: BaseRequestClient[SyncHttpIO]) -> Wire:
    """What the string builder `builder` sends."""
    return wire(builder.request.finalize(builder.base_url, builder.default_headers))


type StringQuery = Callable[[SyncPostgrestClient], BaseRequestClient[SyncHttpIO]]

SAME_QUERY: dict[str, tuple[TableRequest, StringQuery]] = {
    "select": (
        books(TableOperation.SELECT),
        lambda c: c.from_("books").select("*"),
    ),
    "select columns": (
        books(TableOperation.SELECT, columns=(Books.id, Books.title)),
        lambda c: c.from_("books").select("id", "title"),
    ),
    "select or, order and range": (
        books(
            TableOperation.SELECT,
            filter=Books.id.gt(1) | Books.title.eq("a"),
            orderings=(Books.title.desc().nulls_last(),),
            limit=10,
            offset=10,
        ),
        lambda c: c.from_("books")
        .select("*")
        .or_("id.gt.1,title.eq.a")
        .order("title", desc=True, nullsfirst=False)
        .range(10, 19),
    ),
    "select and with a negation": (
        books(TableOperation.SELECT, filter=Books.id.gt(1) & ~Books.title.eq("a")),
        lambda c: c.from_("books").select("*").gt("id", 1).not_.eq("title", "a"),
    ),
    "select limit": (
        books(TableOperation.SELECT, limit=5),
        lambda c: c.from_("books").select("*").limit(5),
    ),
    "select offset": (
        books(TableOperation.SELECT, offset=5),
        lambda c: c.from_("books").select("*").offset(5),
    ),
    "select count": (
        books(TableOperation.SELECT, count=CountMethod.exact),
        lambda c: c.from_("books").select("*", count=CountMethod.exact),
    ),
    "select head": (
        books(TableOperation.SELECT, shape=ResultShape.HEAD),
        lambda c: c.from_("books").select("*", head=True),
    ),
    "select head count": (
        books(TableOperation.SELECT, shape=ResultShape.HEAD, count=CountMethod.planned),
        lambda c: c.from_("books").select("*", count=CountMethod.planned, head=True),
    ),
    "select single": (
        books(TableOperation.SELECT, shape=ResultShape.SINGLE),
        lambda c: c.from_("books").select("*").single(),
    ),
    "select maybe single": (
        books(TableOperation.SELECT, shape=ResultShape.MAYBE_SINGLE),
        lambda c: c.from_("books").select("*").maybe_single(),
    ),
    "select csv": (
        books(TableOperation.SELECT, shape=ResultShape.CSV),
        lambda c: c.from_("books").select("*").csv(),
    ),
    "select explain": (
        books(TableOperation.SELECT, shape=ResultShape.EXPLAIN),
        lambda c: c.from_("books").select("*").explain(),
    ),
    "select explain with options": (
        books(
            TableOperation.SELECT,
            shape=ResultShape.EXPLAIN,
            explain=ExplainOptions(analyze=True, wal=True, format="json"),
        ),
        lambda c: c.from_("books")
        .select("*")
        .explain(
            analyze=True,
            verbose=False,
            settings=False,
            buffers=False,
            wal=True,
            format="json",
        ),
    ),
    "select strip nulls": (
        books(TableOperation.SELECT, strip_nulls=True),
        lambda c: c.from_("books").select("*").strip_nulls(),
    ),
    "select strip nulls single": (
        books(TableOperation.SELECT, strip_nulls=True, shape=ResultShape.SINGLE),
        lambda c: c.from_("books").select("*").strip_nulls().single(),
    ),
    "select max affected": (
        books(TableOperation.SELECT, max_affected=3),
        lambda c: c.from_("books").select("*").max_affected(3),
    ),
    "select with options": (
        books(TableOperation.SELECT, options=RequestOptions(timeout=3, retry=False)),
        lambda c: c.from_("books").select("*").request_timeout(3).retry(False),
    ),
    "insert": (
        books(TableOperation.INSERT, payload=ROW),
        lambda c: c.from_("books").insert(ROW, returning=ReturnMethod.minimal),
    ),
    "insert rows": (
        books(TableOperation.INSERT, payload=ROWS),
        lambda c: c.from_("books").insert(
            ROWS, returning=ReturnMethod.minimal, default_to_null=False
        ),
    ),
    "insert count": (
        books(TableOperation.INSERT, payload=ROW, count=CountMethod.exact),
        lambda c: c.from_("books").insert(
            ROW, count=CountMethod.exact, returning=ReturnMethod.minimal
        ),
    ),
    "insert returning": (
        books(TableOperation.INSERT, payload=ROW, returning=True),
        lambda c: c.from_("books").insert(ROW).select(),
    ),
    "insert returning columns": (
        books(TableOperation.INSERT, payload=ROW, returning=True, columns=(Books.id,)),
        lambda c: c.from_("books").insert(ROW).select("id"),
    ),
    "insert returning single": (
        books(
            TableOperation.INSERT,
            payload=ROW,
            returning=True,
            shape=ResultShape.SINGLE,
        ),
        lambda c: c.from_("books").insert(ROW).select().single(),
    ),
    "insert returning count": (
        books(
            TableOperation.INSERT, payload=ROW, returning=True, count=CountMethod.exact
        ),
        lambda c: c.from_("books").insert(ROW, count=CountMethod.exact).select(),
    ),
    "upsert": (
        books(TableOperation.UPSERT, payload=ROW),
        lambda c: c.from_("books").upsert(ROW, returning=ReturnMethod.minimal),
    ),
    "upsert on conflict ignoring duplicates": (
        books(
            TableOperation.UPSERT,
            payload=ROW,
            on_conflict=(Books.id, Books.title),
            ignore_duplicates=True,
        ),
        lambda c: c.from_("books").upsert(
            ROW,
            returning=ReturnMethod.minimal,
            ignore_duplicates=True,
            on_conflict="id,title",
        ),
    ),
    "upsert rows returning": (
        books(TableOperation.UPSERT, payload=ROWS, returning=True),
        lambda c: c.from_("books").upsert(ROWS, default_to_null=False).select(),
    ),
    "update": (
        books(TableOperation.UPDATE, payload=ROW, filter=Books.id.eq(1)),
        lambda c: c.from_("books")
        .update(ROW, returning=ReturnMethod.minimal)
        .eq("id", 1),
    ),
    "update every row": (
        books(TableOperation.UPDATE, payload=ROW),
        lambda c: c.from_("books").update(ROW, returning=ReturnMethod.minimal).all(),
    ),
    "update returning": (
        books(
            TableOperation.UPDATE, payload=ROW, filter=Books.id.eq(1), returning=True
        ),
        lambda c: c.from_("books").update(ROW).eq("id", 1).select(),
    ),
    "update max affected": (
        books(
            TableOperation.UPDATE, payload=ROW, filter=Books.id.eq(1), max_affected=1
        ),
        lambda c: c.from_("books")
        .update(ROW, returning=ReturnMethod.minimal)
        .eq("id", 1)
        .max_affected(1),
    ),
    "delete": (
        books(TableOperation.DELETE, filter=Books.id.eq(1)),
        lambda c: c.from_("books").delete(returning=ReturnMethod.minimal).eq("id", 1),
    ),
    "delete returning csv": (
        books(
            TableOperation.DELETE,
            filter=Books.id.eq(1),
            returning=True,
            shape=ResultShape.CSV,
        ),
        lambda c: c.from_("books").delete().eq("id", 1).select().csv(),
    ),
    "count": (
        books(TableOperation.COUNT, filter=Books.id.eq(1)),
        lambda c: c.from_("books")
        .select("*", count=CountMethod.exact, head=True)
        .eq("id", 1),
    ),
    "count estimated": (
        books(TableOperation.COUNT, count=CountMethod.estimated),
        lambda c: c.from_("books").select("*", count=CountMethod.estimated, head=True),
    ),
    "rpc": (
        search(payload={"query": "x"}),
        lambda c: c.rpc("search_books", {"query": "x"}),
    ),
    "rpc without arguments": (
        search(),
        lambda c: c.rpc("search_books", {}),
    ),
    "rpc read only": (
        search(payload={"query": "x", "ids": [1, 2]}, read_only=True),
        lambda c: c.rpc("search_books", {"query": "x", "ids": [1, 2]}, get=True),
    ),
    "rpc head": (
        search(payload={"query": "x"}, shape=ResultShape.HEAD),
        lambda c: c.rpc("search_books", {"query": "x"}, head=True),
    ),
    "rpc head count": (
        search(payload={"query": "x"}, shape=ResultShape.HEAD, count=CountMethod.exact),
        lambda c: c.rpc(
            "search_books", {"query": "x"}, head=True, count=CountMethod.exact
        ),
    ),
    "rpc count": (
        search(payload={"query": "x"}, count=CountMethod.exact),
        lambda c: c.rpc("search_books", {"query": "x"}, count=CountMethod.exact),
    ),
    "rpc filter, order and limit": (
        search(
            payload={"query": "x"},
            filter=Books.id.gt(1),
            orderings=(Books.id.asc(),),
            limit=2,
        ),
        lambda c: c.rpc("search_books", {"query": "x"})
        .gt("id", 1)
        .order("id")
        .limit(2),
    ),
    "rpc columns": (
        search(payload={"query": "x"}, columns=(Books.id,)),
        lambda c: c.rpc("search_books", {"query": "x"}).select("id"),
    ),
    "rpc single": (
        search(payload={"query": "x"}, shape=ResultShape.SINGLE),
        lambda c: c.rpc("search_books", {"query": "x"}).single(),
    ),
    "rpc maybe single": (
        search(payload={"query": "x"}, shape=ResultShape.MAYBE_SINGLE),
        lambda c: c.rpc("search_books", {"query": "x"}).maybe_single(),
    ),
    "rpc csv": (
        search(payload={"query": "x"}, shape=ResultShape.CSV),
        lambda c: c.rpc("search_books", {"query": "x"}).csv(),
    ),
    "rpc strip nulls": (
        search(payload={"query": "x"}, strip_nulls=True),
        lambda c: c.rpc("search_books", {"query": "x"}).strip_nulls(),
    ),
}


class TestRendersWhatTheStringBuilderSends:
    @pytest.mark.parametrize("case", SAME_QUERY, ids=SAME_QUERY)
    def test_the_same_query_renders_the_same_request(self, case: str) -> None:
        request, string_query = SAME_QUERY[case]
        client = sync_client(Transport())

        assert typed(client, request) == untyped(string_query(client))

    def test_the_orderings_go_into_one_order_parameter(self) -> None:
        request = books(
            TableOperation.SELECT,
            orderings=(Books.title.desc(), Books.id.nulls_first()),
        )

        rendered = _render(request)

        assert rendered.query.get_list("order") == ["title.desc,id.nullsfirst"]

    def test_a_dry_run_asks_for_a_rollback(self) -> None:
        rendered = _render(books(TableOperation.UPDATE, payload=ROW, dry_run=True))

        assert rendered.headers.get_list("Prefer") == ["return=minimal", "tx=rollback"]

    def test_geojson_is_asked_for_through_accept(self) -> None:
        client = sync_client(Transport())
        request = books(TableOperation.SELECT, shape=ResultShape.GEOJSON)

        sent = _render(request).finalize(client.base_url, client.default_headers)

        assert sent.headers.get("Accept") == "application/geo+json"

    def test_the_headers_of_the_options_replace_all_but_prefer(self) -> None:
        client = sync_client(Transport())
        request = books(
            TableOperation.SELECT,
            count=CountMethod.exact,
            options=RequestOptions(
                headers={"X-Query": "q", "Accept-Profile": "other", "Prefer": "x=1"}
            ),
        )

        sent = _render(request).finalize(client.base_url, client.default_headers)

        assert sent.headers.get("X-Query") == "q"
        assert sent.headers.get("Accept-Profile") == "other"
        assert sent.headers.get_list("Prefer") == ["count=exact", "x=1"]

    def test_a_preference_of_the_options_replaces_the_one_of_its_name(self) -> None:
        request = books(
            TableOperation.UPDATE,
            payload=ROW,
            max_affected=2,
            options=RequestOptions(
                headers={"Prefer": "Return=representation, handling=lenient, x=1"}
            ),
        )

        rendered = _render(request)

        assert rendered.headers.get_list("Prefer") == [
            "max-affected=2",
            "Return=representation",
            "handling=lenient",
            "x=1",
        ]

    def test_the_shape_decides_accept_whatever_the_options_say(self) -> None:
        client = sync_client(Transport())
        request = books(
            TableOperation.SELECT,
            shape=ResultShape.SINGLE,
            options=RequestOptions(headers={"Accept": "application/json"}),
        )

        sent = _render(request).finalize(client.base_url, client.default_headers)

        assert sent.headers.get("Accept") == "application/vnd.pgrst.object+json"

    def test_a_request_in_a_schema_renders_as_a_client_of_that_schema(self) -> None:
        client = sync_client(Transport())
        library = sync_client(Transport(), schema="library")
        request = books(TableOperation.SELECT, schema="library")

        assert typed(client, request) == untyped(library.from_("books").select("*"))

    def test_a_table_carrying_its_schema_is_queried_in_it(self) -> None:
        client = sync_client(Transport())
        library = Table("books", BookRow, schema="library")
        of_table = TableRequest(table=library, operation=TableOperation.SELECT)
        of_request = replace(of_table, schema="archive")

        assert typed(client, of_table) == untyped(
            sync_client(Transport(), schema="library").from_("books").select("*")
        )
        assert typed(client, of_request) == untyped(
            sync_client(Transport(), schema="archive").from_("books").select("*")
        )

    def test_a_request_without_a_schema_keeps_the_schema_of_the_client(self) -> None:
        client = sync_client(Transport(), schema="library")

        sent = _render(books(TableOperation.SELECT)).finalize(
            client.base_url, client.default_headers
        )

        assert sent.headers.get("Accept-Profile") == "library"
        assert sent.headers.get("Content-Profile") == "library"


class TestRejectsBeforeSending:
    @pytest.mark.parametrize(
        ("table_request", "message"),
        [
            pytest.param(
                books(TableOperation.INSERT, payload=ROW, filter=Books.id.eq(1)),
                "An insert takes no filter",
                id="filter on an insert",
            ),
            pytest.param(
                books(TableOperation.UPSERT, payload=ROW, filter=Books.id.eq(1)),
                "An upsert takes no filter",
                id="filter on an upsert",
            ),
            pytest.param(
                books(TableOperation.COUNT, limit=1),
                "A count takes filters only",
                id="limit on a count",
            ),
            pytest.param(
                books(TableOperation.COUNT, offset=1),
                "A count takes filters only",
                id="offset on a count",
            ),
            pytest.param(
                books(TableOperation.COUNT, orderings=(Books.id,)),
                "A count takes filters only",
                id="ordering on a count",
            ),
            pytest.param(
                books(TableOperation.COUNT, shape=ResultShape.SINGLE),
                "A count takes filters only",
                id="shape on a count",
            ),
            pytest.param(
                books(TableOperation.COUNT, columns=(Books.id,)),
                "A count takes filters only",
                id="columns on a count",
            ),
            pytest.param(
                books(TableOperation.COUNT, dry_run=True),
                "A count takes filters only",
                id="dry run on a count",
            ),
            pytest.param(
                books(TableOperation.COUNT, max_affected=1),
                "A count takes filters only",
                id="max affected on a count",
            ),
            pytest.param(
                books(TableOperation.INSERT, payload=ROW, shape=ResultShape.SINGLE),
                "returns no rows unless returning is set",
                id="single on a silent insert",
            ),
            pytest.param(
                books(TableOperation.DELETE, shape=ResultShape.CSV),
                "returns no rows unless returning is set",
                id="csv on a silent delete",
            ),
            pytest.param(
                books(
                    TableOperation.UPDATE, payload=ROW, filter=Books.author_name.eq("x")
                ),
                "names no rows of the table",
                id="relation filter on an update",
            ),
            pytest.param(
                books(TableOperation.DELETE, filter=Books.author_name.eq("x")),
                "names no rows of the table",
                id="relation filter on a delete",
            ),
            pytest.param(
                books(TableOperation.COUNT, filter=Books.author_name.eq("x")),
                "names no rows of the table",
                id="relation filter on a count",
            ),
            pytest.param(
                books(TableOperation.INSERT),
                "An insert needs a payload",
                id="insert without a payload",
            ),
            pytest.param(
                books(TableOperation.UPDATE, filter=Books.id.eq(1)),
                "An update needs a payload",
                id="update without a payload",
            ),
            pytest.param(
                books(TableOperation.INSERT, payload=ROW, shape=ResultShape.HEAD),
                "cannot be sent as HEAD",
                id="head on an insert",
            ),
            pytest.param(
                books(TableOperation.SELECT, strip_nulls=True, shape=ResultShape.CSV),
                "strip_nulls cannot be used with the csv shape",
                id="strip nulls with csv",
            ),
            pytest.param(
                books(
                    TableOperation.SELECT, strip_nulls=True, shape=ResultShape.GEOJSON
                ),
                "strip_nulls cannot be used with the geojson shape",
                id="strip nulls with geojson",
            ),
            pytest.param(
                books(
                    TableOperation.SELECT, strip_nulls=True, shape=ResultShape.EXPLAIN
                ),
                "strip_nulls cannot be used with the explain shape",
                id="strip nulls with explain",
            ),
            pytest.param(
                search(payload=[1, 2]),
                "mapping of its arguments",
                id="rpc with a list payload",
            ),
        ],
    )
    def test_an_invalid_request_raises_and_sends_nothing(
        self, table_request: TableRequest, message: str
    ) -> None:
        transport = Transport()
        executor = HttpTableExecutor(sync_client(transport))

        with pytest.raises(ValueError, match=message):
            executor.execute(table_request)

        assert transport.seen == []

    @pytest.mark.parametrize(
        "filter_",
        [
            pytest.param(
                Books.author_name.eq("x") & Books.id.eq(1), id="with a column"
            ),
            pytest.param(~(Books.id.eq(1) | Books.id.eq(2)), id="negated group"),
            pytest.param(Books.id.eq(1) | Books.author_name.eq("x"), id="or group"),
        ],
    )
    def test_a_filter_that_names_rows_of_the_table_is_sent(self, filter_: Any) -> None:
        transport = Transport(content=b"")
        executor = HttpTableExecutor(sync_client(transport))

        executor.execute(books(TableOperation.DELETE, filter=filter_))

        assert transport.only_request.method == "DELETE"


class TestDecodesByShape:
    def execute(self, transport: Transport, request: TableRequest) -> TableResult:
        return HttpTableExecutor(sync_client(transport)).execute(request)

    def test_rows(self) -> None:
        result = self.execute(
            Transport(content=b'[{"id": 1}]'), books(TableOperation.SELECT)
        )

        assert result == TableResult(data=[{"id": 1}], count=None)

    def test_rows_of_an_empty_body(self) -> None:
        result = self.execute(Transport(content=b""), books(TableOperation.SELECT))

        assert result.data == []

    def test_single(self) -> None:
        result = self.execute(
            Transport(content=b'{"id": 1}'),
            books(TableOperation.SELECT, shape=ResultShape.SINGLE),
        )

        assert result.data == {"id": 1}

    @pytest.mark.parametrize(
        ("content", "data"),
        [(b"[]", None), (b'[{"id": 1}]', {"id": 1})],
        ids=["no row", "one row"],
    )
    def test_maybe_single(self, content: bytes, data: object) -> None:
        result = self.execute(
            Transport(content=content),
            books(TableOperation.SELECT, shape=ResultShape.MAYBE_SINGLE),
        )

        assert result.data == data

    def test_maybe_single_rejects_more_than_one_row(self) -> None:
        with pytest.raises(APIError) as error:
            self.execute(
                Transport(content=b'[{"id": 1}, {"id": 2}]'),
                books(TableOperation.SELECT, shape=ResultShape.MAYBE_SINGLE),
            )

        assert error.value.code == "406"

    def test_none_reads_nothing(self) -> None:
        result = self.execute(
            Transport(content=b'[{"id": 1}]'),
            books(TableOperation.SELECT, shape=ResultShape.NONE),
        )

        assert result.data is None

    def test_head_reads_the_count_only(self) -> None:
        transport = Transport(content=b"", headers={"Content-Range": "0-24/120"})

        result = self.execute(
            transport,
            books(
                TableOperation.SELECT, shape=ResultShape.HEAD, count=CountMethod.exact
            ),
        )

        assert result == TableResult(data=None, count=120)

    def test_csv(self) -> None:
        result = self.execute(
            Transport(content=b"id,title\n1,a"),
            books(TableOperation.SELECT, shape=ResultShape.CSV),
        )

        assert result.data == "id,title\n1,a"

    def test_geojson(self) -> None:
        result = self.execute(
            Transport(content=b'{"type": "FeatureCollection", "features": []}'),
            books(TableOperation.SELECT, shape=ResultShape.GEOJSON),
        )

        assert result.data == {"type": "FeatureCollection", "features": []}

    def test_explain_as_text(self) -> None:
        result = self.execute(
            Transport(content=b"Aggregate (cost=0..1)"),
            books(TableOperation.SELECT, shape=ResultShape.EXPLAIN),
        )

        assert result.data == "Aggregate (cost=0..1)"

    def test_explain_as_json(self) -> None:
        result = self.execute(
            Transport(content=b'[{"Plan": {}}]'),
            books(
                TableOperation.SELECT,
                shape=ResultShape.EXPLAIN,
                explain=ExplainOptions(format="json"),
            ),
        )

        assert result.data == [{"Plan": {}}]

    @pytest.mark.parametrize(
        ("content", "data"),
        [(b"42", 42), (b'"x"', "x"), (b'{"a": [1]}', {"a": [1]}), (b"", None)],
        ids=["number", "string", "object", "empty"],
    )
    def test_value(self, content: bytes, data: object) -> None:
        result = self.execute(
            Transport(content=content),
            search(payload={"query": "x"}, shape=ResultShape.VALUE),
        )

        assert result.data == data

    def test_count(self) -> None:
        transport = Transport(content=b"", headers={"Content-Range": "*/7"})

        result = self.execute(transport, books(TableOperation.COUNT))

        assert result == TableResult(data=None, count=7)

    def test_a_counted_select_carries_rows_and_count(self) -> None:
        transport = Transport(
            content=b'[{"id": 1}]', headers={"Content-Range": "0-0/12"}
        )

        result = self.execute(
            transport, books(TableOperation.SELECT, count=CountMethod.exact)
        )

        assert result == TableResult(data=[{"id": 1}], count=12)

    def test_a_write_reads_nothing_back_unless_returning(self) -> None:
        transport = Transport(content=b'[{"id": 1}]')

        silent = self.execute(transport, books(TableOperation.INSERT, payload=ROW))
        returned = self.execute(
            transport, books(TableOperation.INSERT, payload=ROW, returning=True)
        )

        assert silent.data is None
        assert returned.data == [{"id": 1}]

    def test_a_function_call_reads_its_rows_back(self) -> None:
        result = self.execute(
            Transport(content=b'[{"id": 1}]'), search(payload={"query": "x"})
        )

        assert result.data == [{"id": 1}]

    def test_a_dry_run_that_was_rolled_back_returns_its_result(self) -> None:
        transport = Transport(
            content=b'[{"id": 1}]',
            headers={"Preference-Applied": "return=representation, tx=rollback"},
        )

        result = self.execute(
            transport,
            books(TableOperation.INSERT, payload=ROW, returning=True, dry_run=True),
        )

        assert result.data == [{"id": 1}]

    @pytest.mark.parametrize(
        "headers",
        [
            pytest.param({}, id="no preference applied"),
            pytest.param({"Preference-Applied": "return=minimal"}, id="other ones"),
        ],
    )
    def test_a_dry_run_that_was_committed_raises(self, headers: dict[str, str]) -> None:
        transport = Transport(content=b"", headers=headers)

        with pytest.raises(APIError, match="The dry run was committed"):
            self.execute(transport, books(TableOperation.DELETE, dry_run=True))

        assert transport.only_request.headers["Prefer"] == "return=minimal, tx=rollback"

    def test_an_error_status_raises(self) -> None:
        transport = Transport(
            status=400, content=b'{"message": "bad", "code": "22P02"}'
        )

        with pytest.raises(APIError) as error:
            self.execute(transport, books(TableOperation.SELECT))

        assert error.value.message == "bad"
        assert error.value.code == "22P02"

    @pytest.mark.parametrize(
        ("content", "shape"),
        [
            (b'{"id": 1}', ResultShape.ROWS),
            (b"[1, 2]", ResultShape.ROWS),
            (b"1", ResultShape.ROWS),
            (b"[1]", ResultShape.MAYBE_SINGLE),
            (b'[{"id": 1}]', ResultShape.SINGLE),
            (b"not json", ResultShape.ROWS),
        ],
        ids=[
            "rows-as-object",
            "rows-of-scalars",
            "rows-as-scalar",
            "maybe-single-of-scalar",
            "single-as-array",
            "invalid-json",
        ],
    )
    def test_a_body_in_another_shape_raises(
        self, content: bytes, shape: ResultShape
    ) -> None:
        with pytest.raises(APIError):
            self.execute(
                Transport(content=content),
                books(TableOperation.SELECT, shape=shape),
            )


class TestSends:
    def test_sends_what_the_string_builder_sends_for_the_same_query(self) -> None:
        transport = Transport()
        client = sync_client(transport)
        request = books(
            TableOperation.SELECT,
            columns=(Books.id, Books.title),
            filter=Books.id.gt(1) | Books.title.eq("a"),
            orderings=(Books.title.desc().nulls_last(),),
            limit=10,
            offset=10,
        )

        HttpTableExecutor(client).execute(request)
        client.from_("books").select("id,title").or_("id.gt.1,title.eq.a").order(
            "title", desc=True, nullsfirst=False
        ).range(10, 19).execute()

        typed_request, untyped_request = transport.seen
        assert typed_request.method == untyped_request.method
        assert typed_request.url == untyped_request.url
        assert {
            k: v for k, v in typed_request.headers.items() if k != "x-client-info"
        } == {k: v for k, v in untyped_request.headers.items() if k != "x-client-info"}

    def test_lists_typed_api_in_x_client_info_unlike_the_string_builder(self) -> None:
        transport = Transport()
        client = sync_client(transport)

        HttpTableExecutor(client).execute(books(TableOperation.SELECT))
        client.from_("books").select("*").execute()

        typed_request, untyped_request = transport.seen
        client_info = client.default_headers["X-Client-Info"]
        assert (
            typed_request.headers["X-Client-Info"]
            == f"{client_info}; features=typed-api"
        )
        assert untyped_request.headers["X-Client-Info"] == client_info

    def test_lists_typed_api_in_an_x_client_info_the_client_was_given(self) -> None:
        transport = Transport()
        client = sync_client(transport, headers={"X-Client-Info": "supabase-py/3.0.0"})

        HttpTableExecutor(client).execute(books(TableOperation.SELECT))

        assert transport.only_request.headers["X-Client-Info"] == (
            "supabase-py/3.0.0; features=typed-api"
        )

    def test_reads_the_headers_of_the_client_when_it_sends(self) -> None:
        transport = Transport()
        client = sync_client(transport)
        executor = HttpTableExecutor(client)
        client.set_auth("token")

        executor.execute(books(TableOperation.SELECT))

        headers = transport.only_request.headers
        assert headers["apikey"] == "key"
        assert headers["Authorization"] == "Bearer token"

    def test_uses_the_request_timeout_of_the_client_unless_the_options_say(
        self,
    ) -> None:
        transport = Transport()
        executor = HttpTableExecutor(sync_client(transport, request_timeout=12))

        executor.execute(books(TableOperation.SELECT))
        executor.execute(
            books(TableOperation.SELECT, options=RequestOptions(timeout=3))
        )

        assert [r.extensions["timeout"]["read"] for r in transport.seen] == [12, 3]

    def test_retries_with_the_policy_of_the_client(self, sleeps: list[float]) -> None:
        transport = Transport(status=503)
        executor = HttpTableExecutor(
            sync_client(transport, retry=RetryPolicy(max_retries=2, jitter=0))
        )

        with pytest.raises(APIError):
            executor.execute(books(TableOperation.SELECT))

        assert [r.headers.get("X-Retry-Count") for r in transport.seen] == [
            None,
            "1",
            "2",
        ]
        assert sleeps == [0.5, 1]

    def test_the_options_decide_the_retries_of_the_request(
        self, sleeps: list[float]
    ) -> None:
        transport = Transport(status=503)
        executor = HttpTableExecutor(
            sync_client(transport, retry=RetryPolicy(max_retries=2, jitter=0))
        )

        with pytest.raises(APIError):
            executor.execute(
                books(TableOperation.SELECT, options=RequestOptions(retry=False))
            )
        with pytest.raises(APIError):
            executor.execute(
                books(
                    TableOperation.INSERT,
                    payload=ROW,
                    options=RequestOptions(retry=RetryPolicy(max_retries=1, jitter=0)),
                )
            )

        assert [r.method for r in transport.seen] == ["GET", "POST", "POST"]
        assert sleeps == [0.5]

    def test_scopes_the_request_to_its_schema(self) -> None:
        transport = Transport()

        HttpTableExecutor(sync_client(transport)).execute(
            books(TableOperation.SELECT, schema="library")
        )

        headers = transport.only_request.headers
        assert headers["Accept-Profile"] == "library"
        assert headers["Content-Profile"] == "library"

    async def test_the_async_executor_sends_the_same_request(self) -> None:
        transport = Transport(content=b'[{"id": 1}]')
        client = async_client(transport)
        client.set_auth("token")
        request = books(TableOperation.SELECT, filter=Books.id.eq(1), limit=1)

        result = await AsyncHttpTableExecutor(client).execute(request)

        sent = transport.only_request
        assert result.data == [{"id": 1}]
        assert sent.method == "GET"
        assert dict(sent.url.params) == {"select": "*", "id": "eq.1", "limit": "1"}
        assert sent.headers["Authorization"] == "Bearer token"
        assert sent.headers["X-Client-Info"].endswith("; features=typed-api")

    async def test_the_async_executor_rejects_before_sending(self) -> None:
        transport = Transport()
        executor = AsyncHttpTableExecutor(async_client(transport))

        with pytest.raises(ValueError, match="takes no filter"):
            await executor.execute(
                books(TableOperation.INSERT, payload=ROW, filter=Books.id.eq(1))
            )

        assert transport.seen == []


def soft_deleting(request: TableRequest) -> TableRequest:
    """`request` on a table whose rows are deleted by setting `deleted_at`:
    a delete becomes an update, and a read leaves the deleted rows out."""
    if request.operation is TableOperation.DELETE:
        return replace(
            request,
            operation=TableOperation.UPDATE,
            payload={"deleted_at": "2026-11-12T00:00:00+00:00"},
        )
    if request.operation in (TableOperation.SELECT, TableOperation.COUNT):
        alive = Books.deleted_at.is_null()
        filter_ = alive if request.filter is None else request.filter & alive
        return replace(request, filter=filter_)
    return request


@dataclass
class SoftDeleting:
    inner: TableExecutor

    def execute(self, request: TableRequest) -> TableResult:
        return self.inner.execute(soft_deleting(request))


@dataclass
class AsyncSoftDeleting:
    inner: AsyncTableExecutor

    async def execute(self, request: TableRequest) -> TableResult:
        return await self.inner.execute(soft_deleting(request))


class TestWrapsBothExecutors:
    def test_a_wrapper_rewrites_the_requests_of_the_sync_executor(self) -> None:
        transport = Transport(content=b"")
        executor = SoftDeleting(HttpTableExecutor(sync_client(transport)))

        executor.execute(books(TableOperation.DELETE, filter=Books.id.eq(1)))
        executor.execute(books(TableOperation.SELECT, filter=Books.id.gt(1)))
        executor.execute(books(TableOperation.INSERT, payload=ROW))

        deleted, selected, inserted = transport.seen
        assert deleted.method == "PATCH"
        assert deleted.content == b'{"deleted_at":"2026-11-12T00:00:00+00:00"}'
        assert dict(deleted.url.params) == {"id": "eq.1"}
        assert dict(selected.url.params) == {
            "select": "*",
            "id": "gt.1",
            "deleted_at": "is.null",
        }
        assert inserted.method == "POST"
        assert dict(inserted.url.params) == {}

    async def test_a_wrapper_rewrites_the_requests_of_the_async_executor(self) -> None:
        transport = Transport(content=b"")
        executor = AsyncSoftDeleting(AsyncHttpTableExecutor(async_client(transport)))

        await executor.execute(books(TableOperation.DELETE, filter=Books.id.eq(1)))
        await executor.execute(books(TableOperation.COUNT))

        deleted, counted = transport.seen
        assert deleted.method == "PATCH"
        assert counted.method == "HEAD"
        assert dict(counted.url.params) == {"select": "*", "deleted_at": "is.null"}
