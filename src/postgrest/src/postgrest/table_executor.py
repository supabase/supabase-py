from __future__ import annotations

from collections.abc import Mapping
from dataclasses import replace
from typing import TYPE_CHECKING, Protocol, assert_never

from supabase_utils.http.io import AsyncHttpIO, SyncHttpIO

from ._parsing import parse_json, parse_object, parse_rows
from .exceptions import APIError
from .request_builder import (
    APIResponse,
    PostgrestRequest,
    _api_error,
    _explain,
    _filters_embedded_resource,
    _invalid_response_error,
    _max_affected,
    _multiple_rows_error,
    _select_returned,
    pre_delete,
    pre_insert,
    pre_rpc,
    pre_select,
    pre_update,
    pre_upsert,
)
from .table_request import (
    ExplainOptions,
    ResultShape,
    TableOperation,
    TableRequest,
    TableResult,
)
from .types import CountMethod, ResponseShape, ReturnMethod

if TYPE_CHECKING:
    from collections.abc import Awaitable

    from supabase_utils.http.headers import Headers
    from supabase_utils.http.io import HttpMethod
    from supabase_utils.http.request import Response
    from supabase_utils.types import JSON

    from .client import PostgrestClient


class TableExecutor(Protocol):
    """Runs the requests of the typed table API and waits for the result.

    `HttpTableExecutor` sends them to PostgREST. An executor that wraps
    another, to log, cache or rewrite requests, holds the inner one and
    forwards to it; a changed request is a `dataclasses.replace` of the one
    it got:

        @dataclass
        class SoftDeleting:
            inner: TableExecutor

            def execute(self, request: TableRequest) -> TableResult:
                if request.operation is TableOperation.DELETE:
                    request = replace(
                        request,
                        operation=TableOperation.UPDATE,
                        payload={"deleted_at": datetime.now(UTC).isoformat()},
                    )
                return self.inner.execute(request)
    """

    def execute(self, request: TableRequest) -> TableResult:
        """Performs `request` and returns its result in the shape it asked
        for."""
        ...


class AsyncTableExecutor(Protocol):
    """Runs the requests of the typed table API without blocking, see
    `TableExecutor`.

    `execute()` returns an awaitable, so both an `async def` and a method
    that hands the request to another executor satisfy it.
    """

    def execute(self, request: TableRequest) -> Awaitable[TableResult]:
        """Performs `request` and returns its result in the shape it asked
        for."""
        ...


_TYPED_API = "typed-api"
"""The feature the HTTP executors list in `X-Client-Info` on every request
they send."""

_WRITES = frozenset(
    {
        TableOperation.INSERT,
        TableOperation.UPSERT,
        TableOperation.UPDATE,
        TableOperation.DELETE,
    }
)
"""The operations that get rows back only when `returning` is set."""

_SHAPES_OF_A_SILENT_WRITE = frozenset(
    {ResultShape.ROWS, ResultShape.NONE, ResultShape.EXPLAIN}
)
"""The shapes a write that is not `returning` takes, having no rows to
shape."""

_SHAPES_WITHOUT_STRIP_NULLS = frozenset(
    {ResultShape.CSV, ResultShape.GEOJSON, ResultShape.EXPLAIN}
)
"""The shapes PostgREST cannot strip the nulls of."""

_ROW_FILTERED = frozenset(
    {TableOperation.UPDATE, TableOperation.DELETE, TableOperation.COUNT}
)
"""The operations whose filter has to name rows of the table."""

_LOGIC_KEYS = frozenset({"or", "and", "not.or", "not.and"})
"""The query parameters of a filter group at the top level, which narrow
the rows of the table like a plain filter does."""


class _HttpTableExecutor[HttpIO: (SyncHttpIO, AsyncHttpIO)]:
    """What the HTTP executors share: the client whose transport, headers and
    options the requests use."""

    def __init__(self, client: PostgrestClient[HttpIO]) -> None:
        self.client = client

    def _headers(self) -> Headers:
        """The headers of the client as they are now, so that a request sent
        later carries the current access token, with `typed-api` among the
        features of `X-Client-Info`."""
        return self.client.default_headers.with_client_info_features((_TYPED_API,))

    @staticmethod
    def _exchange(
        rendered: PostgrestRequest, request: TableRequest
    ) -> HttpMethod[TableResult]:
        response = yield rendered
        return _decode(response, request)


