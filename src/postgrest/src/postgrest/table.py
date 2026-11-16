from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import KW_ONLY, dataclass
from functools import cache
from typing import TYPE_CHECKING, Any, Generic

from pydantic import BaseModel, TypeAdapter
from typing_extensions import TypeVar

from .column_expression import Column, ComputedField
from .utils import _row_payload, _rows_payload

if TYPE_CHECKING:
    from supabase_utils.types import JSON

Row = TypeVar("Row", default=Any)
"""The row type of the table, the one its columns and filters carry."""

Insert = TypeVar("Insert", default=Any)
"""The type of a row a table takes on an insert or an upsert, normally the
`TypedDict` the generator emits for it."""

Update = TypeVar("Update", default=Any)
"""The type of the columns a table takes on an update, normally the
`TypedDict` the generator emits for it."""


@dataclass(frozen=True)
class Table(Generic[Row, Insert, Update]):
    """A table, view or materialized view of the database, with the Python
    types its rows are read as and written with.

    Declared once, normally by the generator, as the last attribute of the
    table's namespace class, since a class body runs top to bottom and the
    primary key names the columns above it:

        class Books:
            id = Column[BooksRow, int]("id")
            title = Column[BooksRow, str]("title")
            table = Table(
                "books",
                BooksRow,
                insert_type=BooksInsert,
                update_type=BooksUpdate,
                primary_key=(id,),
                schema="public",
            )

    `Row` is the type a `select()` of every column decodes into. `Insert` and
    `Update` are the only types the write methods of a typed query accept;
    a view declares `Table[Row, Never, Never]`, which makes them uncallable.
    """

    name: str
    """The name of the table in the database."""

    row_type: type[Row]
    """The type a decoded row is validated into."""

    _: KW_ONLY

    insert_type: type[Insert] | None = None
    """The type an inserted or upserted row is validated against before it
    is sent, normally the `Insert` `TypedDict` the generator emits, or `None`
    to send rows as they are given.

    A validated row is sent by alias, so a column whose name is not a Python
    identifier, declared as `Annotated[str, Field(alias="victory road")]`,
    is written under its name in the database. A key the type does not
    declare is rejected rather than dropped.
    """

    update_type: type[Update] | None = None
    """The type the values of an update are validated against before they
    are sent, normally the `Update` `TypedDict` the generator emits, or
    `None` to send them as they are given, see `insert_type`."""

    primary_key: tuple[Column[Row, Any], ...] = ()
    """The columns that identify a row, in key order.

    Empty for a view or a table without a primary key, where nothing on the
    client can tell two rows apart.
    """

    computed_fields: tuple[ComputedField[Row, Any], ...] = ()
    """The computed fields of the table: functions whose only argument is the
    row type, which PostgREST selects like columns but leaves out of `*`, so
    a `select()` row never carries them."""

    schema: str | None = None
    """The schema the table lives in, or `None` to query it in the schema of
    the client.

    A table that carries its schema is queried in it without a `schema()`
    call on the client, so tables from several schemas can be used side by
    side on one client.
    """


def _row_adapter[Row](row_type: type[Row]) -> TypeAdapter[Row]:
    """The validator that decodes one response row into `row_type`."""
    return _cached_adapter(row_type)


def _rows_adapter[Row](row_type: type[Row]) -> TypeAdapter[list[Row]]:
    """The validator that decodes a list of response rows into `row_type`
    in one pass."""
    return _cached_adapter(list[row_type])


@cache
def _cached_adapter(decoded_type: Any) -> TypeAdapter[Any]:
    """One `TypeAdapter` per type, since building one is costly and every
    query of a table decodes into, or writes through, the same type."""
    return TypeAdapter(decoded_type)


def _insert_payload(table: Table[Any, Any, Any], rows: object, method: str) -> JSON:
    """`rows` as the payload of the insert or upsert `method` of `table`:
    validated against its `insert_type` and dumped by alias when it has one.

    Raises `ValidationError` for a row that does not validate and
    `TypeError` for a payload that is neither a row nor rows.
    """
    if table.insert_type is None:
        return _rows_payload(rows, method)
    if isinstance(rows, (Mapping, BaseModel, str, bytes)) or not isinstance(
        rows, Iterable
    ):
        return _rows_payload(_written(_row_adapter(table.insert_type), rows), method)
    given: Iterable[object] = rows
    adapter = _rows_adapter(table.insert_type)
    return _rows_payload(_written(adapter, list(given)), method)


def _update_payload(table: Table[Any, Any, Any], values: object) -> JSON:
    """`values` as the payload of an update of `table`: validated against
    its `update_type` and dumped by alias when it has one."""
    if table.update_type is None:
        return _row_payload(values, "update")
    adapter = _row_adapter(table.update_type)
    return _row_payload(_written(adapter, values), "update")


def _written(adapter: TypeAdapter[Any], given: object) -> object:
    """`given` validated by `adapter` and dumped to plain Python by alias,
    ready to be serialized.

    A row is validated by field name and by alias, so both the key of a
    generated `TypedDict` and the column name are accepted. A key the type
    does not declare fails validation, rather than being dropped, and a
    field a model leaves unset stays out, so the column gets its database
    default.
    """
    validated = adapter.validate_python(
        given, by_alias=True, by_name=True, extra="forbid"
    )
    written: object = adapter.dump_python(validated, by_alias=True, exclude_unset=True)
    return written
