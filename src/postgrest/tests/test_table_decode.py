from datetime import date

import pytest
from pydantic import ValidationError

from tests.typed_schema import Books, BooksRow

RECORD = {
    "id": 1,
    "title": "Dune",
    "isbn": None,
    "pages": 412,
    "published_on": "1965-08-01",
    "tags": ["sf"],
    "metadata": None,
}


class TestDecodeRow:
    def test_a_full_record_decodes_into_the_row_type(self) -> None:
        assert Books.table.decode_row(RECORD) == BooksRow(
            id=1,
            title="Dune",
            pages=412,
            published_on=date(1965, 8, 1),
            tags=["sf"],
        )

    def test_a_record_without_a_required_column_raises(self) -> None:
        with pytest.raises(ValidationError):
            Books.table.decode_row({"id": 1})


class TestDecodePartial:
    def test_the_held_columns_read_through_the_row_type(self) -> None:
        partial = Books.table.decode_partial({"id": 1, "published_on": "1965-08-01"})

        assert partial[Books.id] == 1
        assert partial[Books.published_on] == date(1965, 8, 1)

    def test_a_primary_key_only_record_reads_its_key(self) -> None:
        partial = Books.table.decode_partial({"id": 7})

        assert partial[Books.id] == 7
        assert partial.to_dict() == {"id": 7}

    def test_a_column_the_record_does_not_hold_raises(self) -> None:
        partial = Books.table.decode_partial({"id": 7})

        with pytest.raises(KeyError, match="title was not selected"):
            partial[Books.title]

    def test_a_held_null_reads_none(self) -> None:
        partial = Books.table.decode_partial({"id": 7, "isbn": None})

        assert partial[Books.isbn] is None

    def test_the_record_is_copied(self) -> None:
        record = {"id": 7}
        partial = Books.table.decode_partial(record)
        record["id"] = 8

        assert partial[Books.id] == 7
