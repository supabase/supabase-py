from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from json import JSONDecodeError
from re import search
from types import TracebackType
from typing import (
    Any,
    Awaitable,
    Dict,
    Generic,
    Iterable,
    List,
    Literal,
    NamedTuple,
    Optional,
    Tuple,
    Type,
    TypeVar,
    Union,
    overload,
)

from httpx import AsyncClient, BasicAuth, Client, Headers, QueryParams, Response
from httpx import Response as RequestResponse
from pydantic import BaseModel, TypeAdapter, ValidationError
from supabase_utils.http import (
    AsyncHttpIO,
    HttpIO,
    HttpMethod,
    HTTPRequestMethod,
    JSONRequest,
    SyncHttpIO,
    handle_http_io,
)
from supabase_utils.types import JSON, JSONParser
from typing_extensions import Self, override
from yarl import URL

from .constants import DEFAULT_POSTGREST_CLIENT_HEADERS
from .exceptions import APIError, APIErrorFromJSON, generate_default_error_message
from .types import CountMethod, Filters, RequestMethod, ReturnMethod
from .utils import model_validate_json, sanitize_param

if sys.version_info >= (3, 11):
    from typing import Self
else:
    from typing_extensions import Self

try:
    # >= 2.0.0
    from pydantic import field_validator
except ImportError:
    # < 2.0.0
    from pydantic import validator as field_validator  # type: ignore


class QueryArgs(NamedTuple):
    # groups the method, json, headers and params for a query in a single object
    method: HTTPRequestMethod
    params: QueryParams
    headers: Headers
    json: JSON


C = TypeVar("C", Client, AsyncClient)


def _unique_columns(json: List[Dict[str, JSON]]):
    unique_keys = {key for row in json for key in row.keys()}
    columns = ",".join([f'"{k}"' for k in unique_keys])
    return columns


def _cleaned_columns(columns: Tuple[str, ...]) -> str:
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
    params = QueryParams({"select": cleaned_columns})

    headers = Headers({"Prefer": f"count={count}"}) if count else Headers()
    return QueryArgs(method, params, headers, {})


def pre_insert(
    json: JSON,
    *,
    count: CountMethod | None,
    returning: ReturnMethod,
    upsert: bool,
    default_to_null: bool = True,
) -> QueryArgs:
    prefer_headers = [f"return={returning}"]
    if count:
        prefer_headers.append(f"count={count}")
    if upsert:
        prefer_headers.append("resolution=merge-duplicates")
    if not default_to_null:
        prefer_headers.append("missing=default")
    headers = Headers({"Prefer": ",".join(prefer_headers)})
    # Adding 'columns' query parameters
    query_params = {}
    if isinstance(json, list):
        query_params = {"columns": _unique_columns(json)}
    return QueryArgs("POST", QueryParams(query_params), headers, json)


def pre_upsert(
    json: JSON,
    *,
    count: CountMethod | None,
    returning: ReturnMethod,
    ignore_duplicates: bool,
    on_conflict: str = "",
    default_to_null: bool = True,
) -> QueryArgs:
    query_params = {}
    prefer_headers = [f"return={returning}"]
    if count:
        prefer_headers.append(f"count={count}")
    resolution = "ignore" if ignore_duplicates else "merge"
    prefer_headers.append(f"resolution={resolution}-duplicates")
    if not default_to_null:
        prefer_headers.append("missing=default")
    headers = Headers({"Prefer": ",".join(prefer_headers)})
    if on_conflict:
        query_params["on_conflict"] = on_conflict
    # Adding 'columns' query parameters
    if isinstance(json, list):
        query_params["columns"] = _unique_columns(json)
    return QueryArgs("POST", QueryParams(query_params), headers, json)


def pre_update(
    json: JSON,
    *,
    count: CountMethod | None,
    returning: ReturnMethod,
) -> QueryArgs:
    prefer_headers = [f"return={returning}"]
    if count:
        prefer_headers.append(f"count={count}")
    headers = Headers({"Prefer": ",".join(prefer_headers)})
    return QueryArgs("PATCH", QueryParams(), headers, json)


