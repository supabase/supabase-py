from __future__ import annotations

from collections.abc import Awaitable, Callable, Iterable, Mapping, Sequence
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Any, Literal, Never, Self, overload

from pydantic import TypeAdapter
from pydantic_core import PydanticSerializationError, to_jsonable_python
from supabase_utils.types import JSON, JSONParser

from .partial_row import PartialRow
from .request_builder import JSONDictParser, JSONListParser
from .table import Table, _rows_adapter
from .table_executor import _WRITES, AsyncTableExecutor, TableExecutor
from .table_request import (
    ExplainOptions,
    ResultShape,
    TableOperation,
    TableRequest,
    TableResult,
)
from .types import CountMethod

if TYPE_CHECKING:
    from supabase_utils.http.retry import RetryPolicy

    from .column_expression import Column, NullableColumn
    from .filter import ColumnExpression, Filter, Ordering


@dataclass(frozen=True)
class CountedResponse[T]:
    """The result of a query that asked for the row count next to its data,
    see `TypedTransformBuilder.count`."""

    data: T
    """What the query resolves to without the count."""

    count: int
    """The number of rows the query matches, which `limit()` and `range()`
    do not reduce."""


@dataclass(frozen=True)
class TypedBuilder[Executor: (TableExecutor, AsyncTableExecutor), T]:
    """A typed request that is ready to run, resolving to `T`.

    The methods of the typed query builders collect a `TableRequest` without
    rendering it; `execute()` hands it to the `TableExecutor` of the client,
    waits for the `TableResult` and converts it into `T`. Every method returns
    a copy, so a builder can be kept and branched from.

    `Executor` is the executor protocol of the client: `execute()` returns
    `T` on a `SyncPostgrestClient` and an awaitable of `T` on an
    `AsyncPostgrestClient`.
    """

    request: TableRequest
    """The request `execute()` runs, as collected so far."""

    executor: Executor
    """The executor that runs it, normally the HTTP executor of the client."""

    _convert: Callable[[TableResult], T] = field(repr=False, compare=False)

    def _with(self, **changes: Any) -> Self:
        return replace(self, request=replace(self.request, **changes))

    def _with_options(self, **changes: Any) -> Self:
        return self._with(options=replace(self.request.options, **changes))

    def retry(self, policy: RetryPolicy | bool) -> Self:
        """Decide how this query is retried when a request of it fails in a
        way worth repeating, instead of leaving it to the `RetryPolicy` of the
        client.

        `False` never retries it. `True` retries it with the policy of the
        client, and a `RetryPolicy` with that policy instead, both even when
        it is not a GET or HEAD request, which opts in a write that is safe
        to send twice.
        """
        return self._with_options(retry=policy)

    def request_timeout(self, seconds: float) -> Self:
        """Fail with `RequestTimeoutError` once a request of this query goes
        `seconds` without progress, overriding the timeout of the client."""
        return self._with_options(timeout=seconds)

    @overload
    def execute(self: TypedBuilder[TableExecutor, T]) -> T: ...
    @overload
    def execute(self: TypedBuilder[AsyncTableExecutor, T]) -> Awaitable[T]: ...
    def execute(self: TypedBuilder[Any, T]) -> T | Awaitable[T]:
        """Run the request and convert its result.

        Raises `ValueError` for a request the executor cannot send as it is,
        `APIError` for an answer that is not a success, and
        `pydantic.ValidationError` for rows that do not decode into the row
        type of the table.
        """
        result = self.executor.execute(self.request)
        if isinstance(result, TableResult):
            return self._convert(result)
        return _converted(result, self._convert)


async def _converted[T](
    result: Awaitable[TableResult], convert: Callable[[TableResult], T]
) -> T:
    return convert(await result)


