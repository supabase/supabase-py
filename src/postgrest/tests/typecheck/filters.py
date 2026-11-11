"""The column expressions and the filter tree as the type checkers see them.

`test_typecheck.py` runs mypy, pyright and pyrefly on this file and asserts
that each reports an error on every line marked `# error:` and on no other
line. The pyrefly check of the package excludes this directory.
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from postgrest import Column, ComputedField, Filter, NullableColumn, TextSearchType

if TYPE_CHECKING:
    from postgrest import ColumnExpression, Comparison, FilterOperator


class BooksRow:
    pass


class AuthorsRow:
    pass


class Books:
    id = Column[BooksRow, int]("id")
    title = Column[BooksRow, str]("title")
    is_done = Column[BooksRow, bool]("is_done")
    published_on = NullableColumn[BooksRow, datetime]("published_on")
    is_urgent = NullableColumn[BooksRow, bool]("is_urgent")
    full_title = ComputedField[BooksRow, str]("full_title")


class Authors:
    id = Column[AuthorsRow, int]("id")


by_id: Filter[BooksRow] = Books.id.eq(7)
composed: Filter[BooksRow] = (Books.id.gt(1) & Books.title.neq("x")) | ~Books.id.lt(3)
nullable: Filter[BooksRow] = ~Books.published_on.is_null() & Books.is_urgent.is_true()
in_list: Filter[BooksRow] = Books.id.in_([1, 2]) & Books.title.in_(("a", "b"))
boolean: Filter[BooksRow] = Books.is_done.is_true() | Books.is_done.is_false()
computed: Filter[BooksRow] = Books.full_title.is_null() & Books.full_title.eq("x")
searched: Filter[BooksRow] = Books.title.text_search("py", type=TextSearchType.PLAIN)
configured: Filter[BooksRow] = Books.title.text_search("py", config="english")
raw: Filter[BooksRow] = Books.title.raw("someop.value") & Filter.raw("x", "eq.1")
pinned_raw: Filter[BooksRow] = Filter[BooksRow].raw("cost::text", "eq.10")

ad_hoc: Filter[Any] = NullableColumn("deleted_at").is_null() & Column("id").eq("7")
mixed: Filter[BooksRow] = Books.id.eq(1) & Column("legacy").eq(2)

comparison: Comparison[BooksRow] | None = (~Books.id.eq(7)).comparison
if comparison is not None:
    column: ColumnExpression[BooksRow, Any] = comparison.column
    operator: FilterOperator = comparison.operator
    value: object = comparison.value
    negated: bool = comparison.negated

wrong_operand: Filter[BooksRow] = Books.id.eq("seven")  # error: str is not int
wrong_bound: Filter[BooksRow] = Books.title.gt(7)  # error: int is not str
wrong_member: Filter[BooksRow] = Books.id.in_(["seven"])  # error: str is not int
null_operand: Filter[BooksRow] = Books.published_on.eq(None)  # error: use is_null()

other_table: Filter[BooksRow] = Authors.id.eq(1)  # error: AuthorsRow is not BooksRow
mixed_and: Filter[BooksRow] = Books.id.eq(1) & Authors.id.eq(1)  # error: other table
mixed_or: Filter[BooksRow] = Books.id.eq(1) | Authors.id.eq(1)  # error: other table

not_nullable: Filter[BooksRow] = Books.id.is_null()  # error: Column has no is_null()
not_boolean: Filter[BooksRow] = Books.title.is_true()  # error: str is not bool
not_boolean_either: Filter[BooksRow] = Books.id.is_false()  # error: int is not bool
