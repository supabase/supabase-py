from __future__ import annotations

from typing import List, Optional

from httpx import Client, Headers
from yarl import URL

from ..exceptions import StorageApiError, VectorBucketException
from ..types import (
    JSON,
    DistanceMetric,
    GetVectorBucketResponse,
    GetVectorIndexResponse,
    GetVectorsResponse,
    ListVectorBucketsResponse,
    ListVectorIndexesResponse,
    ListVectorsResponse,
    MetadataConfiguration,
    QueryVectorsResponse,
    VectorData,
    VectorFilter,
    VectorObject,
)
from .request import SyncRequestBuilder


# used to not send non-required values as `null`
# for they cannot be null
def remove_none(**kwargs: JSON) -> JSON:
    return {key: val for key, val in kwargs.items() if val is not None}


class SyncVectorBucketScope:
    def __init__(self, request: SyncRequestBuilder, bucket_name: str) -> None:
        self._request = request
        self._bucket_name = bucket_name

    def with_metadata(self, **data: JSON) -> JSON:
        return remove_none(vectorBucketName=self._bucket_name, **data)

    def create_index(
        self,
        index_name: str,
        dimension: int,
        distance_metric: DistanceMetric,
        data_type: str,
        metadata: Optional[MetadataConfiguration] = None,
    ) -> None:
        body = self.with_metadata(
            indexName=index_name,
            dimension=dimension,
            distanceMetric=distance_metric,
            dataType=data_type,
            metadataConfiguration=metadata.model_dump(by_alias=True)
            if metadata
            else None,
        )
        self._request.send(http_method="POST", path=["CreateIndex"], body=body)

    def get_index(self, index_name: str) -> Optional[GetVectorIndexResponse]:
        body = self.with_metadata(indexName=index_name)
        try:
            data = self._request.send(http_method="POST", path=["GetIndex"], body=body)
            return GetVectorIndexResponse.model_validate_json(data.content)
        except StorageApiError:
            return None

    def list_indexes(
        self,
        next_token: Optional[str] = None,
        max_results: Optional[int] = None,
        prefix: Optional[str] = None,
    ) -> ListVectorIndexesResponse:
        body = self.with_metadata(
            next_token=next_token, max_results=max_results, prefix=prefix
        )
        data = self._request.send(http_method="POST", path=["ListIndexes"], body=body)
        return ListVectorIndexesResponse.model_validate_json(data.content)

    def delete_index(self, index_name: str) -> None:
        body = self.with_metadata(indexName=index_name)
        self._request.send(http_method="POST", path=["DeleteIndex"], body=body)

    def index(self, index_name: str) -> SyncVectorIndexScope:
        return SyncVectorIndexScope(self._request, self._bucket_name, index_name)


class SyncVectorIndexScope:
    def __init__(
        self, request: SyncRequestBuilder, bucket_name: str, index_name: str
    ) -> None:
        self._request = request
        self._bucket_name = bucket_name
        self._index_name = index_name

    def with_metadata(self, **data: JSON) -> JSON:
        return remove_none(
            vectorBucketName=self._bucket_name,
            indexName=self._index_name,
            **data,
        )

    def put(self, vectors: List[VectorObject]) -> None:
        body = self.with_metadata(
            vectors=[v.model_dump(exclude_none=True) for v in vectors]
        )
        self._request.send(http_method="POST", path=["PutVectors"], body=body)

    def get(
        self, *keys: str, return_data: bool = True, return_metadata: bool = True
    ) -> GetVectorsResponse:
        body = self.with_metadata(
            keys=keys, returnData=return_data, returnMetadata=return_metadata
        )
        data = self._request.send(http_method="POST", path=["GetVectors"], body=body)
        return GetVectorsResponse.model_validate_json(data.content)

    def list(
        self,
        max_results: Optional[int] = None,
        next_token: Optional[str] = None,
        return_data: bool = True,
        return_metadata: bool = True,
        segment_count: Optional[int] = None,
        segment_index: Optional[int] = None,
    ) -> ListVectorsResponse:
        body = self.with_metadata(
            maxResults=max_results,
            nextToken=next_token,
            returnData=return_data,
            returnMetadata=return_metadata,
            segmentCount=segment_count,
            segmentIndex=segment_index,
        )
        data = self._request.send(http_method="POST", path=["ListVectors"], body=body)
        return ListVectorsResponse.model_validate_json(data.content)

    def query(
        self,
        query_vector: VectorData,
        topK: Optional[int] = None,
        filter: Optional[VectorFilter] = None,
        return_distance: bool = True,
        return_metadata: bool = True,
    ) -> QueryVectorsResponse:
        body = self.with_metadata(
            queryVector=dict(query_vector),
            topK=topK,
            filter=filter,
            returnDistance=return_distance,
            returnMetadata=return_metadata,
        )
        data = self._request.send(http_method="POST", path=["QueryVectors"], body=body)
        return QueryVectorsResponse.model_validate_json(data.content)

    def delete(self, keys: List[str]) -> None:
        if len(keys) < 1 or len(keys) > 500:
            raise VectorBucketException("Keys batch size must be between 1 and 500.")
        body = self.with_metadata(keys=keys)
        self._request.send(http_method="POST", path=["DeleteVectors"], body=body)


class SyncStorageVectorsClient:
    def __init__(self, url: URL, headers: Headers, session: Client) -> None:
        self._request = SyncRequestBuilder(session, base_url=URL(url), headers=headers)

    def from_(self, bucket_name: str) -> SyncVectorBucketScope:
        return SyncVectorBucketScope(self._request, bucket_name)

    def create_bucket(self, bucket_name: str) -> None:
        body = {"vectorBucketName": bucket_name}
        self._request.send(http_method="POST", path=["CreateVectorBucket"], body=body)

    def get_bucket(self, bucket_name: str) -> Optional[GetVectorBucketResponse]:
        body = {"vectorBucketName": bucket_name}
        try:
            data = self._request.send(
                http_method="POST", path=["GetVectorBucket"], body=body
            )
            return GetVectorBucketResponse.model_validate_json(data.content)
        except StorageApiError:
            return None

    def list_buckets(
        self,
        prefix: Optional[str] = None,
        max_results: Optional[int] = None,
        next_token: Optional[str] = None,
    ) -> ListVectorBucketsResponse:
        body = remove_none(prefix=prefix, maxResults=max_results, nextToken=next_token)
        data = self._request.send(
            http_method="POST", path=["ListVectorBuckets"], body=body
        )
        return ListVectorBucketsResponse.model_validate_json(data.content)

    def delete_bucket(self, bucket_name: str) -> None:
        body = {"vectorBucketName": bucket_name}
        self._request.send(http_method="POST", path=["DeleteVectorBucket"], body=body)
