from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from functools import cache, cached_property
from typing import TYPE_CHECKING, Annotated, Any, get_type_hints, overload

from pydantic import BaseModel, TypeAdapter
from supabase_utils.types import JSON

from .column_expression import ComputedField
from .filter import DerivedExpression, Expression, JsonPath
from .table import Table, _cached_adapter, _row_adapter

if TYPE_CHECKING:
    from .column_expression import Column, NullableColumn
    from .filter import ColumnExpression


@dataclass(frozen=True, repr=False)
class PartialRow[Row]:
    """A row of a `select_only()` list, read through the entries of the list.

    An entry types the read, so `row[Books.title]` is a `str`, a
    `NullableColumn` and a `ComputedField` read as their value or `None`, and
    an entry of another table is a type error:

        books = (
            client.table(Books.table)
            .select_only([Books.id, Books.title, Books.published_on])
            .execute()
        )
        for book in books:
            title: str = book[Books.title]
            published_on: date | None = book[Books.published_on]

    A value is validated against the field of `Row` the entry is named
    after, its type and the constraints of its `Field`, so a `date` column
    reads as a `date` as it does from `select()`; the validators and the
    config of the model itself run in `select()` and `to_row()` only. A
    computed field, which `Row` never carries, decodes through the
    `value_type` it was declared with, and as the decoded JSON without one,
    as does an ad hoc `Column` that names no field of `Row`. A JSON path
    reads as the decoded JSON, and a `DerivedExpression` as described by its
    `value_type`; both read as their value or `None`, like an aggregate of
    no rows:

        total = (
            client.table(Books.table)
            .select_only([Books.pages.sum()])
            .single()
            .execute()
        )
        pages: int | None = total[Books.pages.sum()]

    Reading an entry the list did not ask for raises `KeyError`, instead of
    returning `None` as a missing key would.
    """

    table: Table[Row, Any, Any]
    """The table the row belongs to, whose `Row` type decodes the values."""

    columns: tuple[Expression[Row, Any], ...]
    """The entries of the `select` list this row answers."""

    json: Mapping[str, JSON]
    """The row as decoded from the response, keyed by the `response_key` of
    the entries."""

    @overload
    def __getitem__[Value](self, entry: Column[Row, Value]) -> Value: ...
    @overload
    def __getitem__[Value](self, entry: NullableColumn[Row, Value]) -> Value | None: ...
    @overload
    def __getitem__[Value](self, entry: ComputedField[Row, Value]) -> Value | None: ...
    @overload
    def __getitem__[Value](
        self, entry: ColumnExpression[Row, Value]
    ) -> Value | None: ...
    @overload
    def __getitem__[Value](self, entry: Expression[Row, Value]) -> Value | None: ...
    def __getitem__(self, entry: Expression[Row, Any]) -> Any:
        """The value of `entry` in this row, see the class."""
        key = entry.response_key
        if key not in self._keys:
            selected = ", ".join(column.response_key for column in self.columns)
            raise KeyError(f"{key} was not selected; the row holds {selected}")
        value = self.json.get(key)
        if value is None:
            return None
        adapter = _adapter(entry, self.table.row_type)
        return value if adapter is None else adapter.validate_python(value)

    def to_row(self) -> Row:
        """The row as the full `Row` of its table.

        It decodes the row the way `select()` does, so it raises
        `pydantic.ValidationError` when the list left out a column `Row`
        requires.
        """
        return _row_adapter(self.table.row_type).validate_python(self.json)

    def __repr__(self) -> str:
        return f"PartialRow({dict(self.json)!r})"

    @cached_property
    def _keys(self) -> frozenset[str]:
        return frozenset(column.response_key for column in self.columns)


_KEEPS_SOURCE_TYPE = frozenset({".min()", ".max()"})
"""The derivations whose value is decoded as the expression they apply to."""

_KEEPS_UNCONSTRAINED_SOURCE_TYPE = frozenset({".sum()"})
"""The derivations whose value is decoded as the expression they apply to,
without the constraints of its `Field`, which a sum can exceed."""


def _adapter(
    entry: Expression[Any, Any], row_type: Any, *, constrained: bool = True
) -> TypeAdapter[Any] | None:
    """The validator of a value of `entry`: its `value_type` when it has
    one, the validator of what an aggregate keeping its type applies to,
    nothing for a JSON path, and otherwise the field of `row_type` the entry
    is named after."""
    match entry:
        case (
            ComputedField(value_type=value_type)
            | DerivedExpression(value_type=value_type)
        ) if value_type is not None:
            return _cached_adapter(value_type)
        case DerivedExpression(source=source, derivation=derivation) if (
            source is not None
        ):
            if derivation in _KEEPS_SOURCE_TYPE:
                return _adapter(source, row_type, constrained=constrained)
            if derivation in _KEEPS_UNCONSTRAINED_SOURCE_TYPE:
                return _adapter(source, row_type, constrained=False)
            return None
        case DerivedExpression() | JsonPath():
            return None
        case _:
            return _field_adapter(row_type, entry.expression, constrained)


@cache
def _field_adapter(
    row_type: Any, name: str, constrained: bool
) -> TypeAdapter[Any] | None:
    """The validator of the field of `row_type` that a response row carries
    under `name`, with or without the constraints of its `Field`, or `None`
    when it has no such field."""
    annotation = _field_annotations(row_type, constrained).get(name)
    return None if annotation is None else TypeAdapter(annotation)


@cache
def _field_annotations(row_type: Any, constrained: bool) -> Mapping[str, Any]:
    """The declared type of every field of `row_type`, with or without the
    constraints of its `Field`, by the key the field is read from a response
    row under: the alias of a pydantic field that has one, and the attribute
    name otherwise."""
    if isinstance(row_type, type) and issubclass(row_type, BaseModel):
        return {
            field.alias or name: (
                _constrained(field.annotation, field.metadata)
                if constrained
                else field.annotation
            )
            for name, field in row_type.model_fields.items()
            if field.annotation is not None
        }
    try:
        return get_type_hints(row_type, include_extras=constrained)
    except Exception:
        return {}


def _constrained(annotation: Any, metadata: list[Any]) -> Any:
    return Annotated[annotation, *metadata] if metadata else annotation
