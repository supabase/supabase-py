from typing import List, Optional

from httpx import QueryParams
from pyiceberg.catalog.rest import RestCatalog

from ..types import (
    AnalyticsBucket,
    AnalyticsBucketDeleteResponse,
    AnalyticsBucketsParser,
    SortColumn,
    SortOrder,
)
from .request import AsyncRequestBuilder


class AsyncStorageAnalyticsClient:
    def __init__(self, request: AsyncRequestBuilder) -> None:
        self._request = request

    async def create(self, bucket_name: str) -> AnalyticsBucket:
        body = {"name": bucket_name}
        data = await self._request.send(http_method="POST", path=["bucket"], body=body)
        return AnalyticsBucket.model_validate_json(data.content)

    async def list(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        sort_column: Optional[SortColumn] = None,
        sort_order: Optional[SortOrder] = None,
        search: Optional[str] = None,
    ) -> List[AnalyticsBucket]:
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
        data = await self._request.send(
            http_method="GET", path=["bucket"], query_params=filtered_params
        )
        return AnalyticsBucketsParser.validate_json(data.content)

    async def delete(self, bucket_name: str) -> AnalyticsBucketDeleteResponse:
        data = await self._request.send(
            http_method="DELETE", path=["bucket", bucket_name]
        )
        return AnalyticsBucketDeleteResponse.model_validate_json(data.content)

    def catalog(
        self, catalog_name: str, access_key_id: str, secret_access_key: str
    ) -> RestCatalog:
        catalog_uri = self._request._base_url
        s3_endpoint = self._request._base_url.parent.joinpath("s3")
        service_key = self._request.headers.get("apiKey")
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
