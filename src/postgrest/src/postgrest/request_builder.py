from __future__ import annotations

import json
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from re import search
from typing import (
    TYPE_CHECKING,
    Any,
    Literal,
    NamedTuple,
    Self,
    assert_never,
    overload,
    override,
)

from pydantic import TypeAdapter, ValidationError
from supabase_utils.http.headers import Headers
from supabase_utils.http.io import (
    AsyncHttpIO,
    HttpMethod,
    SyncHttpIO,
    handle_http_io,
)
from supabase_utils.http.query import URLQuery
from supabase_utils.http.request import (
    HTTPRequestMethod,
    JSONRequest,
    Request,
    Response,
    validate_request_timeout,
)
from supabase_utils.types import JSON
from yarl import URL

from .exceptions import APIError, APIErrorFromJSON, generate_default_error_message
from .types import (
    _TEXT_SEARCH_OPERATORS,
    CountMethod,
    Filters,
    FilterValue,
    Mutation,
    ResponseShape,
    ReturnMethod,
    TextSearchType,
)
from .utils import (
    _in_members,
    _quote,
    _rpc_query_param,
    _sanitize_array_param,
    _serialize_filter_value,
    sanitize_param,
)

if TYPE_CHECKING:
    from supabase_utils.http.retry import RetryPolicy


class QueryArgs(NamedTuple):
    # groups the method, json, headers and params for a query in a single object
    method: HTTPRequestMethod
    params: URLQuery
    headers: Headers
    json: JSON


def _unique_columns(json: list[JSON]) -> str:
    unique_keys = dict.fromkeys(
        key for row in json if isinstance(row, Mapping) for key in row
    )
    return ",".join(_quote(key) for key in unique_keys)


def _cleaned_columns(columns: tuple[str, ...]) -> str:
    quoted = False
    cleaned = []

    for column in columns:
        clean_column = ""
        for char in column:
            if char.isspace() and not quoted:
                continue
            if char == '"':
                quoted = not quoted
            clean_column += char
        cleaned.append(clean_column)

    return ",".join(cleaned)


def pre_select(
    *columns: str,
    count: CountMethod | None = None,
    head: bool | None = None,
) -> QueryArgs:
    method: HTTPRequestMethod = "HEAD" if head else "GET"
    cleaned_columns = _cleaned_columns(columns or ("*",))
    params = URLQuery.from_mapping({"select": cleaned_columns})

    headers = (
        Headers.from_mapping({"Prefer": f"count={count}"}) if count else Headers.empty()
    )
    return QueryArgs(method, params, headers, {})


def pre_insert(
    json: JSON,
    *,
    count: CountMethod | None,
    returning: ReturnMethod,
    upsert: bool,
    default_to_null: bool = True,
) -> QueryArgs:
    prefer_headers = Headers.from_mapping({"Prefer": f"return={returning}"})
    if count:
        prefer_headers = prefer_headers.set("Prefer", f"count={count}")
    if upsert:
        prefer_headers = prefer_headers.set("Prefer", "resolution=merge-duplicates")
    if not default_to_null:
        prefer_headers = prefer_headers.set("Prefer", "missing=default")
    query_params: dict[str, str] = {}
    if isinstance(json, list) and (columns := _unique_columns(json)):
        query_params["columns"] = columns
    return QueryArgs("POST", URLQuery.from_mapping(query_params), prefer_headers, json)


def pre_upsert(
    json: JSON,
    *,
    count: CountMethod | None,
    returning: ReturnMethod,
    ignore_duplicates: bool,
    on_conflict: str = "",
    default_to_null: bool = True,
) -> QueryArgs:
    query_params: dict[str, str] = {}
    prefer_headers = Headers.from_mapping({"Prefer": f"return={returning}"})
    if count:
        prefer_headers = prefer_headers.set("Prefer", f"count={count}")
    resolution = "ignore" if ignore_duplicates else "merge"
    prefer_headers = prefer_headers.set("Prefer", f"resolution={resolution}-duplicates")
    if not default_to_null:
        prefer_headers = prefer_headers.set("Prefer", "missing=default")
    if on_conflict:
        query_params["on_conflict"] = on_conflict
    if isinstance(json, list) and (columns := _unique_columns(json)):
        query_params["columns"] = columns
    return QueryArgs("POST", URLQuery.from_mapping(query_params), prefer_headers, json)


def pre_update(
    json: JSON,
    *,
    count: CountMethod | None,
    returning: ReturnMethod,
) -> QueryArgs:
    prefer_headers = Headers.from_mapping({"Prefer": f"return={returning}"})
    if count:
        prefer_headers = prefer_headers.set("Prefer", f"count={count}")
    return QueryArgs("PATCH", URLQuery.empty(), prefer_headers, json)


def pre_delete(
    *,
    count: CountMethod | None,
    returning: ReturnMethod,
) -> QueryArgs:
    prefer_headers = Headers.from_mapping({"Prefer": f"return={returning}"})
    if count:
        prefer_headers = prefer_headers.set("Prefer", f"count={count}")
    return QueryArgs("DELETE", URLQuery.empty(), prefer_headers, {})


JSONListParser = TypeAdapter(list[dict[str, JSON]])
JSONDictParser = TypeAdapter(dict[str, JSON])


