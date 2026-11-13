from dataclasses import FrozenInstanceError, replace

import pytest
from supabase_utils.http.retry import RetryPolicy

from postgrest import (
    Column,
    ComputedField,
    CountMethod,
    ExplainOptions,
    RequestOptions,
    ResultShape,
    Table,
    TableOperation,
    TableRequest,
    TableResult,
)


class BookRow:
    pass


class Books:
    id = Column[BookRow, int]("id")
    title = Column[BookRow, str]("title")
    full_title = ComputedField[BookRow, str]("full_title")
    table = Table("books", BookRow, primary_key=(id,), computed_fields=(full_title,))


class TestTable:
    def test_a_table_carries_its_name_row_type_and_keys(self) -> None:
        assert Books.table.name == "books"
        assert Books.table.row_type is BookRow
        assert Books.table.primary_key == (Books.id,)
        assert Books.table.computed_fields == (Books.full_title,)
        assert Books.table.schema is None

    def test_a_table_defaults_to_no_key_and_the_schema_of_the_client(self) -> None:
        table = Table("books", BookRow)

        assert table.primary_key == ()
        assert table.computed_fields == ()
        assert table.schema is None

    def test_a_table_may_carry_its_schema(self) -> None:
        assert Table("books", BookRow, schema="library").schema == "library"

    def test_a_table_is_a_value(self) -> None:
        declared_twice = Table(
            "books",
            BookRow,
            primary_key=(Books.id,),
            computed_fields=(Books.full_title,),
        )

        assert declared_twice == Books.table
        assert Table("books", BookRow) != Table("authors", BookRow)
        with pytest.raises(FrozenInstanceError):
            Books.table.name = "authors"  # pyrefly: ignore[read-only]


class TestTableRequest:
    def test_a_request_defaults_to_every_column_of_every_row(self) -> None:
        request = TableRequest(table=Books.table, operation=TableOperation.SELECT)

        assert request.schema is None
        assert request.columns == ()
        assert request.filter is None
        assert request.orderings == ()
        assert request.limit is None
        assert request.offset is None
        assert request.shape is ResultShape.ROWS
        assert request.count is None
        assert request.payload is None
        assert request.read_only is False
        assert request.on_conflict is None
        assert request.ignore_duplicates is False
        assert request.returning is False
        assert request.max_affected is None
        assert request.strip_nulls is False
        assert request.dry_run is False
        assert request.explain is None
        assert request.options == RequestOptions()

    def test_a_changed_copy_leaves_the_request_as_it_was(self) -> None:
        request = TableRequest(
            table=Books.table,
            operation=TableOperation.SELECT,
            filter=Books.id.eq(1),
            orderings=(Books.title.desc(),),
        )

        limited = replace(request, limit=5, orderings=())

        assert limited.limit == 5
        assert limited.orderings == ()
        assert limited.filter == Books.id.eq(1)
        assert request.limit is None
        assert request.orderings == (Books.title.desc(),)
        with pytest.raises(FrozenInstanceError):
            request.limit = 5  # pyrefly: ignore[read-only]

    def test_requests_with_the_same_fields_are_equal(self) -> None:
        def request() -> TableRequest:
            return TableRequest(
                table=Books.table,
                operation=TableOperation.UPDATE,
                filter=Books.id.eq(1) & ~Books.title.eq("a"),
                payload={"title": "b"},
                count=CountMethod.exact,
                options=RequestOptions(headers={"X-Query": "q"}, timeout=3),
            )

        assert request() == request()
        assert request() != replace(request(), payload={"title": "c"})


class TestRequestOptions:
    def test_the_options_default_to_the_client(self) -> None:
        options = RequestOptions()

        assert options.headers == {}
        assert options.retry is None
        assert options.timeout is None

    def test_a_retry_policy_and_a_timeout_are_kept_as_given(self) -> None:
        policy = RetryPolicy(max_retries=1)
        options = RequestOptions(retry=policy, timeout=2.5)

        assert options.retry is policy
        assert options.timeout == 2.5
        assert RequestOptions(retry=False).retry is False

    @pytest.mark.parametrize("timeout", [0, -1, float("inf"), float("nan")])
    def test_a_timeout_must_be_a_positive_number_of_seconds(
        self, timeout: float
    ) -> None:
        with pytest.raises(ValueError, match="positive number of seconds"):
            RequestOptions(timeout=timeout)


class TestExplainOptions:
    def test_the_options_default_to_a_plain_text_plan(self) -> None:
        options = ExplainOptions()

        assert options == ExplainOptions(
            analyze=False,
            verbose=False,
            settings=False,
            buffers=False,
            wal=False,
            format="text",
        )


class TestTableResult:
    def test_a_result_defaults_to_no_data_and_no_count(self) -> None:
        assert TableResult() == TableResult(data=None, count=None)

    def test_a_result_holds_the_data_and_the_count(self) -> None:
        result = TableResult([{"id": 1}], 2)

        assert result.data == [{"id": 1}]
        assert result.count == 2