def pre_delete(
    *,
    count: CountMethod | None,
    returning: ReturnMethod,
) -> QueryArgs:
    prefer_headers = [f"return={returning}"]
    if count:
        prefer_headers.append(f"count={count}")
    headers = Headers({"Prefer": ",".join(prefer_headers)})
    return QueryArgs("DELETE", QueryParams(), headers, {})


JSONListParser = TypeAdapter(List[JSON])


@dataclass
class APIResponse:
    data: List[JSON]
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
        response: RequestResponse,
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
    def from_http_request_response(response: RequestResponse) -> APIResponse:
        count = APIResponse._get_count_from_http_request_response(response)
        data = JSONListParser.validate_json(response.content)
        return APIResponse(data=data, count=count)


@dataclass
class SingleAPIResponse:
    data: JSON
    count: int | None

    @staticmethod
    def from_http_request_response(
        response: RequestResponse,
    ) -> SingleAPIResponse:
        count = APIResponse._get_count_from_http_request_response(response)
        data = JSONParser.validate_json(response.content)
        return SingleAPIResponse(data=data, count=count)


@dataclass
class BaseFilterRequestBuilder:
    request: JSONRequest
    negate_next: bool = False

    @property
    def not_(self: Self) -> Self:
        """Whether the filter applied next should be negated."""
        self.negate_next = True
        return self

    def filter(self: Self, column: str, operator: str, criteria: str) -> Self:
        """Apply filters on a query.

        Args:
            column: The name of the column to apply a filter on
            operator: The operator to use while filtering
            criteria: The value to filter by
        """
        if self.negate_next is True:
            self.negate_next = False
            operator = f"{Filters.NOT}.{operator}"
        key, val = sanitize_param(column), f"{operator}.{criteria}"
        self.request.query_params = self.request.query_params.add(key, val)
        return self

    def eq(self: Self, column: str, value: str) -> Self:
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
        if value is None:
            value = "null"
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
        key = f"{sanitize_param(reference_table)}.or" if reference_table else "or"
        self.request.query_params = self.request.query_params.add(key, f"({filters})")
        return self

    def fts(self: Self, column: str, query: Any) -> Self:
        return self.filter(column, Filters.FTS, query)

    def plfts(self: Self, column: str, query: Any) -> Self:
        return self.filter(column, Filters.PLFTS, query)

    def phfts(self: Self, column: str, query: Any) -> Self:
        return self.filter(column, Filters.PHFTS, query)

    def wfts(self: Self, column: str, query: Any) -> Self:
        return self.filter(column, Filters.WFTS, query)

    def in_(self: Self, column: str, values: Iterable[Any]) -> Self:
        values = map(sanitize_param, values)
        values = ",".join(values)
        return self.filter(column, Filters.IN, f"({values})")

    def cs(self: Self, column: str, values: Iterable[Any]) -> Self:
        values = ",".join(values)
        return self.filter(column, Filters.CS, f"{{{values}}}")

    def cd(self: Self, column: str, values: Iterable[Any]) -> Self:
        values = ",".join(values)
        return self.filter(column, Filters.CD, f"{{{values}}}")

    def contains(
        self: Self, column: str, value: Iterable[str] | str | Dict[str, JSON]
    ) -> Self:
        if isinstance(value, str):
            # range types can be inclusive '[', ']' or exclusive '(', ')' so just
            # keep it simple and accept a string
            return self.filter(column, Filters.CS, value)
        if not isinstance(value, dict) and isinstance(value, Iterable):
            # Expected to be some type of iterable
            stringified_values = ",".join(value)
            return self.filter(column, Filters.CS, f"{{{stringified_values}}}")

        return self.filter(column, Filters.CS, json.dumps(value))

    def contained_by(
        self: Self, column: str, value: Iterable[str] | str | Dict[str, JSON]
    ) -> Self:
        if isinstance(value, str):
            # range
            return self.filter(column, Filters.CD, value)
        if not isinstance(value, dict) and isinstance(value, Iterable):
            stringified_values = ",".join(value)
            return self.filter(column, Filters.CD, f"{{{stringified_values}}}")
        return self.filter(column, Filters.CD, json.dumps(value))

    def ov(
        self: Self, column: str, value: Iterable[str] | str | Dict[str, JSON]
    ) -> Self:
        if isinstance(value, str):
            # range types can be inclusive '[', ']' or exclusive '(', ')' so just
            # keep it simple and accept a string
            return self.filter(column, Filters.OV, value)
        if not isinstance(value, dict) and isinstance(value, Iterable):
            # Expected to be some type of iterable
            stringified_values = ",".join(value)
            return self.filter(column, Filters.OV, f"{{{stringified_values}}}")
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

    def overlaps(self: Self, column: str, values: str | Iterable[str]) -> Self:
        return self.ov(column, values)

    def match(self: Self, query: Dict[str, str]) -> Self:
        updated_query = self

        if not query:
            raise ValueError(
                "query dictionary should contain at least one key-value pair"
            )

        for key, value in query.items():
            updated_query = self.eq(key, value)

        return updated_query

    def max_affected(self: Self, value: int) -> Self:
        """Set the maximum number of rows that can be affected by the query.

        Only available in PostgREST v13+ and only works with PATCH and DELETE methods.

        Args:
            value: The maximum number of rows that can be affected
        """
        prefer_header = self.request.headers.get("Prefer", "")
        if prefer_header:
            if "handling=strict" not in prefer_header:
                prefer_header += ",handling=strict"
        else:
            prefer_header = "handling=strict"

        prefer_header += f",max-affected={value}"

        self.request.headers["Prefer"] = prefer_header
        return self


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
        existing_order = self.request.query_params.get(key)

        self.request.query_params = self.request.query_params.set(
            key,
            f"{existing_order + ',' if existing_order else ''}"
            + f"{column}.{'desc' if desc else 'asc'}"
            + (
                f".{'nullsfirst' if nullsfirst else 'nullslast'}"
                if nullsfirst is not None
                else ""
            ),
        )
        return self

    def limit(self: Self, size: int, *, foreign_table: str | None = None) -> Self:
        """Limit the number of rows returned by a query.

        Args:
            size: The number of rows to be returned
            foreign_table: Foreign table name to limit
        .. versionchanged:: 0.10.3
           Allow limiting results returned for foreign tables with the foreign_table parameter.
        """
        self.request.query_params = self.request.query_params.add(
            f"{foreign_table}.limit" if foreign_table else "limit",
            size,
        )
        return self

    def offset(self: Self, size: int) -> Self:
        """Set the starting row index returned by a query.
        Args:
            size: The number of the row to start at
        """
        self.request.query_params = self.request.query_params.add(
            "offset",
            size,
        )
        return self

    def range(
        self: Self, start: int, end: int, foreign_table: str | None = None
    ) -> Self:
        self.request.query_params = self.request.query_params.add(
            f"{foreign_table}.offset" if foreign_table else "offset", start
        )
        self.request.query_params = self.request.query_params.add(
            f"{foreign_table}.limit" if foreign_table else "limit",
            end - start + 1,
        )
        return self


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
        method, params, headers, json = pre_select(*columns, count=None)
        self.request.query_params = self.request.query_params.add(
            "select", params.get("select")
        )
        if self.request.headers.get("Prefer"):
            self.request.headers["Prefer"] += ",return=representation"
        else:
            self.request.headers["Prefer"] = "return=representation"

        return self

    def single(self) -> Self:
        """Specify that the query will only return a single row in response.

        .. caution::
            The API will raise an error if the query returned more than one row.
        """
        self.request.headers["Accept"] = "application/vnd.pgrst.object+json"
        return self

    def csv(self) -> Self:
        """Specify that the query must retrieve data as a single CSV string."""
        self.request.headers["Accept"] = "text/csv"
        return self