@dataclass
class APIResponse:
    data: list[dict[str, JSON]]
    """The data returned by the query."""
    count: int | None = None
    """The number of rows returned."""

    @staticmethod
    def _get_count_from_content_range_header(
        content_range_header: str,
    ) -> int | None:
        content_range = content_range_header.split("/")
        return None if len(content_range) < 2 else int(content_range[1])

    @staticmethod
    def _is_count_in_prefer_header(prefer_header: str) -> bool:
        pattern = f"count=({'|'.join([cm.value for cm in CountMethod])})"
        return bool(search(pattern, prefer_header))

    @staticmethod
    def _get_count_from_http_request_response(
        response: Response,
    ) -> int | None:
        prefer_header: str | None = response.request.headers.get("prefer")
        if not prefer_header:
            return None
        is_count_in_prefer_header = APIResponse._is_count_in_prefer_header(
            prefer_header
        )
        content_range_header: str | None = response.headers.get("content-range")
        if is_count_in_prefer_header and content_range_header:
            return APIResponse._get_count_from_content_range_header(
                content_range_header
            )
        return None

    @staticmethod
    def from_http_request_response(response: Response) -> APIResponse:
        count = APIResponse._get_count_from_http_request_response(response)
        if response.request.method == "HEAD" or not response.content:
            return APIResponse(data=[], count=count)
        data = JSONListParser.validate_json(response.content)
        return APIResponse(data=data, count=count)


@dataclass
class SingleAPIResponse:
    data: dict[str, JSON]
    count: int | None

    @staticmethod
    def from_http_request_response(
        response: Response,
    ) -> SingleAPIResponse:
        count = APIResponse._get_count_from_http_request_response(response)
        data = JSONDictParser.validate_json(response.content)
        return SingleAPIResponse(data=data, count=count)


def _filters_embedded_resource(key: str) -> bool:
    """Whether a filter key such as ``cities.name`` targets an embedded resource.

    PostgREST applies such a filter to the embedded rows only, so it does not
    narrow the rows an update or delete of the table affects. A quoted key is a
    single column name, whatever it contains.
    """
    return not key.startswith('"') and "." in key


_SHAPES_WITHOUT_STRIP_NULLS = {
    ResponseShape.CSV: "csv()",
    ResponseShape.GEOJSON: "geojson()",
    ResponseShape.PLAN: "explain()",
}


@dataclass(frozen=True)
class PostgrestRequest(JSONRequest):
    strip_nulls: bool = False
    shape: ResponseShape = ResponseShape.ROWS
    """The shape of the response, which `finalize()` renders as the `Accept`
    header. `single()`, `csv()` and `explain()` set it."""
    plan_format: Literal["text", "json"] = "text"
    """The format of the plan `explain()` asks for."""
    plan_options: tuple[str, ...] = ()
    """The PostgreSQL `EXPLAIN` options `explain()` asks for, such as
    `analyze`."""
    filter_required_by: Mutation | None = None
    """The write that refuses to send until a filter on the table names the
    rows it affects.

    `update()` and `delete()` set it, so that a forgotten filter does not
    write every row in the table. A filter on the table clears it, and so
    does `all()`. A filter on an embedded resource does not, since PostgREST
    applies it to the embedded rows only.
    """

    def __post_init__(self) -> None:
        super().__post_init__()
        if self.strip_nulls and self.shape in _SHAPES_WITHOUT_STRIP_NULLS:
            method = _SHAPES_WITHOUT_STRIP_NULLS[self.shape]
            raise ValueError(f"strip_nulls() cannot be used with {method}")

    def _accept(self) -> str | None:
        match self.shape:
            case ResponseShape.ROWS:
                if self.strip_nulls:
                    return "application/vnd.pgrst.array+json;nulls=stripped"
                return None
            case ResponseShape.SINGLE:
                if self.strip_nulls:
                    return "application/vnd.pgrst.object+json;nulls=stripped"
                return "application/vnd.pgrst.object+json"
            case ResponseShape.CSV:
                return "text/csv"
            case ResponseShape.GEOJSON:
                return "application/geo+json"
            case ResponseShape.PLAN:
                options = "|".join(self.plan_options)
                return (
                    f"application/vnd.pgrst.plan+{self.plan_format}; options={options}"
                )
            case _:
                assert_never(self.shape)

    @override
    def finalize(self, base_url: URL, default_headers: Headers) -> Request:
        if self.filter_required_by is not None:
            operation = f"{self.filter_required_by}()"
            raise ValueError(
                f"{operation} has no filter that says which rows it affects. Add "
                f"one, such as eq(), or call all() right after {operation} to run "
                "it without a filter on purpose."
            )
        request = super().finalize(base_url, default_headers)
        accept = self._accept()
        if accept is None:
            return request
        if self.strip_nulls and self.shape is ResponseShape.ROWS:
            requested = request.headers.get("Accept")
            if requested not in (None, "application/json"):
                raise ValueError(
                    f"strip_nulls() cannot be used with Accept: {requested}"
                )
        request.headers = request.headers.override("Accept", accept)
        return request


