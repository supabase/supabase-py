from __future__ import annotations

from typing import List, Optional

from httpx import AsyncClient, Headers, Response
from yarl import URL

from ..exceptions import VectorBucketException
from ..types import (
    JSON,
    DistanceMetric,
    GetVectorsResponse,
    ListIndexesResponse,
    ListVectorsResponse,
    MetadataConfiguration,
    QueryVectorsResponse,
    RequestMethod,
    VectorData,
    VectorFilter,
    VectorIndex,
    VectorObject,
)


class PartialRequest:
    def __init__(self, session: AsyncClient, base_url: URL, headers: Headers) -> None:
        self._session = session
        self._base_url = base_url
        self.headers = headers

    async def send(
        self, http_method: RequestMethod, path: list[str], body: JSON = None
    ) -> Response:
        return await self._session.request(
            method=http_method,
            json=body,
            url=str(self._base_url.joinpath(*path)),
            headers=self.headers,
        )


class AsyncVectorBucketScope:
    def __init__(self, request: PartialRequest, bucket_name: str) -> None:
        self._request = request
        self._bucket_name = bucket_name

    def with_metadata(self, **data: JSON) -> JSON:
        return {"vectorBucketName": self._bucket_name, **data}

    async def create_index(
        self,
        dimension: int,
        distance_metric: DistanceMetric,
        data_type: str,
        metadata: Optional[MetadataConfiguration] = None,
    ) -> None:
        body = self.with_metadata(
            dimension=dimension,
            distanceMetric=distance_metric,
            dataType=data_type,
            metadataConfiguration=dict(metadata) if metadata else None,
        )
        await self._request.send(http_method="POST", path=["CreateIndex"], body=body)

    async def get_index(self, index_name: str) -> VectorIndex:
        body = self.with_metadata(indexName=index_name)
        data = self._request.send(http_method="POST", path=["GetIndex"], body=body)
        return VectorIndex.model_validate(data)

    async def list_indexes(
        self,
        next_token: Optional[str] = None,
        max_results: Optional[int] = None,
        prefix: Optional[str] = None,
    ) -> ListIndexesResponse:
        body = self.with_metadata(
            next_token=next_token, max_results=max_results, prefix=prefix
        )
        data = self._request.send(http_method="POST", path=["ListIndexes"], body=body)
        return ListIndexesResponse.model_validate(data)

    async def delete_index(self, index_name: str) -> None:
        body = self.with_metadata(indexName=index_name)
        await self._request.send(http_method="POST", path=["DeleteIndex"], body=body)

    def index(self, index_name: str) -> AsyncVectorIndexScope:
        return AsyncVectorIndexScope(self._request, self._bucket_name, index_name)


class AsyncVectorIndexScope:
    def __init__(
        self, request: PartialRequest, bucket_name: str, index_name: str
    ) -> None:
        self._request = request
        self._bucket_name = bucket_name
        self._index_name = index_name

    def with_metadata(self, **data: JSON) -> JSON:
        return {
            "vectorBucketName": self._bucket_name,
            "indexName": self._index_name,
            **data,
        }

    async def put(self, vectors: List[VectorObject]) -> None:
        body = self.with_metadata(vectors=list(dict(v) for v in vectors))
        await self._request.send(http_method="POST", path=["PutVectors"], body=body)

    async def get(
        self, *keys: str, return_data: bool = True, return_metadata: bool = True
    ) -> GetVectorsResponse:
        body = self.with_metadata(
            keys=keys, returnData=return_data, returnMetadata=return_metadata
        )
        data = self._request.send(http_method="POST", path=["GetVectors"], body=body)
        return GetVectorsResponse.model_validate(data)

    async def list(
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
        data = await self._request.send(
            http_method="POST", path=["ListVectors"], body=body
        )
        return ListVectorsResponse.model_validate(data)

    async def query(
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
        data = await self._request.send(
            http_method="POST", path=["QueryVectors"], body=body
        )
        return QueryVectorsResponse.model_validate(data)

    async def delete(self, keys: List[str]) -> None:
        if 1 < len(keys) or len(keys) > 500:
            raise VectorBucketException("Keys batch size must be between 1 and 500.")
        body = self.with_metadata(keys=keys)
        await self._request.send(http_method="POST", path=["DeleteVectors"], body=body)


class AsyncStorageVectorsClient:
    def __init__(self, url: str, headers: Headers, session: AsyncClient) -> None:
        if url and url[-1] != "/":
            print("Storage endpoint URL should have a trailing slash.")
            url += "/"
        self._request = PartialRequest(session, base_url=URL(url), headers=headers)

    def from_(self, bucket_name: str) -> AsyncVectorBucketScope:
        return AsyncVectorBucketScope(self._request, bucket_name)
