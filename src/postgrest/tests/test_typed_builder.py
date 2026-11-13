from collections.abc import Awaitable, Iterator
from dataclasses import FrozenInstanceError, dataclass, field
from datetime import date
from typing import Any

import pytest
from httpx import AsyncClient, Client, MockTransport
from httpx import Request as HttpxRequest
from httpx import Response as HttpxResponse
from pydantic import BaseModel, ValidationError
from supabase_utils.http.adapters.httpx import AsyncHttpxSession, HttpxSession
from supabase_utils.http.retry import RetryPolicy

from postgrest import (
    AsyncHttpTableExecutor,
    AsyncPostgrestClient,
    AsyncTableExecutor,
    CountedResponse,
    CountMethod,
    ExplainOptions,
    HttpTableExecutor,
    PartialRow,
    RequestOptions,
    ResultShape,
    SyncPostgrestClient,
    Table,
    TableExecutor,
    TableOperation,
    TableRequest,
    TableResult,
    TypedBuilder,
    TypedCountBuilder,
    TypedFilterBuilder,
    TypedMutationBuilder,
    TypedQueryBuilder,
    TypedTransformBuilder,
)
from postgrest.request_builder import RequestBuilder
from tests.typed_schema import Books, BooksInsert, BooksRow, BooksUpdate

REST_URL = "https://example.com/rest/v1"
DUNE = {
    "id": 1,
    "title": "Dune",
    "isbn": None,
    "pages": 412,
    "published_on": "1965-08-01",
    "tags": ["science fiction"],
    "metadata": None,
}
EMMA = {**DUNE, "id": 2, "title": "Emma", "pages": 474}
ROWS = TableResult(data=[DUNE, EMMA], count=7)

type SyncBooks = TypedQueryBuilder[TableExecutor, BooksRow, BooksInsert, BooksUpdate]


@dataclass
class Recording:
    """A sync executor that answers every request with `result` and keeps
    what it was given."""

    result: TableResult = field(default_factory=TableResult)
    requests: list[TableRequest] = field(default_factory=list)

    def execute(self, request: TableRequest) -> TableResult:
        self.requests.append(request)
        return self.result

    @property
    def only_request(self) -> TableRequest:
        (request,) = self.requests
        return request


@dataclass
class AsyncRecording:
    result: TableResult = field(default_factory=TableResult)
    requests: list[TableRequest] = field(default_factory=list)

    async def execute(self, request: TableRequest) -> TableResult:
        self.requests.append(request)
        return self.result


def books(result: TableResult = ROWS) -> tuple[SyncBooks, Recording]:
    executor = Recording(result)
    return TypedQueryBuilder(Books.table, executor), executor


def request(operation: TableOperation, **fields: Any) -> TableRequest:
    return TableRequest(table=Books.table, operation=operation, **fields)


class TestClient:
    @pytest.fixture
    def sync_client(self) -> Iterator[SyncPostgrestClient]:
        with Client() as client:
            yield SyncPostgrestClient(
                REST_URL, http_session=HttpxSession(client=client)
            )

    @pytest.fixture
    async def async_client(self) -> AsyncPostgrestClient:
        return AsyncPostgrestClient(
            REST_URL, http_session=AsyncHttpxSession(client=AsyncClient())
        )

    def test_a_table_gives_the_typed_builder_over_the_http_executor(
        self, sync_client: SyncPostgrestClient
    ) -> None:
        builder = sync_client.table(Books.table)

        assert isinstance(builder, TypedQueryBuilder)
        assert builder.table is Books.table
        assert isinstance(builder.executor, HttpTableExecutor)
        assert builder.executor.client is sync_client

    async def test_the_async_client_gives_the_async_executor(
        self, async_client: AsyncPostgrestClient
    ) -> None:
        builder = async_client.table(Books.table)

        assert isinstance(builder.executor, AsyncHttpTableExecutor)
        assert builder.executor.client is async_client

    def test_builders_of_one_client_compare_by_request(
        self, sync_client: SyncPostgrestClient
    ) -> None:
        query = sync_client.table(Books.table).select().where(Books.id.eq(1))

        assert query == sync_client.table(Books.table).select().where(Books.id.eq(1))
        assert query != sync_client.table(Books.table).select()

    def test_a_name_still_gives_the_string_builder(
        self, sync_client: SyncPostgrestClient
    ) -> None:
        assert isinstance(sync_client.table("books"), RequestBuilder)
        assert isinstance(sync_client.table(table="books"), RequestBuilder)