def pre_rpc(
    func: str,
    params: Mapping[str, JSON],
    *,
    head: bool = False,
    count: CountMethod | None = None,
    get: bool = False,
) -> PostgrestRequest:
    """The request of a call of the function `func` with the arguments
    `params`, see `PostgrestClient.rpc`.

    A `GET` or `HEAD` request has no body, so `get` and `head` send the
    arguments as query parameters, with a list as a PostgreSQL array literal.
    """
    method: HTTPRequestMethod = "HEAD" if head else "GET" if get else "POST"
    headers = (
        Headers.from_mapping({"Prefer": f"count={count}"}) if count else Headers.empty()
    )
    json, http_params = (
        (
            {},
            URLQuery.from_mapping({k: _rpc_query_param(v) for k, v in params.items()}),
        )
        if method in ("HEAD", "GET")
        else (dict(params), URLQuery.empty())
    )
    return PostgrestRequest(
        path=["rpc", func],
        method=method,
        headers=headers,
        query=http_params,
        body=json,
    )


def _select_returned(request: PostgrestRequest, *columns: str) -> PostgrestRequest:
    """`request` asking the rows it affects back, with `columns` as its
    `select` list: `Prefer: return=representation` replaces any other
    `return=` preference, and the list is cleaned as `pre_select` does."""
    _, params, _, _ = pre_select(*columns, count=None)
    query = request.query.set("select", params["select"])
    if prefer_headers := request.headers.get_list("Prefer"):
        prefer_headers = [h for h in prefer_headers if not h.startswith("return=")]
        prefer_headers.append("return=representation")
        headers = request.headers.override("Prefer", ",".join(prefer_headers))
    else:
        headers = request.headers.set("Prefer", "return=representation")
    return replace(request, query=query, headers=headers)


def _max_affected(request: PostgrestRequest, value: int) -> PostgrestRequest:
    """`request` allowing at most `value` affected rows, which PostgREST
    enforces with `Prefer: handling=strict`."""
    headers = request.headers.set("Prefer", "handling=strict").set(
        "Prefer", f"max-affected={value}"
    )
    return replace(request, headers=headers)


def _explain(
    request: PostgrestRequest,
    *,
    analyze: bool,
    verbose: bool,
    settings: bool,
    buffers: bool,
    wal: bool,
    format: Literal["text", "json"],
) -> PostgrestRequest:
    """`request` asking for its query plan instead of its rows, with the
    PostgreSQL `EXPLAIN` options that are enabled."""
    flags = {
        "analyze": analyze,
        "verbose": verbose,
        "settings": settings,
        "buffers": buffers,
        "wal": wal,
    }
    return replace(
        request,
        shape=ResponseShape.PLAN,
        plan_format=format,
        plan_options=tuple(option for option, enabled in flags.items() if enabled),
    )


def _multiple_rows_error() -> APIError:
    """The error of a `maybe_single()` whose query returned more than one
    row, shaped like the one PostgREST answers a `single()` with."""
    return APIError(
        {
            "message": "Cannot coerce the result to a single JSON object",
            "code": "406",
            "hint": "Please check traceback of the code",
            "details": "The result contains more than one row.",
        },
        status_code=406,
    )