@dataclass(frozen=True)
class TypedTransformBuilder[Executor: (TableExecutor, AsyncTableExecutor), Row, T](
    TypedBuilder[Executor, T]
):
    """The typed counterpart of the select, mutation and shape methods of the
    string builders.

    `Row` is the row type of the table and `T` what the request resolves to.
    The sort keys, the row window and the shape of the result are set here;
    `where()` lives on the `TypedFilterBuilder` the query starts as, so a
    filter comes before a shape such as `csv()`.
    """

    def select(self) -> TypedTransformBuilder[Executor, Row, list[Row]]:
        """Return the rows a write affected, decoded into `Row`:

            books = client.table(Books.table).insert(row).select().execute()

        Without it a write resolves to `None`. See `select_only()` to return
        some columns only.
        """
        request = replace(
            self.request, columns=(), shape=ResultShape.ROWS, returning=True
        )
        return TypedTransformBuilder(request, self.executor, _rows(self.request.table))

    def select_only(
        self, columns: Iterable[ColumnExpression[Row, Any]]
    ) -> TypedTransformBuilder[Executor, Row, list[PartialRow[Row]]]:
        """Return `columns` of the rows a write affected, as `PartialRow`s
        read through the same entries:

            rows = (
                client.table(Books.table)
                .insert(row)
                .select_only([Books.id])
                .execute()
            )
            book_id = rows[0][Books.id]

        See `TypedQueryBuilder.select_only` for `columns`.
        """
        selected = _selected(columns)
        request = replace(
            self.request, columns=selected, shape=ResultShape.ROWS, returning=True
        )
        convert = _partial_rows(self.request.table, selected)
        return TypedTransformBuilder(request, self.executor, convert)

    def order(self, ordering: Ordering[Row]) -> Self:
        """Sort the rows by `ordering`, a column with a direction and a null
        placement when they matter:

            .order(Books.title)                        # order=title
            .order(Books.priority.desc())              # order=priority.desc
            .order(Books.due_date.asc().nulls_first())  # order=due_date.asc.nullsfirst

        Repeated calls append, so the second key breaks ties in the first.
        """
        return self._with(orderings=(*self.request.orderings, ordering))

    def limit(self, count: int) -> Self:
        """Return at most `count` rows."""
        return self._with(limit=count)

    def range(self, start: int, end: int) -> Self:
        """Return the rows from index `start` to index `end`, both included,
        as the string builder's `range()` does.

        Raises `ValueError` when `end` is less than `start`.
        """
        if end < start:
            raise ValueError(
                f"range() needs end ({end}) to be at least start ({start})"
            )
        return self._with(offset=start, limit=end - start + 1)

    def strip_nulls(self) -> Self:
        """Leave the `NULL` values out of the returned rows, with the
        `nulls=stripped` variant of the `Accept` header.

        Only available in PostgREST v11.2+. A `select()` then decodes rows
        with keys missing, so `Row` needs a default for every field that can
        be `NULL`; a `select_only()` reads a stripped column as `None`. It
        cannot be combined with `csv()`, `geojson()` or `explain()`.
        """
        return self._with(strip_nulls=True)

    def dry_run(self) -> Self:
        """Run the request and roll the transaction back, so that nothing is
        persisted while the result is what it would have been:

            book = (
                client.table(Books.table)
                .insert(row)
                .select()
                .single()
                .dry_run()
                .execute()
            )

        PostgREST rolls back only when its `db-tx-end` setting allows the
        override; `execute()` raises `APIError` when the response shows that
        it committed instead.
        """
        return self._with(dry_run=True)

    def max_affected(self, value: int) -> Self:
        """Fail the request when it would affect more than `value` rows.

        Only available in PostgREST v13+ and only for an update or a delete.
        """
        return self._with(max_affected=value)

    def csv[Element](
        self: TypedTransformBuilder[Executor, Row, list[Element]],
    ) -> TypedTransformBuilder[Executor, Row, str]:
        """Resolve to the rows rendered as csv text.

        It applies to a query that resolves to a list, so a write needs
        `select()` first.
        """
        request = replace(self.request, shape=ResultShape.CSV)
        return TypedTransformBuilder(request, self.executor, _text)

    def head(self) -> TypedBuilder[Executor, None]:
        """Send a `HEAD` request, which carries no rows back, and resolve to
        `None`. See `TypedQueryBuilder.count` to count rows without reading
        them.

        Raises `ValueError` after an insert, upsert, update or delete, which
        a `HEAD` request cannot perform.
        """
        if self.request.operation in _WRITES:
            raise ValueError(
                f"head() applies to a select, not to the {self.request.operation}"
            )
        request = replace(self.request, shape=ResultShape.HEAD)
        return TypedBuilder(request, self.executor, _none)

    def geojson[Element](
        self: TypedTransformBuilder[Executor, Row, list[Element]],
    ) -> TypedBuilder[Executor, dict[str, JSON]]:
        """Resolve to the rows as one GeoJSON `FeatureCollection`, which
        needs the PostGIS extension.

        It applies to a query that resolves to a list, so a write needs
        `select()` first.
        """
        request = replace(self.request, shape=ResultShape.GEOJSON)
        return TypedBuilder(request, self.executor, _object)

    @overload
    def explain(
        self,
        *,
        analyze: bool = ...,
        verbose: bool = ...,
        settings: bool = ...,
        buffers: bool = ...,
        wal: bool = ...,
        format: Literal["text"] = ...,
    ) -> TypedBuilder[Executor, str]: ...
    @overload
    def explain(
        self,
        *,
        analyze: bool = ...,
        verbose: bool = ...,
        settings: bool = ...,
        buffers: bool = ...,
        wal: bool = ...,
        format: Literal["json"],
    ) -> TypedBuilder[Executor, JSON]: ...
    def explain(
        self,
        *,
        analyze: bool = False,
        verbose: bool = False,
        settings: bool = False,
        buffers: bool = False,
        wal: bool = False,
        format: Literal["text", "json"] = "text",
    ) -> TypedBuilder[Executor, str] | TypedBuilder[Executor, JSON]:
        """Resolve to the query plan of the request instead of its rows, as
        text or, with `format="json"`, as decoded JSON.

        The options are the ones of PostgreSQL's `EXPLAIN`. PostgREST only
        answers when its `db-plan-enabled` setting is on.
        """
        options = ExplainOptions(
            analyze=analyze,
            verbose=verbose,
            settings=settings,
            buffers=buffers,
            wal=wal,
            format=format,
        )
        request = replace(self.request, shape=ResultShape.EXPLAIN, explain=options)
        if format == "text":
            return TypedBuilder(request, self.executor, _text)
        return TypedBuilder(request, self.executor, _value)

    def count(
        self, method: CountMethod = CountMethod.exact
    ) -> TypedBuilder[Executor, CountedResponse[T]]:
        """Ask for the number of rows the request matches next to its data:

            response = client.table(Books.table).select().count().execute()
            books: list[BooksRow] = response.data
            total: int = response.count

        `method` is how PostgREST counts; `limit()` and `range()` do not
        reduce the count. See `TypedQueryBuilder.count` to count without
        reading rows.
        """
        convert = self._convert

        def counted(result: TableResult) -> CountedResponse[T]:
            return CountedResponse(convert(result), _count(result))

        request = replace(self.request, count=method)
        return TypedBuilder(request, self.executor, counted)

    def single[Element](
        self: TypedTransformBuilder[Executor, Row, list[Element]],
    ) -> TypedTransformBuilder[Executor, Row, Element]:
        """Resolve to the one row of the result instead of a list of rows.

        PostgREST answers with an error when the result holds any other
        number of rows. It applies to a query that resolves to a list, so a
        write needs `select()` first.
        """
        request = replace(self.request, shape=ResultShape.SINGLE)
        return TypedTransformBuilder(request, self.executor, _one(self._convert))

    def maybe_single[Element](
        self: TypedTransformBuilder[Executor, Row, list[Element]],
    ) -> TypedTransformBuilder[Executor, Row, Element | None]:
        """Resolve to the one row of the result, or `None` when it is empty.

        `execute()` raises `APIError` when the result holds more than one
        row. It applies to a query that resolves to a list, so a write needs
        `select()` first.
        """
        request = replace(self.request, shape=ResultShape.MAYBE_SINGLE)
        return TypedTransformBuilder(request, self.executor, _maybe_one(self._convert))