@dataclass
class BaseRequestClient(Generic[HttpIO]):
    executor: HttpIO
    base_url: URL
    default_headers: Headers
    request: JSONRequest


class QueryRequestBuilder(BaseRequestClient[HttpIO]):
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
        try:
            if r.is_success:
                return APIResponse.from_http_request_response(r)
            else:
                json_obj = model_validate_json(APIErrorFromJSON, r.content)
                raise APIError(dict(json_obj))
        except ValidationError as e:
            raise APIError(generate_default_error_message(r))


class SingleRequestBuilder(BaseRequestClient[HttpIO]):
    @handle_http_io
    def execute(self) -> HttpMethod[SingleAPIResponse]:
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
            return SingleAPIResponse.from_http_request_response(response)
        else:
            json_obj = model_validate_json(APIErrorFromJSON, response.content)
            raise APIError(dict(json_obj))


class TextRequestBuilder(BaseRequestClient[HttpIO]):
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
            json_obj = model_validate_json(APIErrorFromJSON, response.content)
            raise APIError(dict(json_obj))


class ExplainRequestBuilder(BaseRequestClient[HttpIO]):
    @handle_http_io
    def execute(self) -> HttpMethod[str]:
        r = yield self.request
        try:
            if r.is_success:
                return r.text
            else:
                json_obj = model_validate_json(APIErrorFromJSON, r.content)
                raise APIError(dict(json_obj))
        except ValidationError as e:
            raise APIError(generate_default_error_message(r))


