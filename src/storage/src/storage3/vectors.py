from __future__ import annotations

from dataclasses import dataclass
from typing import Generic, List

from httpx import Headers, Response
from supabase_utils.http import (
    Executor,
    JSONRequest,
    ResponseCases,
    ResponseHandler,
    handle_http_response,
    validate_model,
)
from supabase_utils.types import JSON
from yarl import URL

from .exceptions import VectorBucketException, parse_api_error
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
class VectorBucketScope(Generic[Executor]):
    base_url: URL
    _headers: Headers
    bucket_name: str
    executor: Executor

    def with_metadata(self, **data: JSON) -> JSON:
        return remove_none(vectorBucketName=self.bucket_name, **data)

    @handle_http_response
    def create_index(
        self,
        index_name: str,
        dimension: int,
        distance_metric: DistanceMetric,
        data_type: str,
        metadata: MetadataConfiguration | None = None,
    ) -> ResponseHandler[None]:
        body = self.with_metadata(
            indexName=index_name,
            dimension=dimension,
            distanceMetric=distance_metric,
            dataType=data_type,
            metadataConfiguration=metadata.model_dump(by_alias=True)
            if metadata
            else None,
        )
        request = JSONRequest(
            method="POST",
            path=["CreateIndex"],
            body=body,
            headers=self._headers,
        )
        return ResponseCases(
            request=request,
            on_success=lambda _request: None,
            on_failure=parse_api_error,
        )

    @handle_http_response
    def get_index(
        self, index_name: str
    ) -> ResponseHandler[GetVectorIndexResponse | None]:
        body = self.with_metadata(indexName=index_name)
        request = JSONRequest(
            method="POST",
            path=["GetIndex"],
            body=body,
            headers=self._headers,
        )

        def maybe_index(response: Response) -> GetVectorIndexResponse | None:
            if response.is_success:
                return GetVectorIndexResponse.model_validate_json(response.content)
            elif 400 <= response.status_code <= 401:
                return None
            else:
                raise parse_api_error(response)

        return ResponseHandler(
            request=request,
            callback=maybe_index,
        )

    @handle_http_response
    def list_indexes(
        self,
        next_token: str | None = None,
        max_results: int | None = None,
        prefix: str | None = None,
    ) -> ResponseHandler[ListVectorIndexesResponse]:
        body = self.with_metadata(
            next_token=next_token, max_results=max_results, prefix=prefix
        )
        request = JSONRequest(
            method="POST",
            path=["ListIndexes"],
            body=body,
            headers=self._headers,
        )
        return ResponseCases(
            request=request,
            on_success=validate_model(ListVectorIndexesResponse),
            on_failure=parse_api_error,
        )

    @handle_http_response
    def delete_index(self, index_name: str) -> ResponseHandler[None]:
        body = self.with_metadata(indexName=index_name)
        request = JSONRequest(
            method="POST", path=["DeleteIndex"], body=body, headers=self._headers
        )
        return ResponseCases(
            request=request,
            on_success=lambda _response: None,
            on_failure=parse_api_error,
        )

    def index(self, index_name: str) -> VectorIndexScope[Executor]:
        return VectorIndexScope(
            bucket_name=self.bucket_name,
            index_name=index_name,
            base_url=self.base_url,
            executor=self.executor,
            _headers=self._headers,
        )