@dataclass(frozen=True)
class TypedFilterBuilder[Executor: (TableExecutor, AsyncTableExecutor), Row, T](
    TypedTransformBuilder[Executor, Row, T]
):
    """A typed query that still takes filters, see `where()`."""

    def where(self, filter: Filter[Row]) -> Self:
        """Only the rows satisfying `filter`, built from the operator methods
        of the columns and composed with `&`, `|` and `~`:

            books = (
                client.table(Books.table)
                .select()
                .where((Books.is_done.eq(False) & Books.priority.gt(3)) | Books.id.eq(7))
                .execute()
            )

        A filter is a value, so it can be assembled before the query:

            filter = Books.is_done.eq(False)
            if priority is not None:
                filter = filter & Books.priority.gte(priority)

        Repeated calls combine with `&`. A filter on another table is a type
        error.
        """
        return self._with(filter=_and_filter(self.request.filter, filter))


@dataclass(frozen=True)
class TypedCountBuilder[Executor: (TableExecutor, AsyncTableExecutor), Row](
    TypedBuilder[Executor, int]
):
    """A count of the rows of a table, resolving to the count, see
    `TypedQueryBuilder.count`.

    The rows to count are narrowed with `where()`. A count reads no rows, so
    there is nothing to order, limit or reshape.
    """

    def where(self, filter: Filter[Row]) -> Self:
        """Only count the rows satisfying `filter`, see
        `TypedFilterBuilder.where`. Repeated calls combine with `&`."""
        return self._with(filter=_and_filter(self.request.filter, filter))


