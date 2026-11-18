import re
from datetime import UTC, datetime
from typing import Any

import pytest
from postgrest import Column, Filter, NullableColumn, Table
from pydantic import BaseModel

from realtime.channel import RealtimeChannelOptions
from realtime.types import PostgresChangesBinding, RealtimePostgresChangesListenEvent

INSERT = RealtimePostgresChangesListenEvent.Insert


class BooksRow(BaseModel):
    id: int
    title: str
    subtitle: str | None = None
    pages: int
    is_done: bool
    tags: list[str]
    published_at: datetime | None = None


class Books:
    id = Column[BooksRow, int]("id")
    title = Column[BooksRow, str]("title")
    subtitle = NullableColumn[BooksRow, str]("subtitle")
    pages = Column[BooksRow, int]("pages")
    is_done = Column[BooksRow, bool]("is_done")
    tags = Column[BooksRow, list[str]]("tags")
    published_at = NullableColumn[BooksRow, datetime]("published_at")
    table = Table("books", BooksRow, primary_key=(id,), schema="library")


def binding(**arguments: Any) -> PostgresChangesBinding:
    options = RealtimeChannelOptions().postgres_changes(
        INSERT, Books.table, **arguments
    )
    (only,) = options.postgres_changes_bindings
    return only


def rendered(filter: Filter[BooksRow]) -> str | None:
    return binding(filter=filter).filter


class TestTable:
    def test_a_typed_table_sends_its_name_and_schema(self) -> None:
        sent = binding()

        assert (sent.table, sent.schema, sent.filter, sent.select) == (
            "books",
            "library",
            None,
            None,
        )

    def test_an_explicit_schema_overrides_the_table_schema(self) -> None:
        assert binding(schema="archive").schema == "archive"

    def test_a_table_without_a_schema_is_listened_to_in_public(self) -> None:
        table = Table("books", BooksRow)

        options = RealtimeChannelOptions().postgres_changes(INSERT, table)

        assert options.postgres_changes_bindings[0].schema == "public"

    def test_an_empty_schema_is_sent_as_given(self) -> None:
        options = RealtimeChannelOptions().postgres_changes(INSERT, "books", schema="")

        assert options.postgres_changes_bindings[0].schema == ""

    def test_the_string_overload_is_unchanged(self) -> None:
        options = RealtimeChannelOptions().postgres_changes(
            INSERT, "books", filter="id=eq.1", select=["title"]
        )

        assert options.postgres_changes_bindings == (
            PostgresChangesBinding(
                event=INSERT,
                table="books",
                schema="public",
                filter="id=eq.1",
                select=("title",),
            ),
        )


