from __future__ import annotations

from dataclasses import KW_ONLY, dataclass
from typing import Any, Generic

from typing_extensions import TypeVar

from .column_expression import Column, ComputedField

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
            table = Table[BooksRow, BooksInsert, BooksUpdate](
                "books", BooksRow, primary_key=(id,), schema="public"
            )

    `Row` is the type a `select()` of every column decodes into. `Insert` and
    `Update` are the only types the write methods of a typed query accept;
    a view declares `Table[Row, Never, Never]`, which makes them uncallable.
    All three have to be spelled out, since nothing in the arguments can
    infer the write types.
    """

    name: str
    """The name of the table in the database."""

    row_type: type[Row]
    """The type a decoded row is validated into."""

    _: KW_ONLY

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