@dataclass(frozen=True)
class TypedMutationBuilder[Executor: (TableExecutor, AsyncTableExecutor), Row]:
    """An update or a delete that does not say yet which rows it affects.

    It has no `execute()`: a filter has to be added with `where()`, or every
    row chosen on purpose with `all()`, before there is a request to run, so
    a forgotten filter cannot write the whole table.
    """

    request: TableRequest
    """The request so far, without a filter."""

    executor: Executor
    """The executor that will run it."""

    def where(self, filter: Filter[Row]) -> TypedFilterBuilder[Executor, Row, None]:
        """Only the rows satisfying `filter`, see `TypedFilterBuilder.where`:

        client.table(Books.table).update({"title": "x"}).where(Books.id.eq(1)).execute()
        """
        return self.all().where(filter)

    def all(self) -> TypedFilterBuilder[Executor, Row, None]:
        """Every row of the table, on purpose:

            client.table(Books.table).delete().all().execute()

        A filter can still be added afterwards, and `max_affected()` bounds
        how many rows the request may touch.
        """
        return TypedFilterBuilder(self.request, self.executor, _none)


@dataclass(frozen=True)
class TypedQueryBuilder[
    Executor: (TableExecutor, AsyncTableExecutor),
    Row,
    Insert,
    Update,
]:
    """The typed counterpart of `RequestBuilder`, returned by
    `PostgrestClient.table` for a `Table`.

    Rows come back decoded into `Row`, and the write methods accept only the
    `Insert` and `Update` types of the table, so a table that declares them
    as `Never`, a view for example, cannot be written to:

        books = (
            client.table(Books.table)
            .select()
            .where(Books.title.like("%Python%"))
            .order(Books.id.desc())
            .execute()
        )
        client.table(Books.table).insert({"title": "Python"}).execute()
    """

    table: Table[Row, Insert, Update]
    """The table the queries address."""

    executor: Executor
    """The executor that runs them, normally the HTTP executor of the
    client."""

    def _request(self, operation: TableOperation) -> TableRequest:
        return TableRequest(table=self.table, operation=operation)

    def select(self) -> TypedFilterBuilder[Executor, Row, list[Row]]:
        """Read every column of the rows, decoded into `Row`:

            books: list[BooksRow] = client.table(Books.table).select().execute()

        See `select_only()` to read some columns only.
        """
        request = self._request(TableOperation.SELECT)
        return TypedFilterBuilder(request, self.executor, _rows(self.table))

    def select_only(
        self, columns: Iterable[ColumnExpression[Row, Any]]
    ) -> TypedFilterBuilder[Executor, Row, list[PartialRow[Row]]]:
        """Read `columns` of the rows only, as `PartialRow`s read through the
        same entries, so a column left out cannot be read by mistake:

            books = client.table(Books.table).select_only([Books.id, Books.title]).execute()
            title: str = books[0][Books.title]

        Every entry has to belong to this table. Raises `ValueError` for an
        empty `columns`; use `select()` for every column.
        """
        selected = _selected(columns)
        request = replace(self._request(TableOperation.SELECT), columns=selected)
        convert = _partial_rows(self.table, selected)
        return TypedFilterBuilder(request, self.executor, convert)

    def insert(
        self, rows: Insert | Iterable[Insert]
    ) -> TypedTransformBuilder[Executor, Row, None]:
        """Insert one row, or every row of an iterable, into the table:

            client.table(Books.table).insert({"title": "Dune"}).execute()
            client.table(Books.table).insert([{"title": "Dune"}, {"title": "Emma"}]).execute()

        A row is a mapping of column names to values, the `Insert` type of
        the table. A column left out of a row gets its database default, even
        when another row of the same request sets it; `None` writes `NULL`.
        Values are serialized the way pydantic serializes them, so a `date`
        or a `UUID` can be given as it is.

        The request resolves to `None`; a trailing `select()` returns the
        inserted rows instead. Raises `TypeError` for a payload that is
        neither a row nor an iterable of rows.
        """
        request = replace(
            self._request(TableOperation.INSERT),
            payload=_rows_payload(rows, "insert"),
            shape=ResultShape.NONE,
        )
        return TypedTransformBuilder(request, self.executor, _none)

    def upsert(
        self,
        rows: Insert | Iterable[Insert],
        *,
        on_conflict: Iterable[Column[Row, Any] | NullableColumn[Row, Any]]
        | None = None,
        ignore_duplicates: bool = False,
    ) -> TypedTransformBuilder[Executor, Row, None]:
        """Insert one row, or every row of an iterable, merging each into the
        existing row it conflicts with, see `insert()` for `rows`.

        `on_conflict` names the columns of the unique constraint to merge on;
        without it the primary key is the target. With `ignore_duplicates`
        a conflicting row is skipped instead of merged:

            client.table(Users.table).upsert(
                {"email": "a@example.com", "name": "Ada"},
                on_conflict=[Users.email],
            ).execute()

        Raises `ValueError` for an empty `on_conflict`.
        """
        conflict = None if on_conflict is None else tuple(on_conflict)
        if conflict is not None and not conflict:
            raise ValueError("on_conflict needs at least one column")
        request = replace(
            self._request(TableOperation.UPSERT),
            payload=_rows_payload(rows, "upsert"),
            shape=ResultShape.NONE,
            on_conflict=conflict,
            ignore_duplicates=ignore_duplicates,
        )
        return TypedTransformBuilder(request, self.executor, _none)

    def update(self, values: Update) -> TypedMutationBuilder[Executor, Row]:
        """Update the rows chosen with `where()`, or every row with `all()`,
        to `values`, the `Update` type of the table:

            client.table(Books.table).update({"title": "x"}).where(Books.id.eq(1)).execute()

        Nothing is sent before one of them is called. The request resolves to
        `None`; a trailing `select()` returns the updated rows instead.
        Raises `TypeError` for `values` that is not a mapping.
        """
        request = replace(
            self._request(TableOperation.UPDATE),
            payload=_row_payload(values, "update"),
            shape=ResultShape.NONE,
        )
        return TypedMutationBuilder(request, self.executor)

    @overload
    def delete(self: TypedQueryBuilder[Executor, Row, Insert, Never]) -> None: ...
    @overload
    def delete(self) -> TypedMutationBuilder[Executor, Row]: ...
    def delete(self) -> TypedMutationBuilder[Executor, Row] | None:
        """Delete the rows chosen with `where()`, or every row with `all()`:

            client.table(Books.table).delete().where(Books.id.eq(1)).execute()

        Nothing is sent before one of them is called. The request resolves to
        `None`; a trailing `select()` returns the deleted rows instead.

        On a table whose `Update` type is `Never`, a view that cannot be
        written to, the type checkers see `None` here, so neither `where()`
        nor `all()` can follow and no delete can be sent.
        """
        request = replace(self._request(TableOperation.DELETE), shape=ResultShape.NONE)
        return TypedMutationBuilder(request, self.executor)

    def count(
        self, method: CountMethod = CountMethod.exact
    ) -> TypedCountBuilder[Executor, Row]:
        """Count the rows of the table without reading them, narrowed with
        `where()`:

            open_books = (
                client.table(Books.table).count().where(Books.is_done.eq(False)).execute()
            )

        `method` is how PostgREST counts. See `TypedTransformBuilder.count`
        for the count next to the rows.
        """
        request = replace(
            self._request(TableOperation.COUNT), count=method, shape=ResultShape.NONE
        )
        return TypedCountBuilder(request, self.executor, _count)


