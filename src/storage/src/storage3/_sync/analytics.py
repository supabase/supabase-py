from typing import List, Optional

from httpx import QueryParams

from ..types import (
    AnalyticsBucket,
    AnalyticsBucketDeleteResponse,
    AnalyticsBucketsParser,
    SortColumn,
    SortOrder,
)
from .request import SyncRequestBuilder


class SyncStorageAnalyticsClient:
    def __init__(self, request: SyncRequestBuilder) -> None:
        self._request = request

    def create(self, bucket_name: str) -> AnalyticsBucket:
        body = {"name": bucket_name}
        data = self._request.send(http_method="POST", path=["bucket"], body=body)
        return AnalyticsBucket.model_validate_json(data.content)

    def list(
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
        data = self._request.send(
            http_method="GET", path=["bucket"], query_params=filtered_params
        )
        return AnalyticsBucketsParser.validate_json(data.content)

    def delete(self, bucket_name: str) -> AnalyticsBucketDeleteResponse:
        data = self._request.send(http_method="DELETE", path=["bucket", bucket_name])
        return AnalyticsBucketDeleteResponse.model_validate_json(data.content)