@dataclass(frozen=True, kw_only=True)
class BaseFilterRequestBuilder:
    request: PostgrestRequest
    negate_next: bool = False

    @property
    def not_(self: Self) -> Self:
        """A copy of this query that negates the filter applied next."""
        return replace(self, negate_next=True)

    def filter(self: Self, column: str, operator: Filters | str, criteria: Any) -> Self:
        """Apply filters on a query.

        Args:
            column: The name of the column to apply a filter on
            operator: The operator to use while filtering. A `Filters` member,
                or a string for an operator it does not list, such as `match`
            criteria: The value to filter by
        """
        if self.negate_next:
            operator = f"{Filters.NOT}.{operator}"
        key = sanitize_param(column)
        val = f"{operator}.{_serialize_filter_value(criteria)}"
        request = replace(
            self.request,
            query=self.request.query.set(key, val),
            filter_required_by=self.request.filter_required_by
            if _filters_embedded_resource(key)
            else None,
        )
        return replace(self, negate_next=False, request=request)

    def eq(self: Self, column: str, value: Any) -> Self:
        """An 'equal to' filter.

        Args:
            column: The name of the column to apply a filter on
            value: The value to filter by
        """
        return self.filter(column, Filters.EQ, value)

    def neq(self: Self, column: str, value: Any) -> Self:
        """A 'not equal to' filter

        Args:
            column: The name of the column to apply a filter on
            value: The value to filter by
        """
        return self.filter(column, Filters.NEQ, value)

    def gt(self: Self, column: str, value: Any) -> Self:
        """A 'greater than' filter

        Args:
            column: The name of the column to apply a filter on
            value: The value to filter by
        """
        return self.filter(column, Filters.GT, value)

    def gte(self: Self, column: str, value: Any) -> Self:
        """A 'greater than or equal to' filter

        Args:
            column: The name of the column to apply a filter on
            value: The value to filter by
        """
        return self.filter(column, Filters.GTE, value)

    def lt(self: Self, column: str, value: Any) -> Self:
        """A 'less than' filter

        Args:
            column: The name of the column to apply a filter on
            value: The value to filter by
        """
        return self.filter(column, Filters.LT, value)

    def lte(self: Self, column: str, value: Any) -> Self:
        """A 'less than or equal to' filter

        Args:
            column: The name of the column to apply a filter on
            value: The value to filter by
        """
        return self.filter(column, Filters.LTE, value)

    def is_(self: Self, column: str, value: Any) -> Self:
        """An 'is' filter

        Args:
            column: The name of the column to apply a filter on
            value: The value to filter by
        """
        return self.filter(column, Filters.IS, value)

    def like(self: Self, column: str, pattern: str) -> Self:
        """A 'LIKE' filter, to use for pattern matching.

        Args:
            column: The name of the column to apply a filter on
            pattern: The pattern to filter by
        """
        return self.filter(column, Filters.LIKE, pattern)

    def like_all_of(self: Self, column: str, pattern: str) -> Self:
        """A 'LIKE' filter, to use for pattern matching.

        Args:
            column: The name of the column to apply a filter on
            pattern: The pattern to filter by
        """

        return self.filter(column, Filters.LIKE_ALL, f"{{{pattern}}}")

    def like_any_of(self: Self, column: str, pattern: str) -> Self:
        """A 'LIKE' filter, to use for pattern matching.

        Args:
            column: The name of the column to apply a filter on
            pattern: The pattern to filter by
        """

        return self.filter(column, Filters.LIKE_ANY, f"{{{pattern}}}")

    def ilike_all_of(self: Self, column: str, pattern: str) -> Self:
        """A 'ILIKE' filter, to use for pattern matching (case insensitive).

        Args:
            column: The name of the column to apply a filter on
            pattern: The pattern to filter by
        """

        return self.filter(column, Filters.ILIKE_ALL, f"{{{pattern}}}")

    def ilike_any_of(self: Self, column: str, pattern: str) -> Self:
        """A 'ILIKE' filter, to use for pattern matching (case insensitive).

        Args:
            column: The name of the column to apply a filter on
            pattern: The pattern to filter by
        """

        return self.filter(column, Filters.ILIKE_ANY, f"{{{pattern}}}")

    def ilike(self: Self, column: str, pattern: str) -> Self:
        """An 'ILIKE' filter, to use for pattern matching (case insensitive).

        Args:
            column: The name of the column to apply a filter on
            pattern: The pattern to filter by
        """
        return self.filter(column, Filters.ILIKE, pattern)

    def or_(self: Self, filters: str, reference_table: str | None = None) -> Self:
        """An 'or' filter

        Args:
            filters: The filters to use, following PostgREST syntax
            reference_table: Set this to filter on referenced tables instead of the parent table
        """
        op = "not.or" if self.negate_next else "or"
        key = f"{sanitize_param(reference_table)}.{op}" if reference_table else op
        request = replace(
            self.request,
            query=self.request.query.set(key, f"({filters})"),
            filter_required_by=self.request.filter_required_by
            if reference_table is not None
            else None,
        )
        return replace(self, negate_next=False, request=request)

    def fts(self: Self, column: str, query: Any) -> Self:
        return self.filter(column, Filters.FTS, query)

    def plfts(self: Self, column: str, query: Any) -> Self:
        return self.filter(column, Filters.PLFTS, query)

    def phfts(self: Self, column: str, query: Any) -> Self:
        return self.filter(column, Filters.PHFTS, query)

    def wfts(self: Self, column: str, query: Any) -> Self:
        return self.filter(column, Filters.WFTS, query)

    def in_(self: Self, column: str, values: Iterable[FilterValue]) -> Self:
        stringified_values = ",".join(
            sanitize_param(_serialize_filter_value(value))
            for value in _in_members(values)
        )
        return self.filter(column, Filters.IN, f"({stringified_values})")

    def cs(self: Self, column: str, values: Iterable[FilterValue]) -> Self:
        return self.filter(column, Filters.CS, _sanitize_array_param(values))

    def cd(self: Self, column: str, values: Iterable[FilterValue]) -> Self:
        return self.filter(column, Filters.CD, _sanitize_array_param(values))

    def contains(
        self: Self, column: str, value: Iterable[FilterValue] | str | dict[str, JSON]
    ) -> Self:
        if isinstance(value, str):
            # range types can be inclusive '[', ']' or exclusive '(', ')' so just
            # keep it simple and accept a string
            return self.filter(column, Filters.CS, value)
        if not isinstance(value, dict) and isinstance(value, Iterable):
            # Expected to be some type of iterable
            return self.filter(column, Filters.CS, _sanitize_array_param(value))

        return self.filter(column, Filters.CS, json.dumps(value))

    def contained_by(
        self: Self, column: str, value: Iterable[FilterValue] | str | dict[str, JSON]
    ) -> Self:
        if isinstance(value, str):
            # range
            return self.filter(column, Filters.CD, value)
        if not isinstance(value, dict) and isinstance(value, Iterable):
            return self.filter(column, Filters.CD, _sanitize_array_param(value))
        return self.filter(column, Filters.CD, json.dumps(value))

    def ov(
        self: Self, column: str, value: Iterable[FilterValue] | str | dict[str, JSON]
    ) -> Self:
        if isinstance(value, str):
            # range types can be inclusive '[', ']' or exclusive '(', ')' so just
            # keep it simple and accept a string
            return self.filter(column, Filters.OV, value)
        if not isinstance(value, dict) and isinstance(value, Iterable):
            # Expected to be some type of iterable
            return self.filter(column, Filters.OV, _sanitize_array_param(value))
        return self.filter(column, Filters.OV, json.dumps(value))

    def sl(self: Self, column: str, min: str, max: str) -> Self:
        return self.filter(column, Filters.SL, f"({min},{max})")

    def sr(self: Self, column: str, min: str, max: str) -> Self:
        return self.filter(column, Filters.SR, f"({min},{max})")

    def nxl(self: Self, column: str, min: str, max: str) -> Self:
        return self.filter(column, Filters.NXL, f"({min},{max})")

    def nxr(self: Self, column: str, min: str, max: str) -> Self:
        return self.filter(column, Filters.NXR, f"({min},{max})")

    def adj(self: Self, column: str, min: str, max: str) -> Self:
        return self.filter(column, Filters.ADJ, f"({min},{max})")

    def range_gt(self: Self, column: str, min: str, max: str) -> Self:
        return self.sr(column, min, max)

    def range_gte(self: Self, column: str, min: str, max: str) -> Self:
        return self.nxl(column, min, max)

    def range_lt(self: Self, column: str, min: str, max: str) -> Self:
        return self.sl(column, min, max)

    def range_lte(self: Self, column: str, min: str, max: str) -> Self:
        return self.nxr(column, min, max)

    def range_adjacent(self: Self, column: str, min: str, max: str) -> Self:
        return self.adj(column, min, max)

    def overlaps(self: Self, column: str, values: str | Iterable[FilterValue]) -> Self:
        return self.ov(column, values)

    def match(self: Self, query: dict[str, str | int]) -> Self:
        updated_query = self

        if not query:
            raise ValueError(
                "query dictionary should contain at least one key-value pair"
            )

        for key, value in query.items():
            updated_query = updated_query.eq(key, value)

        return updated_query

    def max_affected(self: Self, value: int) -> Self:
        """Set the maximum number of rows that can be affected by the query.

        Only available in PostgREST v13+ and only works with PATCH and DELETE methods.

        Args:
            value: The maximum number of rows that can be affected
        """
        return replace(self, request=_max_affected(self.request, value))


