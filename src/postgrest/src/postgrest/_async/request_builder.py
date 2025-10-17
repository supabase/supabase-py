from __future__ import annotations

from typing import Any, Generic, Literal, Optional, TypeVar, Union, overload

from httpx import AsyncClient, BasicAuth, Headers, QueryParams, Response
from pydantic import ValidationError
from typing_extensions import override
from yarl import URL

from ..base_request_builder import (
    APIResponse,
    BaseFilterRequestBuilder,
    BaseRPCRequestBuilder,
    BaseSelectRequestBuilder,
    CountMethod,
    RequestConfig,
    SingleAPIResponse,
    pre_delete,
    pre_insert,
    pre_select,
    pre_update,
    pre_upsert,
)
from ..exceptions import APIError, APIErrorFromJSON, generate_default_error_message
from ..types import JSON, ReturnMethod
from ..utils import model_validate_json

ReqConfig = RequestConfig[AsyncClient]


class AsyncQueryRequestBuilder:
    def __init__(self, request: ReqConfig):
        self.request = request

    async def execute(self) -> APIResponse:
        """Execute the query.

        .. tip::
            This is the last method called, after the query is built.

        Returns:
            :class:`APIResponse`

        Raises:
            :class:`APIError` If the API raised an error.
        """
        r = await self.request.send()
        try:
            if r.is_success:
                return APIResponse.from_http_request_response(r)
            else:
                json_obj = model_validate_json(APIErrorFromJSON, r.content)
                raise APIError(dict(json_obj))
        except ValidationError as e:
            raise APIError(generate_default_error_message(r))


class AsyncSingleRequestBuilder:
    def __init__(self, request: ReqConfig):
        self.request = request

    async def execute(self) -> SingleAPIResponse:
        """Execute the query.

                .. tip::
                    This is the last method called, after the query is built.

                Returns:
                    :class:`SingleAPIResponse`
        na
                Raises:
                    :class:`APIError` If the API raised an error.
        """
        r = await self.request.send()
        try:
            if (
                200 <= r.status_code <= 299
            ):  # Response.ok from JS (https://developer.mozilla.org/en-US/docs/Web/API/Response/ok)
                return SingleAPIResponse.from_http_request_response(r)
            else:
                json_obj = model_validate_json(APIErrorFromJSON, r.content)
                raise APIError(dict(json_obj))
        except ValidationError as e:
            raise APIError(generate_default_error_message(r))


class AsyncExplainRequestBuilder:
    def __init__(self, request: ReqConfig):
        self.request = request

    async def execute(self) -> str:
        r = await self.request.send()
        try:
            if r.is_success:
                return r.text
            else:
                json_obj = model_validate_json(APIErrorFromJSON, r.content)
                raise APIError(dict(json_obj))
        except ValidationError as e:
            raise APIError(generate_default_error_message(r))


class AsyncMaybeSingleRequestBuilder:
    def __init__(self, request: ReqConfig):
        self.request = request

    async def execute(self) -> Optional[SingleAPIResponse]:
        r = None
        try:
            r = await AsyncSingleRequestBuilder(self.request).execute()
        except APIError as e:
            if e.details and "The result contains 0 rows" in e.details:
                return None
        if not r:
            raise APIError(
                {
                    "message": "Missing response",
                    "code": "204",
                    "hint": "Please check traceback of the code",
                    "details": "Postgrest couldn't retrieve response, please check traceback of the code. Please create an issue in `supabase-community/postgrest-py` if needed.",
                }
            )
        return r


class AsyncFilterRequestBuilder(
    BaseFilterRequestBuilder[AsyncClient], AsyncQueryRequestBuilder
):
    def __init__(self, request: ReqConfig) -> None:
        BaseFilterRequestBuilder.__init__(self, request)
        AsyncQueryRequestBuilder.__init__(self, request)


class AsyncRPCFilterRequestBuilder(BaseRPCRequestBuilder, AsyncSingleRequestBuilder):
    def __init__(self, request: ReqConfig) -> None:
        BaseFilterRequestBuilder.__init__(self, request)
        AsyncSingleRequestBuilder.__init__(self, request)


