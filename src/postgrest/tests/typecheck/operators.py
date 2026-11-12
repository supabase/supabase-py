"""The text, array, JSON and range operators as the type checkers see them.

`test_typecheck.py` runs mypy, pyright and pyrefly on this file and asserts
that each reports an error on every line marked `# error:` and on no other
line. The pyrefly check of the package excludes this directory.
"""

from __future__ import annotations

from datetime import UTC, date, datetime
from typing import Any

from pydantic import JsonValue

from postgrest import Column, ComputedField, Filter, NullableColumn, Range


class BooksRow:
    pass


class Books:
    id = Column[BooksRow, int]("id")
    title = Column[BooksRow, str]("title")
    subtitle = NullableColumn[BooksRow, str]("subtitle")
    full_title = ComputedField[BooksRow, str]("full_title")
    tags = Column[BooksRow, list[str]]("tags")
    ratings = NullableColumn[BooksRow, list[int]]("ratings")
    metadata = Column[BooksRow, JsonValue]("metadata")
    extra = NullableColumn[BooksRow, JsonValue]("extra")
    pages = Column[BooksRow, Range[int]]("pages")
    on_sale = NullableColumn[BooksRow, Range[date]]("on_sale")
    available = Column[BooksRow, Range[datetime]]("available")


patterns: Filter[BooksRow] = (
    Books.title.like("%py%")
    & Books.subtitle.ilike("%PY%")
    & Books.full_title.match_regex("^py")
    & Books.title.imatch_regex("^PY")
)
quantified: Filter[BooksRow] = (
    Books.title.like_all_of(["%a%", "%b%"])
    & Books.title.like_any_of(("%a%", "%b%"))
    & Books.subtitle.ilike_all_of([])
    & Books.full_title.ilike_any_of({"%a%"})
)
arrays: Filter[BooksRow] = (
    Books.tags.contains(["python"])
    & Books.tags.contained_by(("python", "typing"))
    & Books.tags.overlaps(["python", None])
    & Books.ratings.contains([5])
)
json: Filter[BooksRow] = (
    Books.metadata.contains({"a": 1})
    & Books.metadata.contained_by({"a": 1, "b": [2, "x"]})
    & Books.extra.contains({"nested": {"a": None}})
)
ranges: Filter[BooksRow] = (
    Books.pages.contains(Range(1, 10))
    & Books.pages.contains(5)
    & Books.pages.contained_by(Range(None, 100, "(]"))
    & Books.pages.overlaps(Range(5, 15))
    & Books.pages.range_lt(Range(100, None))
    & Books.pages.range_gt(Range(0, 1))
    & Books.on_sale.range_gte(Range(date(2024, 1, 1), date(2024, 2, 1)))
    & Books.on_sale.range_lte(Range(None, date(2024, 2, 1)))
    & Books.available.range_adjacent(Range(datetime(2024, 1, 1, tzinfo=UTC), None))
    & Books.available.eq(
        Range(datetime(2024, 1, 1, tzinfo=UTC), datetime(2024, 2, 1, tzinfo=UTC), "[]")
    )
)
ad_hoc: Filter[Any] = (
    Column("title").like("%a%")
    & Column("tags").contains(["a"])
    & Column("metadata").contains({"a": 1})
    & Column("pages").range_lt(Range(1, 2))
    & NullableColumn("pages").overlaps(Range(1, 2))
)

not_text: Filter[BooksRow] = Books.id.like("%1%")  # error: int is not str
not_text_either: Filter[BooksRow] = Books.tags.ilike("%a%")  # error: list is not str
not_text_regex: Filter[BooksRow] = Books.id.match_regex("1")  # error: int is not str
not_text_all: Filter[BooksRow] = Books.id.like_all_of(["1"])  # error: int is not str
not_patterns: Filter[BooksRow] = Books.title.like_any_of([1])  # error: int is not str

not_array: Filter[BooksRow] = Books.id.contains([1])  # error: int is not an array
not_array_either: Filter[BooksRow] = Books.title.overlaps(["a"])  # error: str
wrong_element: Filter[BooksRow] = Books.tags.contains([1])  # error: int is not str
wrong_element_either: Filter[BooksRow] = Books.tags.contained_by([1])  # error: int

json_array: Filter[BooksRow] = Books.metadata.contains([1])  # error: not an object
json_scalar: Filter[BooksRow] = Books.metadata.contained_by("a")  # error: not an object
no_json_overlap: Filter[BooksRow] = Books.metadata.overlaps({"a": 1})  # error: no &&

not_range: Filter[BooksRow] = Books.title.range_lt(Range(1, 2))  # error: str
not_range_either: Filter[BooksRow] = Books.id.range_adjacent(Range(1, 2))  # error: int
not_range_array: Filter[BooksRow] = Books.tags.range_gt(Range(1, 2))  # error: list
wrong_bound: Filter[BooksRow] = Books.pages.range_lt(Range("a", "b"))  # error: str
wrong_bound_date: Filter[BooksRow] = Books.on_sale.overlaps(Range(1, 2))  # error: int
wrong_element_bound: Filter[BooksRow] = Books.pages.contains("5")  # error: str
range_literal: Filter[BooksRow] = Books.pages.range_lt("[1,2)")  # error: not a Range
wrong_bounds: Range[int] = Range(1, 2, "[>")  # error: not a bounds form
