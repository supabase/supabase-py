from dataclasses import dataclass
from typing import Generic, List

from httpx import Headers, QueryParams
from pyiceberg.catalog.rest import RestCatalog
from supabase_utils.http import (
    EmptyRequest,
    Executor,
    JSONRequest,
    ResponseCases,
    ResponseHandler,
    handle_http_response,
    validate_adapter,
    validate_model,
)
from yarl import URL

from .exceptions import parse_api_error
from .types import (
    AnalyticsBucket,
    AnalyticsBucketDeleteResponse,
    AnalyticsBucketsParser,
    SortColumn,
    SortOrder,
)


@dataclass
class StorageAnalyticsClient(Generic[Executor]):
    _headers: Headers
    base_url: URL
    executor: Executor

    @handle_http_response
    def create(self, bucket_name: str) -> ResponseHandler[AnalyticsBucket]:
        body = {"name": bucket_name}
        request = JSONRequest(
            method="POST",
            path=["bucket"],
            body=body,
            headers=self._headers,
        )
        return ResponseCases(
            request=request,
            on_success=validate_model(AnalyticsBucket),
            on_failure=parse_api_error,
        )

    @handle_http_response
    def list(
        self,
        limit: int | None = None,
        offset: int | None = None,
        sort_column: SortColumn | None = None,
        sort_order: SortOrder | None = None,
        search: str | None = None,
    ) -> ResponseHandler[List[AnalyticsBucket]]:
        params = dict(
            limit=limit,
            offset=offset,
            sort_column=sort_column,
            sort_order=sort_order,
            search=search,
        )
        filtered_params = QueryParams(
            **{k: v for k, v in params.items() if v is not None}
        )
        request = EmptyRequest(
            method="GET",
            path=["bucket"],
            query_params=filtered_params,
            headers=self._headers,
        )
        return ResponseCases(
            request=request,
            on_success=validate_adapter(AnalyticsBucketsParser),
            on_failure=parse_api_error,
        )

    @handle_http_response
    def delete(
        self, bucket_name: str
    ) -> ResponseHandler[AnalyticsBucketDeleteResponse]:
        request = EmptyRequest(
            method="DELETE",
            path=["bucket", bucket_name],
            headers=self._headers,
        )
        return ResponseCases(
            request=request,
            on_success=validate_model(AnalyticsBucketDeleteResponse),
            on_failure=parse_api_error,
        )

    def catalog(
        self, catalog_name: str, access_key_id: str, secret_access_key: str
    ) -> RestCatalog:
        catalog_uri = self.base_url
        s3_endpoint = self.base_url.parent.joinpath("s3")
        service_key = self._headers.get("apiKey")
        assert service_key, "apiKey must be passed in the headers."
        return RestCatalog(
            catalog_name,
            warehouse=catalog_name,
            uri=str(catalog_uri),
            token=service_key,
            **{
                "py-io-impl": "pyiceberg.io.pyarrow.PyArrowFileIO",
                "s3.endpoint": str(s3_endpoint),
                "s3.access-key-id": access_key_id,
                "s3.secret-access-key": secret_access_key,
                "s3.force-virtual-addressing": "False",
            },
        )
