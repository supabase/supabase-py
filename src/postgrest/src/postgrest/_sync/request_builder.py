from __future__ import annotations

from typing import Any, Generic, Optional, TypeVar, Union

from httpx import Client, Headers, QueryParams
from pydantic import ValidationError
from typing_extensions import override

from ..base_request_builder import (
    APIResponse,
    BaseFilterRequestBuilder,
    BaseRPCRequestBuilder,
    BaseSelectRequestBuilder,
    CountMethod,
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


class SyncQueryRequestBuilder:
    def __init__(
        self,
        session: Client,
        path: str,
        http_method: str,
        headers: Headers,
        params: QueryParams,
        json: JSON,
    ) -> None:
        self.session = session
        self.path = path
        self.http_method = http_method
        self.headers = headers
        self.params = params
        self.json = None if http_method in {"GET", "HEAD"} else json

    def execute(self) -> APIResponse | str:
        """Execute the query.

        .. tip::
            This is the last method called, after the query is built.

        Returns:
            :class:`APIResponse`

        Raises:
            :class:`APIError` If the API raised an error.
        """
        r = self.session.request(
            self.http_method,
            self.path,
            json=self.json,
            params=self.params,
            headers=self.headers,
        )
        try:
            if r.is_success:
                if self.http_method != "HEAD":
                    body = r.text
                    if self.headers.get("Accept") == "text/csv":
                        return body
                    if self.headers.get(
                        "Accept"
                    ) and "application/vnd.pgrst.plan" in self.headers.get("Accept"):
                        if "+json" not in self.headers.get("Accept"):
                            return body
                return APIResponse.from_http_request_response(r)
            else:
                json_obj = model_validate_json(APIErrorFromJSON, r.content)
                raise APIError(dict(json_obj))
        except ValidationError as e:
            raise APIError(generate_default_error_message(r))


class SyncSingleRequestBuilder:
    def __init__(
        self,
        session: Client,
        path: str,
        http_method: str,
        headers: Headers,
        params: QueryParams,
        json: JSON,
    ) -> None:
        self.session = session
        self.path = path
        self.http_method = http_method
        self.headers = headers
        self.params = params
        self.json = json

    def execute(self) -> SingleAPIResponse:
        """Execute the query.

                .. tip::
                    This is the last method called, after the query is built.

                Returns:
                    :class:`SingleAPIResponse`
        na
                Raises:
                    :class:`APIError` If the API raised an error.
        """
        r = self.session.request(
            self.http_method,
            self.path,
            json=self.json,
            params=self.params,
            headers=self.headers,
        )
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


class SyncMaybeSingleRequestBuilder:
    def __init__(
        self,
        session: Client,
        path: str,
        http_method: str,
        headers: Headers,
        params: QueryParams,
        json: JSON,
    ) -> None:
        self.session = session
        self.path = path
        self.http_method = http_method
        self.headers = headers
        self.params = params
        self.json = json

    def execute(self) -> Optional[SingleAPIResponse]:
        r = None
        try:
            request = SyncSingleRequestBuilder(
                self.session,
                self.path,
                self.http_method,
                self.headers,
                self.params,
                self.json,
            )
            r = request.execute()
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


class SyncFilterRequestBuilder(BaseFilterRequestBuilder, SyncQueryRequestBuilder):
    def __init__(
        self,
        session: Client,
        path: str,
        http_method: str,
        headers: Headers,
        params: QueryParams,
        json: JSON,
    ) -> None:
        BaseFilterRequestBuilder.__init__(self, headers, params)
        SyncQueryRequestBuilder.__init__(
            self, session, path, http_method, headers, params, json
        )


class SyncRPCFilterRequestBuilder(BaseRPCRequestBuilder, SyncSingleRequestBuilder):
    def __init__(
        self,
        session: Client,
        path: str,
        http_method: str,
        headers: Headers,
        params: QueryParams,
        json: JSON,
    ) -> None:
        BaseFilterRequestBuilder.__init__(self, headers, params)
        SyncSingleRequestBuilder.__init__(
            self, session, path, http_method, headers, params, json
        )


class SyncSelectRequestBuilder(SyncQueryRequestBuilder, BaseSelectRequestBuilder):
    def __init__(
        self,
        session: Client,
        path: str,
        http_method: str,
        headers: Headers,
        params: QueryParams,
        json: JSON,
    ) -> None:
        BaseSelectRequestBuilder.__init__(self, headers, params)
        SyncQueryRequestBuilder.__init__(
            self, session, path, http_method, headers, params, json
        )

    def single(self) -> SyncSingleRequestBuilder:
        """Specify that the query will only return a single row in response.

        .. caution::
            The API will raise an error if the query returned more than one row.
        """
        self.headers["Accept"] = "application/vnd.pgrst.object+json"
        return SyncSingleRequestBuilder(
            headers=self.headers,
            http_method=self.http_method,
            json=self.json,
            params=self.params,
            path=self.path,
            session=self.session,
        )

    def maybe_single(self) -> SyncMaybeSingleRequestBuilder:
        """Retrieves at most one row from the result. Result must be at most one row (e.g. using `eq` on a UNIQUE column), otherwise this will result in an error."""
        self.headers["Accept"] = "application/vnd.pgrst.object+json"
        return SyncMaybeSingleRequestBuilder(
            headers=self.headers,
            http_method=self.http_method,
            json=self.json,
            params=self.params,
            path=self.path,
            session=self.session,
        )

    def text_search(
        self, column: str, query: str, options: dict[str, Any] = {}
    ) -> SyncQueryRequestBuilder:
        type_ = options.get("type")
        type_part = ""
        if type_ == "plain":
            type_part = "pl"
        elif type_ == "phrase":
            type_part = "ph"
        elif type_ == "web_search":
            type_part = "w"
        config_part = f"({options.get('config')})" if options.get("config") else ""
        self.params = self.params.add(column, f"{type_part}fts{config_part}.{query}")

        return SyncQueryRequestBuilder(
            headers=self.headers,
            http_method=self.http_method,
            json=self.json,
            params=self.params,
            path=self.path,
            session=self.session,
        )

    def csv(self) -> SyncSingleRequestBuilder:
        """Specify that the query must retrieve data as a single CSV string."""
        self.headers["Accept"] = "text/csv"
        return SyncSingleRequestBuilder(
            session=self.session,
            path=self.path,
            http_method=self.http_method,
            headers=self.headers,
            params=self.params,
            json=self.json,
        )


class SyncRequestBuilder:
    def __init__(self, session: Client, path: str) -> None:
        self.session = session
        self.path = path

    def select(
        self,
        *columns: str,
        count: Optional[CountMethod] = None,
        head: Optional[bool] = None,
    ) -> SyncSelectRequestBuilder:
        """Run a SELECT query.

        Args:
            *columns: The names of the columns to fetch.
            count: The method to use to get the count of rows returned.
        Returns:
            :class:`SyncSelectRequestBuilder`
        """
        method, params, headers, json = pre_select(*columns, count=count, head=head)
        return SyncSelectRequestBuilder(
            self.session, self.path, method, headers, params, json
        )

    def insert(
        self,
        json: JSON,
        *,
        count: Optional[CountMethod] = None,
        returning: ReturnMethod = ReturnMethod.representation,
        upsert: bool = False,
        default_to_null: bool = True,
    ) -> SyncQueryRequestBuilder:
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
            :class:`SyncQueryRequestBuilder`
        """
        method, params, headers, json = pre_insert(
            json,
            count=count,
            returning=returning,
            upsert=upsert,
            default_to_null=default_to_null,
        )
        return SyncQueryRequestBuilder(
            self.session, self.path, method, headers, params, json
        )

    def upsert(
        self,
        json: JSON,
        *,
        count: Optional[CountMethod] = None,
        returning: ReturnMethod = ReturnMethod.representation,
        ignore_duplicates: bool = False,
        on_conflict: str = "",
        default_to_null: bool = True,
    ) -> SyncQueryRequestBuilder:
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
            :class:`SyncQueryRequestBuilder`
        """
        method, params, headers, json = pre_upsert(
            json,
            count=count,
            returning=returning,
            ignore_duplicates=ignore_duplicates,
            on_conflict=on_conflict,
            default_to_null=default_to_null,
        )
        return SyncQueryRequestBuilder(
            self.session, self.path, method, headers, params, json
        )

    def update(
        self,
        json: JSON,
        *,
        count: Optional[CountMethod] = None,
        returning: ReturnMethod = ReturnMethod.representation,
    ) -> SyncFilterRequestBuilder:
        """Run an UPDATE query.

        Args:
            json: The updated fields.
            count: The method to use to get the count of rows returned.
            returning: Either 'minimal' or 'representation'
        Returns:
            :class:`SyncFilterRequestBuilder`
        """
        method, params, headers, json = pre_update(
            json,
            count=count,
            returning=returning,
        )
        return SyncFilterRequestBuilder(
            self.session, self.path, method, headers, params, json
        )

    def delete(
        self,
        *,
        count: Optional[CountMethod] = None,
        returning: ReturnMethod = ReturnMethod.representation,
    ) -> SyncFilterRequestBuilder:
        """Run a DELETE query.

        Args:
            count: The method to use to get the count of rows returned.
            returning: Either 'minimal' or 'representation'
        Returns:
            :class:`SyncFilterRequestBuilder`
        """
        method, params, headers, json = pre_delete(
            count=count,
            returning=returning,
        )
        return SyncFilterRequestBuilder(
            self.session, self.path, method, headers, params, json
        )