class HttpTableExecutor(_HttpTableExecutor[SyncHttpIO]):
    """The executor of a `SyncPostgrestClient`, which sends a request to
    PostgREST and waits for the answer.

    The request is rendered through the string builders of the client, so
    the parameters and headers on the wire are the ones `from_()` and `rpc()`
    would have produced for the same query, and the `RetryPolicy` and the
    request timeout of the client apply. The headers of the client, with the
    access token and the `apikey` among them, are read when the request is
    sent, not when it is built.
    """

    def execute(self, request: TableRequest) -> TableResult:
        """Sends `request` and returns its result in the shape it asked for.

        Raises `ValueError` before anything is sent for a request that cannot
        be rendered: a filter on an insert or upsert, anything but a filter
        on a count, a filter of an update, delete or count that names no rows
        of the table, a write without a payload, a shape on a write that
        returns no rows, and `strip_nulls` with a shape that has no nulls to
        strip. Raises `APIError` for an answer that is not a success, that
        is not in the shape asked for, or that committed a dry run.
        """
        rendered = _render(request)
        return self.client.executor.communicate(
            self.client.base_url, self._headers(), self._exchange(rendered, request)
        )


class AsyncHttpTableExecutor(_HttpTableExecutor[AsyncHttpIO]):
    """The executor of an `AsyncPostgrestClient`, see `HttpTableExecutor`."""

    async def execute(self, request: TableRequest) -> TableResult:
        """Sends `request` and returns its result in the shape it asked for,
        see `HttpTableExecutor.execute`."""
        rendered = _render(request)
        return await self.client.executor.communicate(
            self.client.base_url, self._headers(), self._exchange(rendered, request)
        )


def _render(request: TableRequest) -> PostgrestRequest:
    """The `PostgrestRequest` the string builders would send for `request`,
    with its options applied.

    Raises `ValueError` for a request that cannot be sent as it is, see
    `HttpTableExecutor.execute`.
    """
    if request.strip_nulls and request.shape in _SHAPES_WITHOUT_STRIP_NULLS:
        raise ValueError(f"strip_nulls cannot be used with the {request.shape} shape")
    rendered = _filtered(_operation(request), request)
    if request.operation is TableOperation.COUNT:
        _reject_transforms(request)
    else:
        rendered = _shaped(_transformed(rendered, request), request)
    return _with_options(rendered, request)


def _operation(request: TableRequest) -> PostgrestRequest:
    """The request of the operation alone, as `from_()` and `rpc()` start
    it."""
    table = request.table.name
    head = request.shape is ResultShape.HEAD
    match request.operation:
        case TableOperation.SELECT:
            args = pre_select(*_select_list(request), count=request.count, head=head)
        case TableOperation.COUNT:
            args = pre_select("*", count=request.count or CountMethod.exact, head=True)
        case TableOperation.INSERT:
            payload = _payload(request)
            args = pre_insert(
                payload,
                count=request.count,
                returning=_return_method(request),
                upsert=False,
                default_to_null=not isinstance(payload, list),
            )
        case TableOperation.UPSERT:
            payload = _payload(request)
            args = pre_upsert(
                payload,
                count=request.count,
                returning=_return_method(request),
                ignore_duplicates=request.ignore_duplicates,
                on_conflict=",".join(
                    column.name for column in request.on_conflict or ()
                ),
                default_to_null=not isinstance(payload, list),
            )
        case TableOperation.UPDATE:
            args = pre_update(
                _payload(request),
                count=request.count,
                returning=_return_method(request),
            )
        case TableOperation.DELETE:
            args = pre_delete(count=request.count, returning=_return_method(request))
        case TableOperation.RPC:
            return pre_rpc(
                table,
                _arguments(request),
                head=head,
                count=request.count,
                get=request.read_only,
            )
        case _:
            assert_never(request.operation)
    return PostgrestRequest(
        path=[table],
        method=args.method,
        headers=args.headers,
        query=args.params,
        body=args.json,
    )


def _select_list(request: TableRequest) -> tuple[str, ...]:
    """The entries of the `select` list, which `pre_select` cleans and
    replaces with `*` when there are none."""
    return tuple(column.expression for column in request.columns)


def _return_method(request: TableRequest) -> ReturnMethod:
    return ReturnMethod.representation if request.returning else ReturnMethod.minimal