@dataclass(frozen=True, kw_only=True)
class BaseSelectRequestBuilder(BaseFilterRequestBuilder):
    def order(
        self: Self,
        column: str,
        *,
        desc: bool = False,
        nullsfirst: bool | None = None,
        foreign_table: str | None = None,
    ) -> Self:
        """Sort the returned rows in some specific order.

        Args:
            column: The column to order by
            desc: Whether the rows should be ordered in descending order or not.
            nullsfirst: nullsfirst
            foreign_table: Foreign table name whose results are to be ordered.
        .. versionchanged:: 0.10.3
           Allow ordering results for foreign tables with the foreign_table parameter.
        """
        key = f"{foreign_table}.order" if foreign_table else "order"
        order = f"{column}.{'desc' if desc else 'asc'}"
        nullsfirst_str = (
            f".{'nullsfirst' if nullsfirst else 'nullslast'}"
            if nullsfirst is not None
            else ""
        )
        val = f"{order}{nullsfirst_str}"
        query = self.request.query.set(key, val)
        return replace(self, request=replace(self.request, query=query))

    def strip_nulls(self: Self) -> Self:
        """Strip null values from the response data.

        Only available in PostgREST v11.2+. It cannot be combined with
        `csv()` or `explain()`, and raises `ValueError` when it is.
        """
        return replace(self, request=replace(self.request, strip_nulls=True))

    def limit(self: Self, size: int, *, foreign_table: str | None = None) -> Self:
        """Limit the number of rows returned by a query.

        Args:
            size: The number of rows to be returned
            foreign_table: Foreign table name to limit
        .. versionchanged:: 0.10.3
           Allow limiting results returned for foreign tables with the foreign_table parameter.
        """
        query = self.request.query.set(
            f"{foreign_table}.limit" if foreign_table else "limit", size
        )
        return replace(self, request=replace(self.request, query=query))

    def offset(self: Self, size: int) -> Self:
        """Set the starting row index returned by a query.
        Args:
            size: The number of the row to start at
        """
        query = self.request.query.set("offset", size)
        return replace(self, request=replace(self.request, query=query))

    def range(
        self: Self, start: int, end: int, foreign_table: str | None = None
    ) -> Self:
        query = self.request.query.set(
            f"{foreign_table}.offset" if foreign_table else "offset", start
        ).set(f"{foreign_table}.limit" if foreign_table else "limit", end - start + 1)
        return replace(self, request=replace(self.request, query=query))


@dataclass(frozen=True, kw_only=True)
class BaseRPCRequestBuilder(BaseSelectRequestBuilder):
    def select(
        self,
        *columns: str,
    ) -> Self:
        """Run a SELECT query.

        Args:
            *columns: The names of the columns to fetch.
        Returns:
            :class:`BaseSelectRequestBuilder`
        """
        _method, params, _headers, _json = pre_select(*columns, count=None)
        request = replace(
            self.request,
            query=self.request.query.merge(params),
            headers=self.request.headers.set("Prefer", "return=representation"),
        )
        return replace(self, request=request)

    def csv(self) -> Self:
        """Specify that the query must retrieve data as a single CSV string."""
        request = replace(self.request, shape=ResponseShape.CSV)
        return replace(self, request=request)


@dataclass(frozen=True, kw_only=True)
class BaseRequestClient[HttpIO: (SyncHttpIO, AsyncHttpIO)]:
    executor: HttpIO
    base_url: URL
    default_headers: Headers
    request: PostgrestRequest

    def retry(self, policy: RetryPolicy | bool) -> Self:
        """Decide how this query is retried when a request of it fails in a
        way worth repeating, instead of leaving it to the `RetryPolicy` of the
        client.

        `False` never retries it. `True` retries it with the policy of the
        client, and a `RetryPolicy` with that policy instead, both even when
        it is not a GET or HEAD request, which opts in a write that is safe
        to send twice.
        """
        return replace(self, request=replace(self.request, retry=policy))

    def request_timeout(self, seconds: float) -> Self:
        """Fail with `RequestTimeoutError` once a request of this query goes
        `seconds` without progress, overriding the timeout of the client."""
        validate_request_timeout(seconds)
        return replace(self, request=replace(self.request, timeout=seconds))


