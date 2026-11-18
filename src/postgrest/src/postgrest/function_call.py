from __future__ import annotations

from collections.abc import Mapping
from dataclasses import KW_ONLY, dataclass, field
from typing import Any, Literal, Never

from supabase_utils.types import JSON

from .table_request import ResultShape


@dataclass(frozen=True)
class FunctionCall[Row, Result]:
    """A call of a database function, with the Python type its result is
    read as, which `PostgrestClient.rpc` runs.

    Built with `rows()` for a function that returns rows, which can then be
    filtered, ordered and paged like the rows of a table, or with `value()`
    for one that returns a scalar, a single row or an array:

        books = (
            client.rpc(FunctionCall.rows("search_books", BooksRow, arguments={"query": "dune"}))
            .where(Books.pages.gt(300))
            .order(Books.title)
            .execute()
        )
        total = client.rpc(FunctionCall.value("count_books", int)).execute()

    `Row` is the type of a returned row, `Never` for a call built with
    `value()`, and `Result` what the call resolves to.
    """

    name: str
    """The name of the function in the database."""

    return_type: type[Any]
    """The type each returned row decodes into for a call built with
    `rows()`, or the type the whole result decodes into for one built with
    `value()`."""

    _: KW_ONLY

    shape: Literal[ResultShape.ROWS, ResultShape.VALUE]
    """`ResultShape.ROWS` for a call built with `rows()` and
    `ResultShape.VALUE` for one built with `value()`."""

    arguments: Mapping[str, JSON] = field(default_factory=dict[str, JSON])
    """The named arguments of the call."""

    schema: str | None = None
    """The schema the function lives in, or `None` to call it in the schema
    of the client."""

    read_only: bool = False
    """Whether the function only reads, see `rows()`."""

    @staticmethod
    def rows[R](
        name: str,
        row_type: type[R],
        *,
        arguments: Mapping[str, JSON] | None = None,
        schema: str | None = None,
        read_only: bool = False,
    ) -> FunctionCall[R, list[R]]:
        """A call of the function `name`, which returns a set of rows, each
        decoded into `row_type`. PostgREST answers a function that returns
        one row, not a set, with the row alone; call it with `value()`.

        `arguments` are the named arguments of the function. With
        `read_only`, the function is called with a `GET` request, in a
        read-only transaction, and retried like a select; the arguments are
        then sent as query parameters, with a list as a PostgreSQL array
        literal. When PostgREST would read an argument as something else,
        one named like an option such as `limit`, a `None`, or a value that
        starts like a filter such as `eq.x`, the call is sent as a `POST`
        instead, which is neither read-only nor retried.
        """
        return FunctionCall(
            name,
            row_type,
            shape=ResultShape.ROWS,
            arguments=arguments or {},
            schema=schema,
            read_only=read_only,
        )

    @staticmethod
    def value[V](
        name: str,
        result_type: type[V],
        *,
        arguments: Mapping[str, JSON] | None = None,
        schema: str | None = None,
        read_only: bool = False,
    ) -> FunctionCall[Never, V | None]:
        """A call of the function `name`, whose result, a scalar, a single
        row or an array, decodes into `result_type`, or into `None` when the
        function returns `NULL`.

        PostgREST answers a function that returns one row, not a set, and
        finds none with a row whose columns are all `null`, which only
        decodes into a `result_type` that allows it. Declare such a function
        `returns setof` and read it with `rows()` and `maybe_single()` to
        get `None` instead.

        See `rows()` for `arguments` and `read_only`.
        """
        return FunctionCall(
            name,
            result_type,
            shape=ResultShape.VALUE,
            arguments=arguments or {},
            schema=schema,
            read_only=read_only,
        )