class MaybeSingleRequestBuilder(BaseRequestClient[HttpIO]):
    @handle_http_io
    def execute(self) -> HttpMethod[SingleAPIResponse | None]:
        response = yield self.request
        if response.is_success:
            parsed = APIResponse.from_http_request_response(response)
            if len(parsed.data) == 0:
                return None
            if len(parsed.data) == 1:
                return SingleAPIResponse(data=parsed.data[0], count=parsed.count)
            else:
                raise APIError(dict())
        else:
            json_obj = model_validate_json(APIErrorFromJSON, response.content)
            raise APIError(dict(json_obj))


class FilterRequestBuilder(QueryRequestBuilder[HttpIO], BaseFilterRequestBuilder):
    pass


class RPCFilterRequestBuilder(SingleRequestBuilder[HttpIO], BaseRPCRequestBuilder):
    pass


class RPCCountRequestBuilder(BaseRequestClient[HttpIO], BaseRPCRequestBuilder):
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
            json_obj = model_validate_json(APIErrorFromJSON, response.content)
            raise APIError(dict(json_obj))


class SelectRequestBuilder(QueryRequestBuilder[HttpIO], BaseSelectRequestBuilder):
    def single(self) -> SingleRequestBuilder[HttpIO]:
        """Specify that the query will only return a single row in response.

        .. caution::
            The API will raise an error if the query returned more than one row.
        """
        self.request.headers["Accept"] = "application/vnd.pgrst.object+json"
        return SingleRequestBuilder(
            executor=self.executor,
            base_url=self.base_url,
            default_headers=self.default_headers,
            request=self.request,
        )

    def maybe_single(self) -> MaybeSingleRequestBuilder[HttpIO]:
        """Retrieves at most one row from the result. Result must be at most one row (e.g. using `eq` on a UNIQUE column), otherwise this will result in an error."""
        return MaybeSingleRequestBuilder(
            executor=self.executor,
            base_url=self.base_url,
            default_headers=self.default_headers,
            request=self.request,
        )

    def text_search(
        self, column: str, query: str, options: dict[str, Any] = {}
    ) -> QueryRequestBuilder[HttpIO]:
        type_ = options.get("type")
        type_part = ""
        if type_ == "plain":
            type_part = "pl"
        elif type_ == "phrase":
            type_part = "ph"
        elif type_ == "web_search":
            type_part = "w"
        config_part = f"({options.get('config')})" if options.get("config") else ""
        self.request.query_params = self.request.query_params.add(
            column, f"{type_part}fts{config_part}.{query}"
        )

        return QueryRequestBuilder(
            executor=self.executor,
            base_url=self.base_url,
            default_headers=self.default_headers,
            request=self.request,
        )

    def csv(self) -> TextRequestBuilder[HttpIO]:
        """Specify that the query must retrieve data as a single CSV string."""
        self.request.headers["Accept"] = "text/csv"
        return TextRequestBuilder(
            executor=self.executor,
            base_url=self.base_url,
            default_headers=self.default_headers,
            request=self.request,
        )

    @overload
    def explain(
        self,
        analyze: bool = False,
        verbose: bool = False,
        settings: bool = False,
        buffers: bool = False,
        wal: bool = False,
        format: Literal["text"] = "text",
    ) -> ExplainRequestBuilder[HttpIO]: ...

    @overload
    def explain(
        self,
        analyze: bool = False,
        verbose: bool = False,
        settings: bool = False,
        buffers: bool = False,
        wal: bool = False,
        *,
        format: Literal["json"],
    ) -> SingleRequestBuilder[HttpIO]: ...

    def explain(
        self,
        analyze: bool = False,
        verbose: bool = False,
        settings: bool = False,
        buffers: bool = False,
        wal: bool = False,
        format: Literal["text", "json"] = "text",
    ) -> ExplainRequestBuilder[HttpIO] | SingleRequestBuilder[HttpIO]:
        options = [
            key
            for key, value in locals().items()
            if key not in ["self", "format"] and value
        ]
        options_str = "|".join(options)
        self.request.headers["Accept"] = (
            f"application/vnd.pgrst.plan+{format}; options={options_str}"
        )
        if format == "text":
            return ExplainRequestBuilder(
                executor=self.executor,
                base_url=self.base_url,
                default_headers=self.default_headers,
                request=self.request,
            )
        else:
            return SingleRequestBuilder(
                executor=self.executor,
                base_url=self.base_url,
                default_headers=self.default_headers,
                request=self.request,
            )