class TestSelect:
    def test_reads_every_column(self) -> None:
        builder, executor = books()

        rows = builder.select().execute()

        assert executor.only_request == request(TableOperation.SELECT)
        assert rows == [BooksRow.model_validate(DUNE), BooksRow.model_validate(EMMA)]
        assert rows[0].published_on == date(1965, 8, 1)

    def test_rows_that_do_not_decode_raise(self) -> None:
        builder, _ = books(TableResult(data=[{"id": "one"}]))

        with pytest.raises(ValidationError):
            builder.select().execute()

    def test_select_only_reads_the_columns_as_partial_rows(self) -> None:
        builder, executor = books(TableResult(data=[{"id": 1, "published_on": None}]))

        rows = builder.select_only([Books.id, Books.published_on]).execute()

        assert executor.only_request == request(
            TableOperation.SELECT, columns=(Books.id, Books.published_on)
        )
        assert rows == [
            PartialRow(
                Books.table,
                (Books.id, Books.published_on),
                {"id": 1, "published_on": None},
            )
        ]
        assert rows[0][Books.id] == 1
        assert rows[0][Books.published_on] is None

    def test_select_only_takes_any_iterable_of_columns(self) -> None:
        builder, executor = books()

        builder.select_only(column for column in (Books.id, Books.title)).execute()

        assert executor.only_request.columns == (Books.id, Books.title)

    def test_select_only_needs_a_column(self) -> None:
        builder, _ = books()

        with pytest.raises(
            ValueError, match="select_only\\(\\) needs at least one column"
        ):
            builder.select_only([])

    def test_where_combines_with_and(self) -> None:
        builder, executor = books()

        builder.select().where(Books.id.gt(1)).where(Books.title.eq("x")).execute()

        assert executor.only_request.filter == Books.id.gt(1) & Books.title.eq("x")

    def test_order_appends(self) -> None:
        builder, executor = books()

        builder.select().order(Books.title.desc()).order(Books.id).execute()

        assert executor.only_request.orderings == (Books.title.desc(), Books.id)

    def test_limit_and_range(self) -> None:
        builder, executor = books()

        builder.select().limit(5).execute()
        builder.select().range(10, 19).execute()

        assert executor.requests[0].limit == 5
        assert executor.requests[0].offset is None
        assert executor.requests[1].offset == 10
        assert executor.requests[1].limit == 10

    def test_range_rejects_an_end_before_its_start(self) -> None:
        builder, _ = books()

        with pytest.raises(
            ValueError, match="range\\(\\) needs end \\(1\\) to be at least"
        ):
            builder.select().range(2, 1)

    def test_the_flags_of_a_request(self) -> None:
        builder, executor = books()

        builder.select().strip_nulls().dry_run().max_affected(3).execute()

        assert executor.only_request == request(
            TableOperation.SELECT, strip_nulls=True, dry_run=True, max_affected=3
        )

    def test_the_options_of_a_request(self) -> None:
        builder, executor = books()
        policy = RetryPolicy(max_retries=1)

        builder.select().retry(policy).request_timeout(2.5).execute()
        builder.select().retry(False).execute()

        assert executor.requests[0].options == RequestOptions(retry=policy, timeout=2.5)
        assert executor.requests[1].options == RequestOptions(retry=False)

    def test_an_invalid_timeout_is_rejected(self) -> None:
        builder, _ = books()

        with pytest.raises(ValueError, match="timeout"):
            builder.select().request_timeout(-1)


