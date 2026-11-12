from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Literal

from supabase_utils.http.request import validate_request_timeout
from supabase_utils.http.retry import RetryPolicy
from supabase_utils.types import JSON

from .column_expression import Column, NullableColumn
from .filter import ColumnExpression, Filter, Ordering
from .table import Table
from .types import CountMethod


class TableOperation(StrEnum):
    """What a `TableRequest` does to its table."""

    SELECT = "select"
    """Reads rows."""

    INSERT = "insert"
    """Inserts the payload rows."""

    UPSERT = "upsert"
    """Inserts the payload rows, merging or skipping the ones that conflict."""

    UPDATE = "update"
    """Updates the matching rows with the payload."""

    DELETE = "delete"
    """Deletes the matching rows."""

    COUNT = "count"
    """Counts the matching rows without reading them."""

    RPC = "rpc"
    """Calls the function the table of the request is named after, with the
    payload as its arguments."""


class ResultShape(StrEnum):
    """The form a `TableRequest` asks its result back in."""

    ROWS = "rows"
    """Every matching row."""

    SINGLE = "single"
    """Exactly one row; anything else is an error."""

    MAYBE_SINGLE = "maybe_single"
    """At most one row, or nothing."""

    NONE = "none"
    """No rows; the request runs for its effect only."""

    HEAD = "head"
    """No rows and no body, a `HEAD` request."""

    CSV = "csv"
    """The rows rendered as csv text."""

    GEOJSON = "geojson"
    """The rows as one GeoJSON object."""

    EXPLAIN = "explain"
    """The query plan instead of the rows."""

    VALUE = "value"
    """The response body of a function call as decoded, whatever its shape."""


@dataclass(frozen=True, kw_only=True)
class ExplainOptions:
    """The options of a `ResultShape.EXPLAIN` request, the ones of the string
    builder's `explain()`."""

    analyze: bool = False
    """Runs the query and reports actual run times."""

    verbose: bool = False
    """Includes additional plan detail."""

    settings: bool = False
    """Includes the configuration parameters that affect the plan."""

    buffers: bool = False
    """Includes buffer usage."""

    wal: bool = False
    """Includes write-ahead log usage."""

    format: Literal["text", "json"] = "text"
    """The output format of the plan."""


@dataclass(frozen=True, kw_only=True)
class RequestOptions:
    """How a `TableRequest` is sent, as opposed to what it asks for.

    `HttpTableExecutor` and `AsyncHttpTableExecutor` apply every option. An
    executor that does not send the request over HTTP, one answering from a
    local store for example, may ignore them.
    """

    headers: Mapping[str, str] = field(default_factory=dict)
    """The headers sent on top of the ones the request renders to.

    A header replaces the one the request or the client would send under the
    same name, with two exceptions. `Accept` is decided by the shape of the
    request. The preferences of `Prefer`, comma-separated `name=value` pairs,
    are merged into the ones the request carries, each replacing the
    preference of the same name.
    """

    retry: RetryPolicy | bool | None = None
    """How the request is retried when it fails in a way worth repeating,
    instead of leaving it to the `RetryPolicy` of the client.

    `None` leaves it to the method of the request, as the client does.
    `False` never retries it. `True` retries it with the policy of the
    client, and a `RetryPolicy` with that policy instead, both even when it
    is not a GET or HEAD request, which opts in a write that is safe to send
    twice.
    """

    timeout: float | None = None
    """Seconds the request may go without progress before it fails with
    `RequestTimeoutError`, or `None` for the request timeout of the client."""

    def __post_init__(self) -> None:
        validate_request_timeout(self.timeout)