def _api_error(response: Response) -> APIError:
    try:
        json_obj = APIErrorFromJSON.model_validate_json(response.content)
    except ValidationError:
        error = generate_default_error_message(response)
    else:
        error = dict(json_obj)
    return APIError(error, status_code=response.status, response=response)


def _invalid_response_error(response: Response) -> APIError:
    return APIError(
        generate_default_error_message(response),
        status_code=response.status,
        response=response,
    )


@dataclass(frozen=True, kw_only=True)
class QueryRequestBuilder[HttpIO: (SyncHttpIO, AsyncHttpIO)](BaseRequestClient[HttpIO]):
    def select(self, *columns: str) -> Self:
        return replace(self, request=_select_returned(self.request, *columns))

    def single(self) -> SingleRequestBuilder[HttpIO]:
        """Specify that the query will only return a single row in response.

        .. caution::
            The API will raise an error if the query returned more than one row.
        """
        return SingleRequestBuilder(
            executor=self.executor,
            base_url=self.base_url,
            default_headers=self.default_headers,
            request=replace(self.request, shape=ResponseShape.SINGLE),
        )

    def maybe_single(self) -> MaybeSingleRequestBuilder[HttpIO]:
        """Retrieves at most one row from the result. Result must be at most one row (e.g. using `eq` on a UNIQUE column), otherwise this will result in an error."""
        return MaybeSingleRequestBuilder(
            executor=self.executor,
            base_url=self.base_url,
            default_headers=self.default_headers,
            request=self.request,
        )

    def csv(self) -> TextRequestBuilder[HttpIO]:
        """Specify that the query must retrieve data as a single CSV string."""
        return TextRequestBuilder(
            executor=self.executor,
            base_url=self.base_url,
            default_headers=self.default_headers,
            request=replace(self.request, shape=ResponseShape.CSV),
        )

    @overload
    def explain(self) -> ExplainRequestBuilder[HttpIO]: ...

    @overload
    def explain(
        self,
        *,
        analyze: bool,
        verbose: bool,
        settings: bool,
        buffers: bool,
        wal: bool,
        format: Literal["text"],
    ) -> ExplainRequestBuilder[HttpIO]: ...

    @overload
    def explain(
        self,
        *,
        analyze: bool,
        verbose: bool,
        settings: bool,
        buffers: bool,
        wal: bool,
        format: Literal["json"],
    ) -> QueryRequestBuilder[HttpIO]: ...

    def explain(
        self,
        *,
        analyze: bool = False,
        verbose: bool = False,
        settings: bool = False,
        buffers: bool = False,
        wal: bool = False,
        format: Literal["text", "json"] = "text",
    ) -> ExplainRequestBuilder[HttpIO] | QueryRequestBuilder[HttpIO]:
        request = _explain(
            self.request,
            analyze=analyze,
            verbose=verbose,
            settings=settings,
            buffers=buffers,
            wal=wal,
            format=format,
        )
        if format == "text":
            return ExplainRequestBuilder(
                executor=self.executor,
                base_url=self.base_url,
                default_headers=self.default_headers,
                request=request,
            )
        return QueryRequestBuilder(
            executor=self.executor,
            base_url=self.base_url,
            default_headers=self.default_headers,
            request=request,
        )

    @handle_http_io
    def execute(self) -> HttpMethod[APIResponse]:
        """Execute the query.

        .. tip::
            This is the last method called, after the query is built.

        Returns:
            :class:`APIResponse`

        Raises:
            :class:`APIError` If the API raised an error.
        """
        r = yield self.request
        if not r.is_success:
            raise _api_error(r)
        try:
            return APIResponse.from_http_request_response(r)
        except ValidationError as e:
            raise _invalid_response_error(r) from e


@dataclass(frozen=True, kw_only=True)
class SingleRequestBuilder[HttpIO: (SyncHttpIO, AsyncHttpIO)](
    BaseRequestClient[HttpIO]
):
    @handle_http_io
    def execute(self) -> HttpMethod[SingleAPIResponse]:
        """Execute the query.

        .. tip::
            This is the last method called, after the query is built.

        Returns:
            :class:`SingleAPIResponse`

        Raises:
            :class:`APIError` If the API raised an error.
        """
        response = yield self.request
        if not response.is_success:
            raise _api_error(response)
        try:
            return SingleAPIResponse.from_http_request_response(response)
        except ValidationError as e:
            raise _invalid_response_error(response) from e


@dataclass(frozen=True, kw_only=True)
class TextRequestBuilder[HttpIO: (SyncHttpIO, AsyncHttpIO)](BaseRequestClient[HttpIO]):
    @handle_http_io
    def execute(self) -> HttpMethod[str]:
        """Execute the query.

                .. tip::
                    This is the last method called, after the query is built.

                Returns:
                    :class:`SingleAPIResponse`
        na
                Raises:
                    :class:`APIError` If the API raised an error.
        """
        response = yield self.request
        if response.is_success:
            return response.content.decode("utf8")
        else:
            raise _api_error(response)


