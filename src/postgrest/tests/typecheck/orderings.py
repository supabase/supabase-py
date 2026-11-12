"""The orderings as the type checkers see them.

`test_typecheck.py` runs mypy, pyright and pyrefly on this file and asserts
that each reports an error on every line marked `# error:` and on no other
line. The pyrefly check of the package excludes this directory.
"""

from __future__ import annotations

from datetime import datetime
from typing import Any

from postgrest import Column, ComputedField, NullableColumn, Ordering


class BooksRow:
    pass


class AuthorsRow:
    pass


class Books:
    id = Column[BooksRow, int]("id")
    title = Column[BooksRow, str]("title")
    published_on = NullableColumn[BooksRow, datetime]("published_on")
    full_title = ComputedField[BooksRow, str]("full_title")


class Authors:
    name = Column[AuthorsRow, str]("name")


bare: Ordering[BooksRow] = Books.title
ascending: Ordering[BooksRow] = Books.title.asc()
descending: Ordering[BooksRow] = Books.published_on.desc().nulls_last()
placed: Ordering[BooksRow] = Books.published_on.nulls_first()
placed_then_directed: Ordering[BooksRow] = Books.published_on.nulls_first().asc()
computed: Ordering[BooksRow] = Books.full_title.desc()
keys: list[str] = [bare.order_key, ascending.order_key, descending.order_key]

ad_hoc: Ordering[Any] = Column("created_at").desc()
ad_hoc_bare: Ordering[Any] = NullableColumn("deleted_at")

other_table: Ordering[BooksRow] = Authors.name  # error: AuthorsRow is not BooksRow
other_table_directed: Ordering[BooksRow] = Authors.name.asc()  # error: other table
not_an_ordering: Ordering[BooksRow] = Books.title.eq("x")  # error: a Filter