class TestFilter:
    @pytest.mark.parametrize(
        ("filter", "expected"),
        [
            (Books.id.eq(1), "id=eq.1"),
            (Books.id.neq(1), "id=neq.1"),
            (Books.pages.lt(10), "pages=lt.10"),
            (Books.pages.lte(10), "pages=lte.10"),
            (Books.pages.gt(10), "pages=gt.10"),
            (Books.pages.gte(10), "pages=gte.10"),
            (Books.title.is_distinct("Dune"), "title=isdistinct.Dune"),
            (Books.id.in_([1, 2]), "id=in.(1,2)"),
            (Books.title.like("%Dune%"), "title=like.%Dune%"),
            (Books.title.ilike("%dune%"), "title=ilike.%dune%"),
            (Books.title.match_regex("^D"), "title=match.^D"),
            (Books.title.imatch_regex("^d"), "title=imatch.^d"),
            (Books.subtitle.is_null(), "subtitle=is.null"),
            (Books.is_done.is_true(), "is_done=is.true"),
            (Books.is_done.is_false(), "is_done=is.false"),
        ],
    )
    def test_a_comparison_renders_as_one_condition(
        self, filter: Filter[BooksRow], expected: str
    ) -> None:
        assert rendered(filter) == expected

    def test_a_negated_comparison_renders_not(self) -> None:
        assert rendered(~Books.id.in_([1, 2])) == "id=not.in.(1,2)"

    def test_a_double_negation_collapses(self) -> None:
        assert rendered(~~Books.id.eq(1)) == "id=eq.1"

    def test_an_and_renders_its_conditions_separated_by_commas(self) -> None:
        filter = Books.pages.gt(100) & ~Books.subtitle.is_null() & Books.id.lt(9)

        assert rendered(filter) == "pages=gt.100,subtitle=not.is.null,id=lt.9"

    def test_a_value_with_reserved_characters_is_quoted(self) -> None:
        assert rendered(Books.title.eq('a,b "c"')) == r'title=eq."a,b \"c\""'

    def test_an_in_member_with_reserved_characters_is_quoted(self) -> None:
        assert rendered(Books.title.in_(["a,b", "c"])) == 'title=in.("a,b",c)'

    @pytest.mark.parametrize(
        ("value", "expected"),
        [(" Dune", 'title=eq." Dune"'), ("Dune ", 'title=eq."Dune "')],
    )
    def test_a_value_with_surrounding_whitespace_is_quoted(
        self, value: str, expected: str
    ) -> None:
        assert rendered(Books.title.eq(value)) == expected

    def test_a_negated_value_with_surrounding_whitespace_is_quoted(self) -> None:
        assert rendered(~Books.title.eq("Dune ")) == 'title=not.eq."Dune "'

    @pytest.mark.parametrize(
        ("members", "expected"),
        [
            ([""], 'title=in.("")'),
            (["NULL"], 'title=in.("NULL")'),
            (["null"], 'title=in.("null")'),
            (["a b"], 'title=in.("a b")'),
            (["{a}"], 'title=in.("{a}")'),
            (["a)b", "c"], 'title=in.("a)b",c)'),
            (['a"b'], r'title=in.("a\"b")'),
        ],
    )
    def test_an_in_member_is_quoted_as_an_array_element(
        self, members: list[str], expected: str
    ) -> None:
        assert rendered(Books.title.in_(members)) == expected

    def test_a_negated_in_member_is_quoted_as_an_array_element(self) -> None:
        assert rendered(~Books.title.in_(["NULL"])) == 'title=not.in.("NULL")'

    def test_a_datetime_is_sent_with_its_offset(self) -> None:
        moment = datetime(2026, 11, 18, 12, 30, tzinfo=UTC)

        assert rendered(Books.published_at.gt(moment)) == (
            'published_at=gt."2026-11-18T12:30:00+00:00"'
        )

    def test_an_operator_the_server_judges_is_sent(self) -> None:
        assert rendered(Books.tags.contains(["sf"])) == "tags=cs.{sf}"

    def test_a_raw_filter_is_sent_as_written(self) -> None:
        assert rendered(Filter.raw("title", "eq.Dune")) == "title=eq.Dune"

    def test_a_raw_operand_on_a_column_is_sent_as_written(self) -> None:
        assert rendered(Books.title.raw("eq.Dune")) == "title=eq.Dune"

    def test_a_negated_raw_filter_gains_not(self) -> None:
        assert rendered(~Filter.raw("title", "eq.Dune")) == "title=not.eq.Dune"

    def test_a_negated_raw_not_filter_loses_it(self) -> None:
        assert rendered(~Filter.raw("title", "not.eq.Dune")) == "title=eq.Dune"

    def test_a_string_filter_is_sent_unchanged(self) -> None:
        assert binding(filter="id=eq.1").filter == "id=eq.1"

    @pytest.mark.parametrize(
        "filter",
        [
            Books.id.eq(1) | Books.id.eq(2),
            Books.pages.gt(1) & (Books.id.eq(1) | Books.id.eq(2)),
        ],
    )
    def test_an_or_raises(self, filter: Filter[BooksRow]) -> None:
        with pytest.raises(ValueError, match=re.escape("cannot use |")):
            rendered(filter)

    @pytest.mark.parametrize(
        "filter",
        [
            ~(Books.id.eq(1) & Books.pages.gt(2)),
            ~(Books.id.eq(1) | Books.id.eq(2)),
        ],
    )
    def test_a_negated_group_raises(self, filter: Filter[BooksRow]) -> None:
        with pytest.raises(ValueError, match="cannot negate a group"):
            rendered(filter)


class TestSelect:
    def test_columns_are_sent_by_name_with_the_primary_key(self) -> None:
        assert binding(select=[Books.title, Books.subtitle]).select == (
            "title",
            "subtitle",
            "id",
        )

    def test_a_selected_primary_key_is_not_repeated(self) -> None:
        assert binding(select=[Books.id, Books.title]).select == ("id", "title")

    def test_names_on_a_typed_table_gain_the_primary_key(self) -> None:
        assert binding(select=["title"]).select == ("title", "id")

    def test_a_table_without_a_primary_key_sends_the_columns_only(self) -> None:
        table = Table("books", BooksRow)

        options = RealtimeChannelOptions().postgres_changes(
            INSERT, table, select=[Books.title]
        )

        assert options.postgres_changes_bindings[0].select == ("title",)