_TEXT = TypeAdapter(str)


def _rows[Row](table: Table[Row, Any, Any]) -> Callable[[TableResult], list[Row]]:
    adapter = _rows_adapter(table.row_type)
    return lambda result: adapter.validate_python(result.data)


def _partial_rows[Row](
    table: Table[Row, Any, Any], columns: tuple[ColumnExpression[Row, Any], ...]
) -> Callable[[TableResult], list[PartialRow[Row]]]:
    return lambda result: [
        PartialRow(table, columns, row)
        for row in JSONListParser.validate_python(result.data)
    ]


def _one[Element](
    convert: Callable[[TableResult], list[Element]],
) -> Callable[[TableResult], Element]:
    """Converts the one row of a result the way `convert` converts a list of
    rows, so the same element type comes out of both."""

    def one(result: TableResult) -> Element:
        (row,) = convert(replace(result, data=[result.data]))
        return row

    return one


def _maybe_one[Element](
    convert: Callable[[TableResult], list[Element]],
) -> Callable[[TableResult], Element | None]:
    one = _one(convert)
    return lambda result: None if result.data is None else one(result)


def _none(result: TableResult) -> None:
    return None


def _text(result: TableResult) -> str:
    return _TEXT.validate_python(result.data)


def _object(result: TableResult) -> dict[str, JSON]:
    return JSONDictParser.validate_python(result.data)