class AsyncSelectRequestBuilder(
    AsyncQueryRequestBuilder, BaseSelectRequestBuilder[AsyncClient]
):
    def __init__(self, request: ReqConfig) -> None:
        BaseSelectRequestBuilder.__init__(self, request)
        AsyncQueryRequestBuilder.__init__(self, request)

    def single(self) -> AsyncSingleRequestBuilder:
        """Specify that the query will only return a single row in response.

        .. caution::
            The API will raise an error if the query returned more than one row.
        """
        self.request.headers["Accept"] = "application/vnd.pgrst.object+json"
        return AsyncSingleRequestBuilder(self.request)

    def maybe_single(self) -> AsyncMaybeSingleRequestBuilder:
        """Retrieves at most one row from the result. Result must be at most one row (e.g. using `eq` on a UNIQUE column), otherwise this will result in an error."""
        self.request.headers["Accept"] = "application/vnd.pgrst.object+json"
        return AsyncMaybeSingleRequestBuilder(self.request)

    def text_search(
        self, column: str, query: str, options: dict[str, Any] = {}
    ) -> AsyncQueryRequestBuilder:
        type_ = options.get("type")
        type_part = ""
        if type_ == "plain":
            type_part = "pl"
        elif type_ == "phrase":
            type_part = "ph"
        elif type_ == "web_search":
            type_part = "w"
        config_part = f"({options.get('config')})" if options.get("config") else ""
        self.request.params = self.request.params.add(
            column, f"{type_part}fts{config_part}.{query}"
        )

        return AsyncQueryRequestBuilder(self.request)

    def csv(self) -> AsyncSingleRequestBuilder:
        """Specify that the query must retrieve data as a single CSV string."""
        self.request.headers["Accept"] = "text/csv"
        return AsyncSingleRequestBuilder(self.request)

    @overload
    def explain(
        self,
        analyze: bool = False,
        verbose: bool = False,
        settings: bool = False,
        buffers: bool = False,
        wal: bool = False,
        format: Literal["text"] = "text",
    ) -> AsyncExplainRequestBuilder: ...

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
    ) -> AsyncSingleRequestBuilder: ...

    def explain(
        self,
        analyze: bool = False,
        verbose: bool = False,
        settings: bool = False,
        buffers: bool = False,
        wal: bool = False,
        format: Literal["text", "json"] = "text",
    ) -> AsyncExplainRequestBuilder | AsyncSingleRequestBuilder:
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
            return AsyncExplainRequestBuilder(self.request)
        else:
            return AsyncSingleRequestBuilder(self.request)


class AsyncRequestBuilder:  #
    def __init__(
        self, session: AsyncClient, path: URL, headers: Headers, auth: BasicAuth | None
    ) -> None:
        self.session = session
        self.path = path
        self.headers = headers
        self.auth = auth

    def select(
        self,
        *columns: str,
        count: Optional[CountMethod] = None,
        head: Optional[bool] = None,
    ) -> AsyncSelectRequestBuilder:
        """Run a SELECT query.

        Args:
            *columns: The names of the columns to fetch.
            count: The method to use to get the count of rows returned.
        Returns:
            :class:`AsyncSelectRequestBuilder`
        """
        method, params, headers, json = pre_select(*columns, count=count, head=head)
        headers.update(self.headers)
        request = RequestConfig(
            session=self.session,
            path=self.path,
            auth=self.auth,
            params=params,
            http_method=method,
            headers=headers,
            json=json,
        )
        return AsyncSelectRequestBuilder(request)

    def insert(
        self,
        json: JSON,
        *,
        count: Optional[CountMethod] = None,
        returning: ReturnMethod = ReturnMethod.representation,
        upsert: bool = False,
        default_to_null: bool = True,
    ) -> AsyncQueryRequestBuilder:
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
        headers.update(self.headers)
        request = RequestConfig(
            session=self.session,
            path=self.path,
            auth=self.auth,
            params=params,
            http_method=method,
            headers=headers,
            json=json,
        )
        return AsyncQueryRequestBuilder(request)

    def upsert(
        self,
        json: JSON,
        *,
        count: Optional[CountMethod] = None,
        returning: ReturnMethod = ReturnMethod.representation,
        ignore_duplicates: bool = False,
        on_conflict: str = "",
        default_to_null: bool = True,
    ) -> AsyncQueryRequestBuilder:
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
        headers.update(self.headers)
        request = RequestConfig(
            session=self.session,
            path=self.path,
            auth=self.auth,
            params=params,
            http_method=method,
            headers=headers,
            json=json,
        )
        return AsyncQueryRequestBuilder(request)

    def update(
        self,
        json: JSON,
        *,
        count: Optional[CountMethod] = None,
        returning: ReturnMethod = ReturnMethod.representation,
    ) -> AsyncFilterRequestBuilder:
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
        headers.update(self.headers)
        request = RequestConfig(
            session=self.session,
            path=self.path,
            auth=self.auth,
            params=params,
            http_method=method,
            headers=headers,
            json=json,
        )
        return AsyncFilterRequestBuilder(request)

    def delete(
        self,
        *,
        count: Optional[CountMethod] = None,
        returning: ReturnMethod = ReturnMethod.representation,
    ) -> AsyncFilterRequestBuilder:
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
        headers.update(self.headers)
        request = RequestConfig(
            session=self.session,
            path=self.path,
            auth=self.auth,
            params=params,
            http_method=method,
            headers=headers,
            json=json,
        )
        return AsyncFilterRequestBuilder(request)
