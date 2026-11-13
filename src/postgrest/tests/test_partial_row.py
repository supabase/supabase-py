from dataclasses import dataclass
from datetime import date
from typing import Annotated, Any

import pytest
from pydantic import BaseModel, Field, ValidationError

from postgrest import Column, ComputedField, NullableColumn, PartialRow, Table
from tests.typed_schema import Books, BooksRow

ROW = {"id": 1, "title": "Dune", "published_on": "1965-08-01", "title_upper": "DUNE"}


def row(*columns: Any, json: dict[str, Any] = ROW) -> PartialRow[BooksRow]:
    return PartialRow(Books.table, columns, json)


class TestReads:
    def test_a_column_reads_as_the_field_of_the_row_type(self) -> None:
        partial = row(Books.id, Books.title, Books.published_on)

        assert partial[Books.id] == 1
        assert partial[Books.title] == "Dune"
        assert partial[Books.published_on] == date(1965, 8, 1)

    def test_a_nullable_column_reads_none(self) -> None:
        partial = row(Books.published_on, json={"published_on": None})

        assert partial[Books.published_on] is None

    def test_a_stripped_column_reads_none(self) -> None:
        partial = row(Books.id, Books.published_on, json={"id": 1})

        assert partial[Books.published_on] is None

    def test_a_computed_field_reads_the_decoded_value(self) -> None:
        partial = row(Books.title_upper)

        assert partial[Books.title_upper] == "DUNE"

    def test_a_computed_field_decodes_through_its_value_type(self) -> None:
        partial = row(Books.next_publication, json={"next_publication": "1966-08-01"})

        assert partial[Books.next_publication] == date(1966, 8, 1)

    def test_a_computed_field_without_a_value_type_reads_the_decoded_value(
        self,
    ) -> None:
        untyped = ComputedField[BooksRow, date]("next_publication")
        partial = row(untyped, json={"next_publication": "1966-08-01"})

        assert partial[untyped] == "1966-08-01"

    def test_an_ad_hoc_column_named_after_a_field_reads_like_it(self) -> None:
        partial = row(Column("published_on"), json={"published_on": "1965-08-01"})

        assert partial[Column("published_on")] == date(1965, 8, 1)

    def test_an_ad_hoc_column_without_a_field_reads_the_decoded_value(self) -> None:
        partial = row(Column("legacy"), json={"legacy": "1965-08-01"})

        assert partial[Column("legacy")] == "1965-08-01"

    def test_an_entry_the_list_did_not_ask_for_raises(self) -> None:
        partial = row(Books.id, Books.title)

        with pytest.raises(
            KeyError, match="pages was not selected; the row holds id, title"
        ):
            partial[Books.pages]

    def test_a_value_the_field_rejects_raises(self) -> None:
        partial = row(Books.id, json={"id": "seven"})

        with pytest.raises(ValidationError):
            partial[Books.id]


class AliasedRow(BaseModel):
    class_: int = Field(alias="class")


class Aliased:
    class_ = Column[AliasedRow, int]("class")
    table = Table[AliasedRow, Any, Any]("aliased", AliasedRow)


@dataclass
class DataclassRow:
    published_on: date | None


class Dataclasses:
    published_on = NullableColumn[DataclassRow, date]("published_on")
    table = Table[DataclassRow, Any, Any]("dataclasses", DataclassRow)


class ConstrainedRow(BaseModel):
    pages: Annotated[int, Field(gt=0)]


class Constrained:
    pages = Column[ConstrainedRow, int]("pages")
    table = Table[ConstrainedRow, Any, Any]("constrained", ConstrainedRow)


class TestRowTypes:
    def test_the_constraints_of_a_field_apply(self) -> None:
        partial = PartialRow(Constrained.table, (Constrained.pages,), {"pages": 0})

        with pytest.raises(ValidationError, match="greater than 0"):
            partial[Constrained.pages]

    def test_a_pydantic_alias_names_the_field(self) -> None:
        partial = PartialRow(Aliased.table, (Aliased.class_,), {"class": "3"})

        assert partial[Aliased.class_] == 3

    def test_the_annotations_of_a_dataclass_decode_its_fields(self) -> None:
        partial = PartialRow(
            Dataclasses.table,
            (Dataclasses.published_on,),
            {"published_on": "2020-01-02"},
        )

        assert partial[Dataclasses.published_on] == date(2020, 1, 2)

    def test_a_row_type_without_fields_reads_the_decoded_value(self) -> None:
        legacy = Table[dict[str, Any], Any, Any]("legacy", dict)
        partial = PartialRow(legacy, (Column("when"),), {"when": "2020-01-02"})

        assert partial[Column("when")] == "2020-01-02"


class TestToRow:
    def test_decodes_the_whole_row(self) -> None:
        json = {
            "id": 1,
            "title": "Dune",
            "isbn": None,
            "pages": 412,
            "published_on": "1965-08-01",
            "tags": ["science fiction"],
            "metadata": None,
        }
        partial = row(*Books.table.primary_key, json=json)

        assert partial.to_row() == BooksRow(
            id=1,
            title="Dune",
            pages=412,
            published_on=date(1965, 8, 1),
            tags=["science fiction"],
        )

    def test_raises_for_a_row_that_misses_a_column(self) -> None:
        with pytest.raises(ValidationError):
            row(Books.id, Books.title, json={"id": 1, "title": "Dune"}).to_row()


class TestValue:
    def test_repr_shows_the_decoded_row(self) -> None:
        assert repr(row(Books.id, json={"id": 1})) == "PartialRow({'id': 1})"

    def test_equality_compares_the_table_the_entries_and_the_row(self) -> None:
        assert row(Books.id, json={"id": 1}) == row(Books.id, json={"id": 1})
        assert row(Books.id, json={"id": 1}) != row(Books.id, json={"id": 2})
        assert row(Books.id, json={"id": 1}) != row(Books.title, json={"id": 1})

    def test_is_immutable(self) -> None:
        with pytest.raises(AttributeError):
            row(Books.id).json = {}  # pyrefly: ignore[read-only]