@dataclass
class VectorIndexScope(Generic[Executor]):
    executor: Executor
    bucket_name: str
    index_name: str
    _headers: Headers
    base_url: URL

    def with_metadata(self, **data: JSON) -> JSON:
        return remove_none(
            vectorBucketName=self.bucket_name,
            indexName=self.index_name,
            **data,
        )

    @handle_http_response
    def put(self, vectors: List[VectorObject]) -> ResponseHandler[None]:
        body = self.with_metadata(
            vectors=[v.model_dump(exclude_none=True) for v in vectors]
        )
        request = JSONRequest(
            method="POST", path=["PutVectors"], body=body, headers=self._headers
        )
        return ResponseCases(
            request=request,
            on_success=lambda _request: None,
            on_failure=parse_api_error,
        )

    @handle_http_response
    def get(
        self, *keys: str, return_data: bool = True, return_metadata: bool = True
    ) -> ResponseHandler[GetVectorsResponse]:
        body = self.with_metadata(
            keys=keys,
            returnData=return_data,
            returnMetadata=return_metadata,
        )
        request = JSONRequest(
            method="POST",
            path=["GetVectors"],
            body=body,
            headers=self._headers,
        )
        return ResponseCases(
            request=request,
            on_success=validate_model(GetVectorsResponse),
            on_failure=parse_api_error,
        )

    @handle_http_response
    def list(
        self,
        max_results: int | None = None,
        next_token: str | None = None,
        return_data: bool = True,
        return_metadata: bool = True,
        segment_count: int | None = None,
        segment_index: int | None = None,
    ) -> ResponseHandler[ListVectorsResponse]:
        body = self.with_metadata(
            maxResults=max_results,
            nextToken=next_token,
            returnData=return_data,
            returnMetadata=return_metadata,
            segmentCount=segment_count,
            segmentIndex=segment_index,
        )
        request = JSONRequest(
            method="POST", path=["ListVectors"], body=body, headers=self._headers
        )
        return ResponseCases(
            request=request,
            on_success=validate_model(ListVectorsResponse),
            on_failure=parse_api_error,
        )

    @handle_http_response
    def query(
        self,
        query_vector: VectorData,
        topK: int | None = None,
        filter: VectorFilter | None = None,
        return_distance: bool = True,
        return_metadata: bool = True,
    ) -> ResponseHandler[QueryVectorsResponse]:
        body = self.with_metadata(
            queryVector=dict(query_vector),
            topK=topK,
            filter=filter,
            returnDistance=return_distance,
            returnMetadata=return_metadata,
        )
        request = JSONRequest(
            method="POST",
            path=["QueryVectors"],
            body=body,
            headers=self._headers,
        )
        return ResponseCases(
            request=request,
            on_success=validate_model(QueryVectorsResponse),
            on_failure=parse_api_error,
        )

    @handle_http_response
    def delete(self, keys: List[str]) -> ResponseHandler[None]:
        if len(keys) < 1 or len(keys) > 500:
            raise VectorBucketException("Keys batch size must be between 1 and 500.")
        body = self.with_metadata(keys=keys)
        request = JSONRequest(
            method="POST", path=["DeleteVectors"], body=body, headers=self._headers
        )
        return ResponseCases(
            request=request,
            on_success=lambda _request: None,
            on_failure=parse_api_error,
        )


@dataclass
class StorageVectorsClient(Generic[Executor]):
    base_url: URL
    _headers: Headers
    executor: Executor

    def from_(self, bucket_name: str) -> VectorBucketScope[Executor]:
        return VectorBucketScope(
            bucket_name=bucket_name,
            base_url=self.base_url,
            _headers=self._headers,
            executor=self.executor,
        )

    @handle_http_response
    def create_bucket(self, bucket_name: str) -> ResponseHandler[None]:
        body = {"vectorBucketName": bucket_name}
        request = JSONRequest(
            method="POST",
            path=["CreateVectorBucket"],
            body=body,
            headers=self._headers,
        )
        return ResponseCases(
            request=request,
            on_success=lambda _request: None,
            on_failure=parse_api_error,
        )

    @handle_http_response
    def get_bucket(
        self, bucket_name: str
    ) -> ResponseHandler[GetVectorBucketResponse | None]:
        body = {"vectorBucketName": bucket_name}
        request = JSONRequest(
            method="POST",
            path=["GetVectorBucket"],
            body=body,
            headers=self._headers,
        )

        def maybe_vector_bucket(
            response: Response,
        ) -> GetVectorBucketResponse | None:
            if response.is_success:
                return GetVectorBucketResponse.model_validate_json(response.content)
            elif 400 <= response.status_code <= 401:
                return None
            else:
                raise parse_api_error(response)

        return ResponseHandler(
            request=request,
            callback=maybe_vector_bucket,
        )

    @handle_http_response
    def list_buckets(
        self,
        prefix: str | None = None,
        max_results: int | None = None,
        next_token: str | None = None,
    ) -> ResponseHandler[ListVectorBucketsResponse]:
        body = {"prefix": prefix, "maxResults": max_results, "nextToken": next_token}
        request = JSONRequest(
            method="POST",
            path=["ListVectorBuckets"],
            body=body,
            headers=self._headers,
            exclude_none=True,
        )
        return ResponseCases(
            request=request,
            on_success=validate_model(ListVectorBucketsResponse),
            on_failure=parse_api_error,
        )

    @handle_http_response
    def delete_bucket(self, bucket_name: str) -> ResponseHandler[None]:
        body = {"vectorBucketName": bucket_name}
        request = JSONRequest(
            method="POST",
            path=["DeleteVectorBucket"],
            body=body,
            headers=self._headers,
        )
        return ResponseCases(
            request=request,
            on_success=lambda _request: None,
            on_failure=parse_api_error,
        )