def _payload(request: TableRequest) -> JSON:
    if request.payload is None:
        raise ValueError(
            f"An {request.operation} needs a payload: the row or rows to write"
        )
    return request.payload


def _arguments(request: TableRequest) -> Mapping[str, JSON]:
    if request.payload is None:
        return {}
    if not isinstance(request.payload, Mapping):
        raise ValueError(
            "The payload of a function call is a mapping of its arguments, "
            f"not {type(request.payload).__name__}"
        )
    return request.payload


def _reject_transforms(request: TableRequest) -> None:
    """Rejects a count that carries anything but its filter, which a count
    has no rows for."""
    bare = TableRequest(
        table=request.table,
        operation=TableOperation.COUNT,
        schema=request.schema,
        filter=request.filter,
        count=request.count,
        options=request.options,
    )
    if request not in (bare, replace(bare, shape=ResultShape.NONE)):
        raise ValueError("A count takes filters only, no transforms")


def _filtered(rendered: PostgrestRequest, request: TableRequest) -> PostgrestRequest:
    """`rendered` with the filter of `request` as its query parameters.

    An insert or upsert takes no filter, the same way the string builders
    offer none after them; a hand-built request that carries one is rejected
    rather than sent with the filter silently dropped. The filter of an
    update, delete or count has to name rows of the table, as the string
    builder requires of an update and a delete: a filter on an embedded
    resource, such as `author.name`, applies to the embedded rows only, so
    sending it would affect every row while looking filtered. No filter at
    all affects every row on purpose, see `TableRequest.filter`.
    """
    if request.filter is None:
        return rendered
    if request.operation in (TableOperation.INSERT, TableOperation.UPSERT):
        raise ValueError(f"An {request.operation} takes no filter")
    parameters = request.filter._query_parameters()
    if request.operation in _ROW_FILTERED and not any(
        _names_rows(key) for key, _ in parameters
    ):
        raise ValueError(
            f"The filter of the {request.operation} names no rows of the table: "
            "a filter on an embedded resource applies to the embedded rows only"
        )
    query = rendered.query
    for key, value in parameters:
        query = query.set(key, value)
    return replace(rendered, query=query)


def _names_rows(key: str) -> bool:
    """Whether the query parameter `key` of a filter narrows the rows of the
    table, rather than the rows of an embedded resource as `author.name`
    does."""
    return key in _LOGIC_KEYS or not _filters_embedded_resource(key)


def _transformed(rendered: PostgrestRequest, request: TableRequest) -> PostgrestRequest:
    """`rendered` with the `select` list of a returning write or of a
    function call, the orderings, the row window and the preferences of
    `request`.

    The orderings go into one `order` parameter, since PostgREST reads the
    first `order` parameter only.
    """
    if (request.operation in _WRITES and request.returning) or (
        request.operation is TableOperation.RPC and request.columns
    ):
        rendered = _select_returned(rendered, *_select_list(request))
    query = rendered.query
    if request.orderings:
        order = ",".join(ordering.order_key for ordering in request.orderings)
        query = query.set("order", order)
    if request.offset is not None:
        query = query.set("offset", request.offset)
    if request.limit is not None:
        query = query.set("limit", request.limit)
    rendered = replace(rendered, query=query)
    if request.max_affected is not None:
        rendered = _max_affected(rendered, request.max_affected)
    if request.dry_run:
        rendered = replace(
            rendered, headers=_preferring(rendered.headers, "tx=rollback")
        )
    if request.strip_nulls:
        rendered = replace(rendered, strip_nulls=True)
    return rendered


def _shaped(rendered: PostgrestRequest, request: TableRequest) -> PostgrestRequest:
    """`rendered` asking for the shape of `request`, which the `Accept`
    header carries."""
    if request.shape is ResultShape.HEAD and request.operation in _WRITES:
        raise ValueError(
            f"The {request.operation} cannot be sent as HEAD, which carries no body"
        )
    if (
        request.operation in _WRITES
        and not request.returning
        and request.shape not in _SHAPES_OF_A_SILENT_WRITE
    ):
        raise ValueError(
            f"The {request.operation} returns no rows unless returning is set, "
            f"so it cannot be read as {request.shape}"
        )
    match request.shape:
        case (
            ResultShape.ROWS
            | ResultShape.MAYBE_SINGLE
            | ResultShape.NONE
            | ResultShape.HEAD
            | ResultShape.VALUE
        ):
            return rendered
        case ResultShape.SINGLE:
            return replace(rendered, shape=ResponseShape.SINGLE)
        case ResultShape.CSV:
            return replace(rendered, shape=ResponseShape.CSV)
        case ResultShape.GEOJSON:
            return replace(rendered, shape=ResponseShape.GEOJSON)
        case ResultShape.EXPLAIN:
            options = request.explain or ExplainOptions()
            return _explain(
                rendered,
                analyze=options.analyze,
                verbose=options.verbose,
                settings=options.settings,
                buffers=options.buffers,
                wal=options.wal,
                format=options.format,
            )
        case _:
            assert_never(request.shape)


