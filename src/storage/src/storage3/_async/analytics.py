from typing import List, Optional

from httpx import QueryParams

from ..types import (
    AnalyticsBucket,
    AnalyticsBucketDeleteResponse,
    AnalyticsBucketsParser,
    SortColumn,
    SortOrder,
)
from .request import RequestBuilder


class AsyncStorageAnalyticsClient:
    def __init__(self, request: RequestBuilder) -> None:
        self._request = request

    async def create(self, bucket_name: str) -> AnalyticsBucket:
        body = {"name": bucket_name}
        data = await self._request.send(http_method="POST", path=["bucket"], body=body)
        return AnalyticsBucket.model_validate(data.content)

    async def list(
        self,
        limit: Optional[int] = None,
        offset: Optional[int] = None,
        sort_column: Optional[SortColumn] = None,
        sort_order: Optional[SortOrder] = None,
        search: Optional[str] = None,
    ) -> List[AnalyticsBucket]:
        params = QueryParams(
            limit=limit,
            offset=offset,
            sort_column=sort_column,
            sort_order=sort_order,
            search=search,
        )
        data = await self._request.send(
            http_method="GET", path=["bucket"], query_params=params
        )
        return AnalyticsBucketsParser.validate_json(data.content)

    async def delete(self, bucket_name: str) -> AnalyticsBucketDeleteResponse:
        data = await self._request.send(
            http_method="DELETE", path=["bucket", bucket_name]
        )
        return AnalyticsBucketDeleteResponse.model_validate(data.content)