class TestShapes:
    def test_single_decodes_the_one_row(self) -> None:
        builder, executor = books(TableResult(data=DUNE))

        row = builder.select().where(Books.id.eq(1)).single().execute()

        assert executor.only_request.shape is ResultShape.SINGLE
        assert row == BooksRow.model_validate(DUNE)

    def test_single_keeps_the_partial_rows_of_select_only(self) -> None:
        builder, _ = books(TableResult(data={"id": 1}))

        row = builder.select_only([Books.id]).single().execute()

        assert row[Books.id] == 1

    def test_maybe_single_decodes_the_row_or_none(self) -> None:
        builder, executor = books(TableResult(data=DUNE))
        assert builder.select().maybe_single().execute() == BooksRow.model_validate(
            DUNE
        )
        assert executor.only_request.shape is ResultShape.MAYBE_SINGLE

        builder, _ = books(TableResult(data=None))
        assert builder.select().maybe_single().execute() is None

    def test_count_adds_the_count_to_the_data(self) -> None:
        builder, executor = books()

        response = builder.select().count().execute()

        assert executor.only_request.count is CountMethod.exact
        assert response == CountedResponse(
            [BooksRow.model_validate(DUNE), BooksRow.model_validate(EMMA)], 7
        )

    def test_count_keeps_the_shape_it_follows(self) -> None:
        builder, executor = books(TableResult(data=DUNE, count=1))

        response = builder.select().single().count(CountMethod.planned).execute()

        assert executor.only_request.count is CountMethod.planned
        assert executor.only_request.shape is ResultShape.SINGLE
        assert response == CountedResponse(BooksRow.model_validate(DUNE), 1)

    def test_a_count_only_reads_no_rows(self) -> None:
        builder, executor = books(TableResult(count=3))

        count = builder.count(CountMethod.estimated).where(Books.id.gt(1)).execute()

        assert executor.only_request == request(
            TableOperation.COUNT,
            count=CountMethod.estimated,
            shape=ResultShape.NONE,
            filter=Books.id.gt(1),
        )
        assert count == 3

    def test_a_missing_count_raises(self) -> None:
        builder, _ = books(TableResult(data=[]))

        with pytest.raises(ValueError, match="returned no count"):
            builder.count().execute()

    def test_head_resolves_to_nothing(self) -> None:
        builder, executor = books(TableResult())

        assert builder.select().where(Books.id.eq(1)).head().execute() is None
        assert executor.only_request.shape is ResultShape.HEAD

    def test_head_rejects_a_write(self) -> None:
        builder, _ = books()

        with pytest.raises(
            ValueError, match="head\\(\\) applies to a select, not to the insert"
        ):
            builder.insert({"title": "x"}).head()

    def test_csv_resolves_to_the_text(self) -> None:
        builder, executor = books(TableResult(data="id,title\n1,Dune\n"))

        text = builder.select().csv().order(Books.id).execute()

        assert executor.only_request.shape is ResultShape.CSV
        assert executor.only_request.orderings == (Books.id,)
        assert text == "id,title\n1,Dune\n"

    def test_a_result_that_is_not_text_raises(self) -> None:
        builder, _ = books(TableResult(data=[]))

        with pytest.raises(ValidationError):
            builder.select().csv().execute()

    def test_explain_resolves_to_the_plan(self) -> None:
        builder, executor = books(TableResult(data="Seq Scan"))
        assert builder.select().explain(analyze=True, wal=True).execute() == "Seq Scan"
        assert executor.only_request.shape is ResultShape.EXPLAIN
        assert executor.only_request.explain == ExplainOptions(analyze=True, wal=True)

        builder, executor = books(TableResult(data=[{"Plan": {}}]))
        assert builder.select().explain(format="json").execute() == [{"Plan": {}}]
        assert executor.only_request.explain == ExplainOptions(format="json")

    def test_geojson_resolves_to_the_collection(self) -> None:
        collection = {"type": "FeatureCollection", "features": []}
        builder, executor = books(TableResult(data=collection))

        assert builder.select().geojson().execute() == collection
        assert executor.only_request.shape is ResultShape.GEOJSON


class Insert(BaseModel):
    title: str
    published_on: date | None = None