@dataclass(frozen=True, kw_only=True)
class ExplainRequestBuilder[HttpIO: (SyncHttpIO, AsyncHttpIO)](
    BaseRequestClient[HttpIO]
):
    @handle_http_io
    def execute(self) -> HttpMethod[str]:
        r = yield self.request
        if not r.is_success:
            raise _api_error(r)
        return r.content.decode("utf-8")


@dataclass(frozen=True, kw_only=True)
class MaybeSingleRequestBuilder[HttpIO: (SyncHttpIO, AsyncHttpIO)](
    BaseRequestClient[HttpIO]
):
    @handle_http_io
    def execute(self) -> HttpMethod[SingleAPIResponse | None]:
        response = yield self.request
        if response.is_success:
            try:
                parsed = APIResponse.from_http_request_response(response)
            except ValidationError as e:
                raise _invalid_response_error(response) from e
            if len(parsed.data) == 0:
                return None
            if len(parsed.data) == 1:
                return SingleAPIResponse(data=parsed.data[0], count=parsed.count)
            else:
                raise _multiple_rows_error()
        else:
            raise _api_error(response)


@dataclass(frozen=True, kw_only=True)
class FilterRequestBuilder[HttpIO: (SyncHttpIO, AsyncHttpIO)](
    QueryRequestBuilder[HttpIO], BaseFilterRequestBuilder
):
    pass


@dataclass(frozen=True, kw_only=True)
class RPCFilterRequestBuilder[HttpIO: (SyncHttpIO, AsyncHttpIO)](
    BaseRequestClient[HttpIO], BaseRPCRequestBuilder
):
    def single(self) -> SingleRequestBuilder[HttpIO]:
        """Specify that the query will only return a single row in response.

        .. caution::
            The API will raise an error if the query returned more than one row.
        """
        return SingleRequestBuilder(
            executor=self.executor,
            base_url=self.base_url,
            default_headers=self.default_headers,
            request=replace(self.request, shape=ResponseShape.SINGLE),
        )

    def maybe_single(self) -> MaybeSingleRequestBuilder[HttpIO]:
        """Retrieves at most one row from the result. Result must be at most one row (e.g. using `eq` on a UNIQUE column), otherwise this will result in an error."""
        return MaybeSingleRequestBuilder(
            executor=self.executor,
            base_url=self.base_url,
            default_headers=self.default_headers,
            request=self.request,
        )

    @handle_http_io
    def execute(self) -> HttpMethod[APIResponse]:
        """Execute the query.

        .. tip::
            This is the last method called, after the query is built.

        Returns:
            :class:`APIResponse`

        Raises:
            :class:`APIError` If the API raised an error.
        """
        r = yield self.request
        if not r.is_success:
            raise _api_error(r)
        try:
            return APIResponse.from_http_request_response(r)
        except ValidationError as e:
            raise _invalid_response_error(r) from e


@dataclass(frozen=True, kw_only=True)
class RPCCountRequestBuilder[HttpIO: (SyncHttpIO, AsyncHttpIO)](
    BaseRequestClient[HttpIO], BaseRPCRequestBuilder
):
    @handle_http_io
    def execute(self) -> HttpMethod[int | None]:
        """Execute the query.

        .. tip::
            This is the last method called, after the query is built.

        Returns:
            :class:`APIResponse`

        Raises:
            :class:`APIError` If the API raised an error.
        """
        response = yield self.request
        if response.is_success:
            count = APIResponse._get_count_from_http_request_response(response)
            return count
        else:
            raise _api_error(response)


@dataclass(frozen=True, kw_only=True)
class SelectRequestBuilder[HttpIO: (SyncHttpIO, AsyncHttpIO)](
    QueryRequestBuilder[HttpIO], BaseSelectRequestBuilder
):
    def text_search(
        self: Self,
        column: str,
        query: str,
        *,
        type: TextSearchType | None = None,
        config: str | None = None,
    ) -> Self:
        """A full text search filter.

        Args:
            column: The name of the column to search
            query: The text search query
            type: How PostgreSQL parses `query`. Without it, `query` is
                parsed by `to_tsquery`
            config: The text search configuration to use, such as `english`
        """
        operator: str = Filters.FTS
        if type is not None:
            operator = _TEXT_SEARCH_OPERATORS[TextSearchType(type)]
        if config:
            operator = f"{operator}({config})"
        return self.filter(column, operator, query)


@dataclass(frozen=True, kw_only=True)
class MutationRequestBuilder[HttpIO: (SyncHttpIO, AsyncHttpIO)](
    SelectRequestBuilder[HttpIO]
):
    """The query of an `update()` or a `delete()`.

    It refuses to send until a filter, or `all()`, names the rows it affects.
    """

    def all(self) -> Self:
        """Run the request without a filter on purpose.

        An `update()` or `delete()` without a filter raises `ValueError`
        instead of being sent, since without a limit it affects every row in
        the table. `all()` states that this is intended. It adds nothing to
        the request, and a filter applied before or after it still applies.
        It is a method of this builder, so it comes before `single()`,
        `maybe_single()`, `csv()` and `explain()`.
        """
        return replace(self, request=replace(self.request, filter_required_by=None))