class RequestBuilder(Generic[HttpIO]):  #
    def __init__(
        self,
        executor: HttpIO,
        base_url: URL,
        default_headers: Headers,
        basic_auth: BasicAuth | None,
    ) -> None:
        self.executor: HttpIO = executor
        self.base_url = base_url
        self.default_headers = default_headers
        self.auth = basic_auth

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
        request = JSONRequest(
            path=[],
            query_params=params,
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
            :class:`AsyncQueryRequestBuilder`
        """
        method, params, headers, json = pre_insert(
            json,
            count=count,
            returning=returning,
            upsert=upsert,
            default_to_null=default_to_null,
        )

        request = JSONRequest(
            path=[],
            query_params=params,
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
            :class:`AsyncQueryRequestBuilder`
        """
        method, params, headers, json = pre_upsert(
            json,
            count=count,
            returning=returning,
            ignore_duplicates=ignore_duplicates,
            on_conflict=on_conflict,
            default_to_null=default_to_null,
        )
        request = JSONRequest(
            path=[],
            query_params=params,
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
    ) -> FilterRequestBuilder[HttpIO]:
        """Run an UPDATE query.

        Args:
            json: The updated fields.
            count: The method to use to get the count of rows returned.
            returning: Either 'minimal' or 'representation'
        Returns:
            :class:`AsyncFilterRequestBuilder`
        """
        method, params, headers, json = pre_update(
            json,
            count=count,
            returning=returning,
        )
        request = JSONRequest(
            path=[],
            query_params=params,
            method=method,
            headers=headers,
            body=json,
        )
        return FilterRequestBuilder(
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
    ) -> FilterRequestBuilder[HttpIO]:
        """Run a DELETE query.

        Args:
            count: The method to use to get the count of rows returned.
            returning: Either 'minimal' or 'representation'
        Returns:
            :class:`AsyncFilterRequestBuilder`
        """
        method, params, headers, json = pre_delete(
            count=count,
            returning=returning,
        )
        request = JSONRequest(
            path=[],
            query_params=params,
            method=method,
            headers=headers,
            body=json,
        )
        return FilterRequestBuilder(
            executor=self.executor,
            base_url=self.base_url,
            default_headers=self.default_headers,
            request=request,
        )