class TestWrites:
    def test_insert_sends_one_row_silently(self) -> None:
        builder, executor = books(TableResult())

        assert (
            builder.insert({"title": "x", "published_on": date(2020, 1, 2)}).execute()
            is None
        )

        assert executor.only_request == request(
            TableOperation.INSERT,
            payload={"title": "x", "published_on": "2020-01-02"},
            shape=ResultShape.NONE,
        )

    @pytest.mark.parametrize(
        "rows",
        [
            [{"title": "x"}, {"title": "y", "pages": 2}],
            ({"title": "x"}, {"title": "y", "pages": 2}),
            iter([{"title": "x"}, {"title": "y", "pages": 2}]),
        ],
        ids=["list", "tuple", "iterator"],
    )
    def test_insert_sends_an_iterable_as_a_list_of_rows(self, rows: Any) -> None:
        builder, executor = books(TableResult())

        builder.insert(rows).execute()

        assert executor.only_request.payload == [
            {"title": "x"},
            {"title": "y", "pages": 2},
        ]

    def test_insert_serializes_a_model_as_pydantic_does(self) -> None:
        _, executor = books(TableResult())
        legacy = TypedQueryBuilder(
            Table[dict[str, Any], Any, Any]("books", dict), executor
        )

        legacy.insert(Insert(title="x")).execute()
        legacy.insert([Insert(title="y", published_on=date(2020, 1, 2))]).execute()

        assert executor.requests[0].payload == {"title": "x", "published_on": None}
        assert executor.requests[1].payload == [
            {"title": "y", "published_on": "2020-01-02"}
        ]

    @pytest.mark.parametrize(
        "rows", ["title", 7, [1], [{"title": "x"}, "y"], object(), [object()]]
    )
    def test_insert_rejects_what_is_not_a_row(self, rows: Any) -> None:
        builder, _ = books()

        with pytest.raises(TypeError, match="insert\\(\\) takes a row"):
            builder.insert(rows)

    def test_insert_returns_the_rows_with_select(self) -> None:
        builder, executor = books()

        rows = builder.insert({"title": "x"}).select().execute()

        assert executor.only_request == request(
            TableOperation.INSERT, payload={"title": "x"}, returning=True
        )
        assert rows == [BooksRow.model_validate(DUNE), BooksRow.model_validate(EMMA)]

    def test_insert_returns_some_columns_with_select_only(self) -> None:
        builder, executor = books(TableResult(data=[{"id": 9}]))

        rows = builder.insert({"title": "x"}).select_only([Books.id]).execute()

        assert executor.only_request == request(
            TableOperation.INSERT,
            payload={"title": "x"},
            returning=True,
            columns=(Books.id,),
        )
        assert rows[0][Books.id] == 9

    def test_insert_returns_one_row_with_select_and_single(self) -> None:
        builder, executor = books(TableResult(data=DUNE))

        row = builder.insert({"title": "x"}).select().single().dry_run().execute()

        assert executor.only_request.shape is ResultShape.SINGLE
        assert executor.only_request.dry_run is True
        assert row == BooksRow.model_validate(DUNE)

    def test_upsert(self) -> None:
        builder, executor = books(TableResult())

        builder.upsert({"title": "x"}).execute()
        builder.upsert(
            [{"title": "x"}],
            on_conflict=[Books.isbn, Books.title],
            ignore_duplicates=True,
        ).execute()

        assert executor.requests[0] == request(
            TableOperation.UPSERT, payload={"title": "x"}, shape=ResultShape.NONE
        )
        assert executor.requests[1] == request(
            TableOperation.UPSERT,
            payload=[{"title": "x"}],
            shape=ResultShape.NONE,
            on_conflict=(Books.isbn, Books.title),
            ignore_duplicates=True,
        )

    def test_upsert_needs_a_column_to_conflict_on(self) -> None:
        builder, _ = books()

        with pytest.raises(ValueError, match="on_conflict needs at least one column"):
            builder.upsert({"title": "x"}, on_conflict=[])

    def test_update_needs_where_or_all(self) -> None:
        builder, executor = books(TableResult())
        mutation = builder.update({"title": "x"})

        assert isinstance(mutation, TypedMutationBuilder)
        assert not hasattr(mutation, "execute")
        assert mutation.where(Books.id.eq(1)).execute() is None
        assert mutation.all().execute() is None

        assert executor.requests[0] == request(
            TableOperation.UPDATE,
            payload={"title": "x"},
            shape=ResultShape.NONE,
            filter=Books.id.eq(1),
        )
        assert executor.requests[1] == request(
            TableOperation.UPDATE, payload={"title": "x"}, shape=ResultShape.NONE
        )

    @pytest.mark.parametrize("values", [[{"title": "x"}], object()])
    def test_update_rejects_what_is_not_a_row(self, values: Any) -> None:
        builder, _ = books()

        with pytest.raises(TypeError, match="update\\(\\) takes a mapping"):
            builder.update(values)

    def test_update_returns_the_rows_with_select(self) -> None:
        builder, executor = books()

        rows = (
            builder.update({"title": "x"})
            .where(Books.id.eq(1))
            .max_affected(1)
            .select()
            .execute()
        )

        assert executor.only_request == request(
            TableOperation.UPDATE,
            payload={"title": "x"},
            filter=Books.id.eq(1),
            max_affected=1,
            returning=True,
        )
        assert len(rows) == 2

    def test_delete_needs_where_or_all(self) -> None:
        builder, executor = books(TableResult())

        assert builder.delete().where(Books.id.eq(1)).execute() is None
        assert builder.delete().all().max_affected(10).execute() is None

        assert executor.requests[0] == request(
            TableOperation.DELETE, shape=ResultShape.NONE, filter=Books.id.eq(1)
        )
        assert executor.requests[1] == request(
            TableOperation.DELETE, shape=ResultShape.NONE, max_affected=10
        )

    def test_delete_counts_the_rows_it_affected(self) -> None:
        builder, executor = books(TableResult(count=4))

        response = builder.delete().all().count().execute()

        assert executor.only_request.count is CountMethod.exact
        assert response == CountedResponse(None, 4)