@dataclass(frozen=True, kw_only=True)
class RequestBuilder[HttpIO: (SyncHttpIO, AsyncHttpIO)]:
    executor: HttpIO
    base_url: URL
    default_headers: Headers

    def select(
        self,
        *columns: str,
        count: CountMethod | None = None,
        head: bool | None = None,
    ) -> SelectRequestBuilder[HttpIO]:
        """Run a SELECT query.

        Args:
            *columns: The names of the columns to fetch.
            count: The method to use to get the count of rows returned.
        Returns:
            :class:`SelectRequestBuilder`
        """
        method, params, headers, json = pre_select(*columns, count=count, head=head)
        request = PostgrestRequest(
            path=[],
            query=params,
            method=method,
            headers=headers,
            body=json,
        )
        return SelectRequestBuilder(
            executor=self.executor,
            base_url=self.base_url,
            default_headers=self.default_headers,
            request=request,
        )

    def insert(
        self,
        json: JSON,
        *,
        count: CountMethod | None = None,
        returning: ReturnMethod = ReturnMethod.representation,
        upsert: bool = False,
        default_to_null: bool = True,
    ) -> QueryRequestBuilder[HttpIO]:
        """Run an INSERT query.

        Args:
            json: The row to be inserted.
            count: The method to use to get the count of rows returned.
            returning: Either 'minimal' or 'representation'
            upsert: Whether the query should be an upsert.
            default_to_null: Make missing fields default to `null`.
                Otherwise, use the default value for the column.
                Only applies for bulk inserts.
        Returns:
            :class:`QueryRequestBuilder`. PostgREST ignores filters, ordering
            and limits on an insert, so only the shape of the returned rows
            can be changed, with `select`, `single`, `maybe_single`, `csv`
            and `explain`.
        """
        method, params, headers, json = pre_insert(
            json,
            count=count,
            returning=returning,
            upsert=upsert,
            default_to_null=default_to_null,
        )

        request = PostgrestRequest(
            path=[],
            query=params,
            method=method,
            headers=headers,
            body=json,
        )
        return QueryRequestBuilder(
            executor=self.executor,
            base_url=self.base_url,
            default_headers=self.default_headers,
            request=request,
        )

    def upsert(
        self,
        json: JSON,
        *,
        count: CountMethod | None = None,
        returning: ReturnMethod = ReturnMethod.representation,
        ignore_duplicates: bool = False,
        on_conflict: str = "",
        default_to_null: bool = True,
    ) -> QueryRequestBuilder[HttpIO]:
        """Run an upsert (INSERT ... ON CONFLICT DO UPDATE) query.

        Args:
            json: The row to be inserted.
            count: The method to use to get the count of rows returned.
            returning: Either 'minimal' or 'representation'
            ignore_duplicates: Whether duplicate rows should be ignored.
            on_conflict: Specified columns to be made to work with UNIQUE constraint.
            default_to_null: Make missing fields default to `null`. Otherwise, use the
                default value for the column. This only applies when inserting new rows,
                not when merging with existing rows under `ignoreDuplicates: false`.
                This also only applies when doing bulk upserts.
        Returns:
            :class:`QueryRequestBuilder`. PostgREST ignores filters, ordering
            and limits on an upsert, so only the shape of the returned rows
            can be changed, with `select`, `single`, `maybe_single`, `csv`
            and `explain`.
        """
        method, params, headers, json = pre_upsert(
            json,
            count=count,
            returning=returning,
            ignore_duplicates=ignore_duplicates,
            on_conflict=on_conflict,
            default_to_null=default_to_null,
        )
        request = PostgrestRequest(
            path=[],
            query=params,
            method=method,
            headers=headers,
            body=json,
        )
        return QueryRequestBuilder(
            executor=self.executor,
            base_url=self.base_url,
            default_headers=self.default_headers,
            request=request,
        )

    def update(
        self,
        json: JSON,
        *,
        count: CountMethod | None = None,
        returning: ReturnMethod = ReturnMethod.representation,
    ) -> MutationRequestBuilder[HttpIO]:
        """Run an UPDATE query.

        Args:
            json: The updated fields.
            count: The method to use to get the count of rows returned.
            returning: Either 'minimal' or 'representation'
        Returns:
            :class:`MutationRequestBuilder`. Executing it without a filter
            raises `ValueError` before anything is sent, since it would
            update every row in the table. Call `all()` to do so on purpose.
        """
        method, params, headers, json = pre_update(
            json,
            count=count,
            returning=returning,
        )
        request = PostgrestRequest(
            path=[],
            query=params,
            method=method,
            headers=headers,
            body=json,
            filter_required_by=Mutation.UPDATE,
        )
        return MutationRequestBuilder(
            executor=self.executor,
            base_url=self.base_url,
            default_headers=self.default_headers,
            request=request,
        )

    def delete(
        self,
        *,
        count: CountMethod | None = None,
        returning: ReturnMethod = ReturnMethod.representation,
    ) -> MutationRequestBuilder[HttpIO]:
        """Run a DELETE query.

        Args:
            count: The method to use to get the count of rows returned.
            returning: Either 'minimal' or 'representation'
        Returns:
            :class:`MutationRequestBuilder`. Executing it without a filter
            raises `ValueError` before anything is sent, since it would
            delete every row in the table. Call `all()` to do so on purpose.
        """
        method, params, headers, json = pre_delete(
            count=count,
            returning=returning,
        )
        request = PostgrestRequest(
            path=[],
            query=params,
            method=method,
            headers=headers,
            body=json,
            filter_required_by=Mutation.DELETE,
        )
        return MutationRequestBuilder(
            executor=self.executor,
            base_url=self.base_url,
            default_headers=self.default_headers,
            request=request,
        )