def _with_options(
    rendered: PostgrestRequest, request: TableRequest
) -> PostgrestRequest:
    """`rendered` in the schema of `request` and with its options: the
    headers, the retry policy and the timeout."""
    headers = rendered.headers
    schema = request.schema if request.schema is not None else request.table.schema
    if schema is not None:
        headers = headers.override("Accept-Profile", schema).override(
            "Content-Profile", schema
        )
    for key, value in request.options.headers.items():
        if key.lower() == "prefer":
            headers = _preferring(headers, value)
        else:
            headers = headers.override(key, value)
    return replace(
        rendered,
        headers=headers,
        retry=request.options.retry,
        timeout=request.options.timeout,
    )


def _preferring(headers: Headers, preferences: str) -> Headers:
    """`headers` with the comma-separated `preferences` added to `Prefer`,
    each replacing the preference of the same name, so that a second
    `return=` or `count=` does not contradict the first."""
    given = [preference.strip() for preference in preferences.split(",")]
    given = [preference for preference in given if preference]
    names = {_preference_name(preference) for preference in given}
    kept = [
        preference.strip()
        for value in headers.get_list("Prefer") or []
        for preference in value.split(",")
        if preference.strip() and _preference_name(preference) not in names
    ]
    headers = headers.remove("Prefer")
    for preference in (*kept, *given):
        headers = headers.set("Prefer", preference)
    return headers


def _preference_name(preference: str) -> str:
    return preference.partition("=")[0].strip().lower()


def _decode(response: Response, request: TableRequest) -> TableResult:
    """The `TableResult` of `response`, decoded by the shape of `request`.

    Raises `APIError` for an answer that is not a success, whose body is not
    in the shape asked for, or that committed a dry run: PostgREST accepts
    `tx=rollback` whatever its `db-tx-end` setting, and lists it in
    `Preference-Applied` only when it rolled back.
    """
    if not response.is_success:
        raise _api_error(response)
    if request.dry_run and not _rolled_back(response):
        raise _committed_dry_run_error(response)
    count = APIResponse._get_count_from_http_request_response(response)
    try:
        data = _data(response, request)
    except ValueError as error:
        raise _invalid_response_error(response) from error
    return TableResult(data=data, count=count)


def _rolled_back(response: Response) -> bool:
    applied = response.headers.get("Preference-Applied") or ""
    return "tx=rollback" in {preference.strip() for preference in applied.split(",")}


def _committed_dry_run_error(response: Response) -> APIError:
    return APIError(
        {
            "message": "The dry run was committed: PostgREST applied no tx=rollback",
            "code": str(response.status),
            "hint": "A rollback needs db-tx-end = commit-allow-override on the server",
            "details": response.headers.get("Preference-Applied"),
        },
        status_code=response.status,
        response=response,
    )


def _data(response: Response, request: TableRequest) -> JSON:
    if request.operation is TableOperation.COUNT:
        return None
    if request.operation in _WRITES and not request.returning:
        return None
    content = response.content
    match request.shape:
        case ResultShape.NONE | ResultShape.HEAD:
            return None
        case ResultShape.ROWS:
            return parse_rows(content) if content else []
        case ResultShape.SINGLE | ResultShape.GEOJSON:
            return parse_object(content)
        case ResultShape.MAYBE_SINGLE:
            rows = parse_rows(content) if content else []
            if len(rows) > 1:
                raise _multiple_rows_error()
            return rows[0] if rows else None
        case ResultShape.CSV:
            return content.decode("utf-8")
        case ResultShape.EXPLAIN:
            if request.explain is None or request.explain.format == "text":
                return content.decode("utf-8")
            return parse_json(content)
        case ResultShape.VALUE:
            return parse_json(content) if content else None
        case _:
            assert_never(request.shape)
