from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, List

from supabase_utils.http.headers import Headers
from supabase_utils.http.io import (
    HttpIO,
    HttpMethod,
    handle_http_io,
)
from supabase_utils.http.request import JSONRequest
from supabase_utils.types import JSON
from yarl import URL

from .exceptions import VectorBucketException, parse_api_error, validate_model
from .types import (
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


# used to not send non-required values as `null`
# for they cannot be null
def remove_none(**kwargs: JSON) -> JSON:
    return {key: val for key, val in kwargs.items() if val is not None}


@dataclass
class VectorBucketScope(Generic[HttpIO]):
    base_url: URL
    default_headers: Headers
    bucket_name: str
    executor: HttpIO

    def with_metadata(self, **data: JSON) -> JSON:
        return remove_none(vectorBucketName=self.bucket_name, **data)

    @handle_http_io
    def create_index(
        self,
        index_name: str,
        dimension: int,
        distance_metric: DistanceMetric,
        data_type: str,
        metadata: MetadataConfiguration | None = None,
    ) -> HttpMethod[None]:
        body = self.with_metadata(
            indexName=index_name,
            dimension=dimension,
            distanceMetric=distance_metric,
            dataType=data_type,
            metadataConfiguration=metadata.model_dump(by_alias=True)
            if metadata
            else None,
        )
        response = yield JSONRequest(
            method="POST",
            path=["CreateIndex"],
            body=body,
        )
        if not response.is_success:
            raise parse_api_error(response)

    @handle_http_io
    def get_index(self, index_name: str) -> HttpMethod[GetVectorIndexResponse | None]:
        body = self.with_metadata(indexName=index_name)
        response = yield JSONRequest(
            method="POST",
            path=["GetIndex"],
            body=body,
        )
        if response.is_success:
            return GetVectorIndexResponse.model_validate_json(response.content)
        elif 400 <= response.status <= 401:
            return None
        else:
            raise parse_api_error(response)

    @handle_http_io
    def list_indexes(
        self,
        next_token: str | None = None,
        max_results: int | None = None,
        prefix: str | None = None,
    ) -> HttpMethod[ListVectorIndexesResponse]:
        body = self.with_metadata(
            next_token=next_token, max_results=max_results, prefix=prefix
        )
        response = yield JSONRequest(
            method="POST",
            path=["ListIndexes"],
            body=body,
        )
        return validate_model(response, ListVectorIndexesResponse)

    @handle_http_io
    def delete_index(self, index_name: str) -> HttpMethod[None]:
        body = self.with_metadata(indexName=index_name)
        response = yield JSONRequest(method="POST", path=["DeleteIndex"], body=body)
        if not response.is_success:
            raise parse_api_error(response)

    def index(self, index_name: str) -> VectorIndexScope[HttpIO]:
        return VectorIndexScope(
            bucket_name=self.bucket_name,
            index_name=index_name,
            base_url=self.base_url,
            executor=self.executor,
            default_headers=self.default_headers,
        )


@dataclass
class VectorIndexScope(Generic[HttpIO]):
    executor: HttpIO
    bucket_name: str
    index_name: str
    default_headers: Headers
    base_url: URL

    def with_metadata(self, **data: JSON) -> JSON:
        return remove_none(
            vectorBucketName=self.bucket_name,
            indexName=self.index_name,
            **data,
        )

    @handle_http_io
    def put(self, vectors: List[VectorObject]) -> HttpMethod[None]:
        body = self.with_metadata(
            vectors=[v.model_dump(exclude_none=True) for v in vectors]
        )
        response = yield JSONRequest(
            method="POST",
            path=["PutVectors"],
            body=body,
        )
        if not response.is_success:
            raise parse_api_error(response)

    @handle_http_io
    def get(
        self, *keys: str, return_data: bool = True, return_metadata: bool = True
    ) -> HttpMethod[GetVectorsResponse]:
        body = self.with_metadata(
            keys=keys,
            returnData=return_data,
            returnMetadata=return_metadata,
        )
        response = yield JSONRequest(
            method="POST",
            path=["GetVectors"],
            body=body,
        )
        return validate_model(response, GetVectorsResponse)

    @handle_http_io
    def list(
        self,
        max_results: int | None = None,
        next_token: str | None = None,
        return_data: bool = True,
        return_metadata: bool = True,
        segment_count: int | None = None,
        segment_index: int | None = None,
    ) -> HttpMethod[ListVectorsResponse]:
        body = self.with_metadata(
            maxResults=max_results,
            nextToken=next_token,
            returnData=return_data,
            returnMetadata=return_metadata,
            segmentCount=segment_count,
            segmentIndex=segment_index,
        )
        response = yield JSONRequest(
            method="POST",
            path=["ListVectors"],
            body=body,
        )
        return validate_model(response, ListVectorsResponse)

    @handle_http_io
    def query(
        self,
        query_vector: VectorData,
        topK: int | None = None,
        filter: VectorFilter | None = None,
        return_distance: bool = True,
        return_metadata: bool = True,
    ) -> HttpMethod[QueryVectorsResponse]:
        body = self.with_metadata(
            queryVector=dict(query_vector),
            topK=topK,
            filter=filter,
            returnDistance=return_distance,
            returnMetadata=return_metadata,
        )
        response = yield JSONRequest(
            method="POST",
            path=["QueryVectors"],
            body=body,
        )
        return validate_model(response, QueryVectorsResponse)

    @handle_http_io
    def delete(self, keys: List[str]) -> HttpMethod[None]:
        if len(keys) < 1 or len(keys) > 500:
            raise VectorBucketException("Keys batch size must be between 1 and 500.")
        body = self.with_metadata(keys=keys)
        response = yield JSONRequest(
            method="POST",
            path=["DeleteVectors"],
            body=body,
        )
        if not response.is_success:
            raise parse_api_error(response)


@dataclass
class StorageVectorsClient(Generic[HttpIO]):
    base_url: URL
    default_headers: Headers
    executor: HttpIO

    def from_(self, bucket_name: str) -> VectorBucketScope[HttpIO]:
        return VectorBucketScope(
            bucket_name=bucket_name,
            base_url=self.base_url,
            executor=self.executor,
            default_headers=self.default_headers,
        )

    @handle_http_io
    def create_bucket(self, bucket_name: str) -> HttpMethod[None]:
        body = {"vectorBucketName": bucket_name}
        response = yield JSONRequest(
            method="POST",
            path=["CreateVectorBucket"],
            body=body,
        )
        if not response.is_success:
            raise parse_api_error(response)

    @handle_http_io
    def get_bucket(
        self, bucket_name: str
    ) -> HttpMethod[GetVectorBucketResponse | None]:
        body = {"vectorBucketName": bucket_name}
        response = yield JSONRequest(
            method="POST",
            path=["GetVectorBucket"],
            body=body,
        )
        if response.is_success:
            return GetVectorBucketResponse.model_validate_json(response.content)
        elif 400 <= response.status <= 401:
            return None
        else:
            raise parse_api_error(response)

    @handle_http_io
    def list_buckets(
        self,
        prefix: str | None = None,
        max_results: int | None = None,
        next_token: str | None = None,
    ) -> HttpMethod[ListVectorBucketsResponse]:
        body = {"prefix": prefix, "maxResults": max_results, "nextToken": next_token}
        response = yield JSONRequest(
            method="POST",
            path=["ListVectorBuckets"],
            body=body,
            exclude_none=True,
        )
        return validate_model(response, ListVectorBucketsResponse)

    @handle_http_io
    def delete_bucket(self, bucket_name: str) -> HttpMethod[None]:
        body = {"vectorBucketName": bucket_name}
        response = yield JSONRequest(
            method="POST",
            path=["DeleteVectorBucket"],
            body=body,
        )
        if not response.is_success:
            raise parse_api_error(response)
