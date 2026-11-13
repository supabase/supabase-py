from __future__ import annotations

from dataclasses import dataclass

from .filter import ColumnExpression, Filter, FilterOperator, Row, Value


@dataclass(frozen=True)
class _StoredColumn(ColumnExpression[Row, Value]):
    """A stored column of the table whose rows are `Row`: a `Column` when the
    database forbids `NULL`, a `NullableColumn` when it allows it."""

    name: str
    """The name of the column in the database."""

    @property
    def expression(self) -> str:
        return self.name


@dataclass(frozen=True)
class Column(_StoredColumn[Row, Value]):
    """A stored column of the table whose rows are `Row`, which the database
    does not allow to be `NULL`; a `NullableColumn` is one that it does.

    Declared once per column, normally by the generator, as a class attribute
    of the table's namespace class:

        class Books:
            id = Column[BooksRow, int]("id")
            title = Column[BooksRow, str]("title")
            due_date = NullableColumn[BooksRow, datetime]("due_date")

    `Value` is the Python type of the column, which every filter takes as its
    operand. An ad hoc column needs no generated code: `Column("deleted_at")`
    leaves `Row` and `Value` as `Any`.
    """


@dataclass(frozen=True)
class NullableColumn(_StoredColumn[Row, Value]):
    """A stored column the database allows to be `NULL`, see `Column`.

    `Value` stays the type of a present value, `NullableColumn[BooksRow, str]`
    for a nullable `text` column; `NULL` is tested with `is_null()`.
    """

    def is_null(self) -> Filter[Row]:
        """Only rows where this column is SQL `NULL`.

        There is no `is_not_null()`; negate instead: `~Books.due_date.is_null()`
        renders `due_date=not.is.null`.
        """
        return self._compare(FilterOperator.IS, None)


@dataclass(frozen=True)
class ComputedField(ColumnExpression[Row, Value]):
    """A computed field of the table whose rows are `Row`: a function whose
    only argument is the table's row type, which PostgREST exposes like a
    column.

    It filters like a column, and has `is_null()` whatever its declared type,
    since the function can return `NULL`. `Value` is the Python type of a
    present value.

    A `select_only()` reads the field through `value_type`, so a `date`
    field comes back as a `date`. Without it the value is the decoded JSON,
    which is right for `str`, `int`, `float`, `bool` and JSON values. `Row`
    cannot decode the field, since a `select()` of every column never
    carries it; the generator gives `value_type` for every field whose type
    differs from its JSON form.
    """

    name: str
    """The name of the function in the database, which is also the name the
    field is selected by."""

    value_type: type[Value] | None = None
    """The type a present value is decoded into when the field is read from
    a `PartialRow`, or `None` for the decoded JSON."""

    @property
    def expression(self) -> str:
        return self.name

    def is_null(self) -> Filter[Row]:
        """Only rows where this field is SQL `NULL`.

        There is no `is_not_null()`; negate instead: `~Users.full_name.is_null()`
        renders `full_name=not.is.null`.
        """
        return self._compare(FilterOperator.IS, None)