def _value(result: TableResult) -> JSON:
    return result.data


def _count(result: TableResult) -> int:
    if result.count is None:
        raise ValueError(
            "The executor returned no count for a request that asked for one"
        )
    return result.count


def _selected[Row](
    columns: Iterable[ColumnExpression[Row, Any]],
) -> tuple[ColumnExpression[Row, Any], ...]:
    selected = tuple(columns)
    if not selected:
        raise ValueError(
            "select_only() needs at least one column; use select() for every column"
        )
    return selected


def _rows_payload(rows: object, method: str) -> JSON:
    """`rows` as the payload of a write: one JSON object for a row, a list of
    them for an iterable of rows."""
    error = (
        f"{method}() takes a row, a mapping of column names to values, or an "
        "iterable of rows"
    )
    payload = _jsonable(rows, error)
    if isinstance(payload, Mapping):
        return payload
    if (
        isinstance(payload, Sequence)
        and not isinstance(payload, str)
        and all(isinstance(row, Mapping) for row in payload)
    ):
        return list(payload)
    raise TypeError(error)


def _row_payload(values: object, method: str) -> JSON:
    error = f"{method}() takes a mapping of column names to values"
    payload = _jsonable(values, error)
    if isinstance(payload, Mapping):
        return payload
    raise TypeError(error)


def _jsonable(value: object, error: str) -> JSON:
    """`value` as plain JSON, serialized the way pydantic serializes it, or
    `TypeError` with `error` when it cannot be."""
    try:
        jsonable = to_jsonable_python(value)
    except PydanticSerializationError as cause:
        raise TypeError(error) from cause
    return JSONParser.validate_python(jsonable)


def _and_filter(current: Filter[Any] | None, filter: Filter[Any]) -> Filter[Any]:
    """`filter` combined with the filter `current` a request carries, when
    it carries one."""
    return filter if current is None else current & filter