class TestValue:
    def test_every_step_returns_a_new_builder(self) -> None:
        builder, _ = books()
        query = builder.select()

        filtered = query.where(Books.id.eq(1))
        ordered = filtered.order(Books.id)

        assert query.request.filter is None
        assert filtered.request.filter == Books.id.eq(1)
        assert filtered.request.orderings == ()
        assert ordered.request.orderings == (Books.id,)
        assert isinstance(query, TypedFilterBuilder)
        assert isinstance(ordered, TypedFilterBuilder)
        assert isinstance(query.single(), TypedTransformBuilder)
        assert isinstance(query.head(), TypedBuilder)
        assert isinstance(builder.count(), TypedCountBuilder)

    def test_builders_are_immutable(self) -> None:
        builder, _ = books()
        query = builder.select()

        with pytest.raises(FrozenInstanceError):
            query.request = query.request  # pyrefly: ignore[read-only]
        with pytest.raises(FrozenInstanceError):
            builder.table = Books.table  # pyrefly: ignore[read-only]

    def test_builders_with_the_same_request_are_equal(self) -> None:
        builder, _ = books()

        assert builder.select().where(Books.id.eq(1)) == builder.select().where(
            Books.id.eq(1)
        )
        assert builder.select() != builder.select().where(Books.id.eq(1))


@dataclass
class Transport:
    content: bytes = b"[]"
    seen: list[HttpxRequest] = field(default_factory=list)

    def handler(self, request: HttpxRequest) -> HttpxResponse:
        self.seen.append(request)
        return HttpxResponse(200, content=self.content)


class TestExecute:
    def test_a_sync_executor_resolves_at_once(self) -> None:
        builder, _ = books()

        assert isinstance(builder.select().execute(), list)

    async def test_an_async_executor_resolves_when_awaited(self) -> None:
        executor = AsyncRecording(ROWS)
        builder = TypedQueryBuilder(Books.table, executor)

        pending = builder.select().where(Books.id.eq(1)).execute()

        assert isinstance(pending, Awaitable)
        assert await pending == [
            BooksRow.model_validate(DUNE),
            BooksRow.model_validate(EMMA),
        ]
        assert executor.requests == [
            request(TableOperation.SELECT, filter=Books.id.eq(1))
        ]

    def test_the_sync_client_sends_the_rendered_request(self) -> None:
        transport = Transport(
            content=b'[{"id": 1, "title": "Dune", "pages": 1, "tags": []}]'
        )
        client = SyncPostgrestClient(
            REST_URL,
            http_session=HttpxSession(
                client=Client(transport=MockTransport(transport.handler))
            ),
        )

        rows = client.table(Books.table).select().where(Books.id.eq(1)).execute()

        (sent,) = transport.seen
        assert sent.url.path == "/rest/v1/books"
        assert sorted(sent.url.params.multi_items()) == [
            ("id", "eq.1"),
            ("select", "*"),
        ]
        assert "features=typed-api" in sent.headers["X-Client-Info"]
        assert rows == [BooksRow(id=1, title="Dune", pages=1, tags=[])]

    async def test_the_async_client_sends_the_rendered_request(self) -> None:
        transport = Transport(
            content=b'{"id": 1, "title": "Dune", "pages": 1, "tags": []}'
        )
        client = AsyncPostgrestClient(
            REST_URL,
            http_session=AsyncHttpxSession(
                client=AsyncClient(transport=MockTransport(transport.handler))
            ),
        )

        row = await client.table(Books.table).select().single().execute()

        (sent,) = transport.seen
        assert sent.headers["Accept"] == "application/vnd.pgrst.object+json"
        assert row == BooksRow(id=1, title="Dune", pages=1, tags=[])


async def test_the_executor_protocols_fit_the_fakes() -> None:
    sync_executor: TableExecutor = Recording()
    async_executor: AsyncTableExecutor = AsyncRecording()

    assert isinstance(
        sync_executor.execute(request(TableOperation.SELECT)), TableResult
    )
    pending = async_executor.execute(request(TableOperation.SELECT))
    assert isinstance(pending, Awaitable)
    assert isinstance(await pending, TableResult)
