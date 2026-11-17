from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from decimal import Decimal
from functools import cache, cached_property, reduce
from operator import or_
from types import UnionType
from typing import (
    TYPE_CHECKING,
    Annotated,
    Any,
    Union,
    get_args,
    get_origin,
    get_type_hints,
    overload,
)

from pydantic import BaseModel, TypeAdapter
from supabase_utils.types import JSON

from .column_expression import ComputedField
from .filter import DerivedExpression, Expression, JsonPath
from .table import Table, _row_adapter

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
        requires. JSON paths, casts and aggregates are left out of it.
        """
        derived = {
            column.response_key
            for column in self.columns
            if isinstance(column, (JsonPath, DerivedExpression))
        }
        row = {key: value for key, value in self.json.items() if key not in derived}
        return _row_adapter(self.table.row_type).validate_python(row)

    def __repr__(self) -> str:
        return f"PartialRow({dict(self.json)!r})"

    @cached_property
    def _keys(self) -> frozenset[str]:
        return frozenset(column.response_key for column in self.columns)


@cache
def _adapter(entry: Expression[Any, Any], row_type: Any) -> TypeAdapter[Any] | None:
    """The validator of a value of `entry`, or `None` to read the decoded
    JSON, see `_annotation`."""
    annotation = _annotation(entry, row_type)
    return None if annotation is None else TypeAdapter(annotation)


def _annotation(entry: Expression[Any, Any], row_type: Any) -> Any:
    """The type a value of `entry` is decoded into, or `None` for the decoded
    JSON: its `value_type` when it has one; for `min()` and `max()` the type
    of what they apply to, for `sum()` that type without the constraints of
    its `Field`, which a sum can exceed, and for `avg()` a `Decimal` over a
    `Decimal` and a `float` otherwise; nothing for a JSON path; and the
    field of `row_type` a column is named after."""
    match entry:
        case (
            ComputedField(value_type=value_type)
            | DerivedExpression(value_type=value_type)
        ) if value_type is not None:
            return value_type
        case DerivedExpression(source=source, derivation=derivation) if (
            source is not None
        ):
            source_type = _annotation(source, row_type)
            match derivation:
                case ".min()" | ".max()":
                    return source_type
                case ".sum()":
                    return _without_constraints(source_type)
                case ".avg()":
                    return Decimal if _holds(source_type, Decimal) else float
                case _:
                    return None
        case DerivedExpression() | JsonPath():
            return None
        case _:
            return _field_annotations(row_type).get(entry.expression)


def _without_constraints(annotation: Any) -> Any:
    """`annotation` with every `Annotated` in it, and so every constraint of
    a `Field`, removed."""
    origin: object = get_origin(annotation)
    if origin is Annotated:
        return _without_constraints(get_args(annotation)[0])
    if origin is Union or origin is UnionType:
        return reduce(or_, map(_without_constraints, get_args(annotation)))
    return annotation


def _holds(annotation: Any, wanted: type) -> bool:
    """Whether `wanted` is `annotation` or appears in it."""
    return annotation is wanted or any(
        _holds(argument, wanted) for argument in get_args(annotation)
    )


@cache
def _field_annotations(row_type: Any) -> Mapping[str, Any]:
    """The declared type of every field of `row_type`, with the constraints
    of its `Field`, by the key the field is read from a response row under:
    the alias of a pydantic field that has one, and the attribute name
    otherwise."""
    if isinstance(row_type, type) and issubclass(row_type, BaseModel):
        return {
            field.alias or name: _constrained(field.annotation, field.metadata)
            for name, field in row_type.model_fields.items()
            if field.annotation is not None
        }
    try:
        return get_type_hints(row_type, include_extras=True)
    except Exception:
        return {}


def _constrained(annotation: Any, metadata: list[Any]) -> Any:
    return Annotated[annotation, *metadata] if metadata else annotation