@dataclass(frozen=True, kw_only=True)
class TableRequest:
    """Everything a typed table query has collected, ready to be run by a
    `TableExecutor`.

    The value is immutable and carries no URL and no headers: the filter, the
    orderings and the payload are still structured values rather than URL
    text, so an executor can run it anywhere, against a local store for
    example. `HttpTableExecutor` renders it into the PostgREST request the
    string builders would have sent. A changed copy is a `dataclasses.replace`.
    """

    table: Table[Any, Any, Any]
    """The table the request addresses.

    For `TableOperation.RPC` it describes the function instead: its name,
    and the row type of the rows it returns.
    """

    operation: TableOperation
    """What the request does to `table`."""

    schema: str | None = None
    """The schema to query `table` in, or `None` for the schema the table
    carries and, when it carries none, the schema of the client."""

    columns: tuple[ColumnExpression[Any, Any], ...] = ()
    """The entries of the `select` list to read back; empty for every column.

    For a write these are the columns of the returned rows, and only apply
    when `returning` is set.
    """

    filter: Filter[Any] | None = None
    """The rows to act on, or `None` for every row.

    An update or delete without a filter affects the whole table, and an
    executor sends it as it is: the typed query builder, not the value,
    requires `where()` or `all()` before it builds one.
    """

    orderings: tuple[Ordering[Any], ...] = ()
    """The sort keys, first key first."""

    limit: int | None = None
    """The maximum number of rows to return."""

    offset: int | None = None
    """The number of rows to skip."""

    shape: ResultShape = ResultShape.ROWS
    """The form the result is asked back in.

    A write that is not `returning` has no rows to shape: it takes `ROWS`,
    `NONE` and `EXPLAIN` only.
    """

    count: CountMethod | None = None
    """The count to compute next to the result, or `None` for none.

    For `TableOperation.COUNT` this is the count algorithm, and `None`
    means exact.
    """

    payload: JSON = None
    """The rows a write sends, one JSON object or a list of them, or the
    arguments of a function call.

    A column left out of some rows of a list gets its database default, and
    a column set to `None` is written as `NULL`.

    Kept as the caller passed it, not copied: an executor must not modify
    it. An executor that stores a request for later, an outbox for example,
    serializes the payload when it takes it.
    """

    read_only: bool = False
    """Whether a `TableOperation.RPC` call only reads, so that it runs in a
    read-only transaction and is retried like a select.

    `HttpTableExecutor` sends such a call as a `GET`, with the payload as
    query parameters, as the string builder's `rpc(get=True)` does.
    """

    on_conflict: tuple[Column[Any, Any] | NullableColumn[Any, Any], ...] | None = None
    """The columns of the unique constraint an upsert merges on, or `None`
    for the primary key."""

    ignore_duplicates: bool = False
    """Whether an upsert skips conflicting rows instead of merging them."""

    returning: bool = False
    """Whether a write returns the rows it affected, which a trailing
    `select()` asks for. Without it the result holds no data. A function
    call returns its rows whatever this says."""

    max_affected: int | None = None
    """The maximum number of rows a write may affect."""

    strip_nulls: bool = False
    """Whether `NULL` values are left out of the returned rows."""

    dry_run: bool = False
    """Whether the transaction is rolled back after the request.

    PostgREST allows the rollback only when its `db-tx-end` setting ends in
    `allow-override`; otherwise the request fails rather than commits.
    """

    explain: ExplainOptions | None = None
    """The options of a `ResultShape.EXPLAIN` request, or `None` for the
    defaults."""

    options: RequestOptions = field(default_factory=RequestOptions)
    """How the request is sent: its headers, retry policy and timeout."""


@dataclass(frozen=True)
class TableResult:
    """What a `TableExecutor` produced for a `TableRequest`.

    `data` follows the `shape` of the request, as plain decoded JSON: a list
    of row objects for rows, one row object or `None` for a single row, a
    `str` for csv and for a text plan, an object for GeoJSON, and `None` when
    nothing was asked back. A `ResultShape.VALUE` request gets the decoded
    response body as it is. The typed query converts it into the row type.
    """

    data: JSON = None
    """The decoded result, shaped as described on the class."""

    count: int | None = None
    """The row count, when the request asked for one."""
