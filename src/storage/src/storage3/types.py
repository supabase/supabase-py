from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, TypeAdapter
from pydantic.dataclasses import dataclass
from typing_extensions import TypeAlias, TypedDict

RequestMethod = Literal["GET", "POST", "DELETE", "PUT", "HEAD"]


class Bucket(BaseModel, extra="ignore"):
    """Represents a file storage bucket."""

    id: str
    name: str
    owner: str
    public: bool
    created_at: datetime
    updated_at: datetime
    file_size_limit: Optional[int]
    allowed_mime_types: Optional[list[str]]
    type: Optional[Literal["STANDARD", "ANALYTICS"]]


class BucketName(BaseModel, extra="ignore"):
    name: str


# used in bucket.list method's option parameter
@dataclass
class SortByType:
    column: str = "name"
    order: Literal["asc", "desc"] = "asc"


class ListBody(BaseModel):
    prefix: str
    limit: int
    offset: int
    search: Optional[str]
    sortBy: SortByType


class SignedUploadUrlResponse(BaseModel):
    url: str
    token: str


@dataclass
class SignedUploadURL:
    signed_url: str
    token: str


@dataclass
class TransformOptions:
    height: Optional[int] = None
    width: Optional[int] = None
    resize: Optional[Literal["cover", "contain", "fill"]] = None
    format: Optional[Literal["origin", "avif"]] = None
    quality: Optional[int] = None


class CreateSignedUrlBody(BaseModel):
    expires_in: int
    download: Optional[Union[str, bool]]
    transform: Optional[TransformOptions]


class CreateSignedUrlsBody(BaseModel):
    paths: List[str]
    expires_in: int
    download: Optional[Union[str, bool]]


def transform_to_dict(t: TransformOptions) -> dict[str, str]:
    return {key: str(val) for key, val in t.items()}


class CreateOrUpdateBucketBody(BaseModel):
    id: str
    name: Optional[str]
    public: Optional[bool]
    file_size_limit: Optional[int]
    allowed_mime_types: Optional[list[str]]


class MessageResponse(BaseModel):
    message: str


class FileObject(BaseModel):
    id: str
    version: str
    name: str
    bucket_id: str
    updated_at: datetime
    created_at: datetime
    size: Optional[int] = None
    cache_control: Optional[str] = None
    content_type: Optional[str] = None
    etag: Optional[str]
    last_modified: Optional[str]
    metadata: Dict[str, Any]


class ListFileObject(BaseModel):
    id: str
    name: str
    owner: Optional[str] = None
    bucket_id: Optional[str] = None
    updated_at: datetime
    created_at: datetime
    metadata: Dict[str, Any]
    buckets: Optional[Bucket] = None


class UploadData(TypedDict, total=False):
    Id: str
    Key: str


class UploadResponse(BaseModel):
    Key: str


@dataclass
class CreateSignedUrlResponse:
    error: Optional[str]
    path: str
    signed_url: str


class SignedUrlJsonResponse(BaseModel, extra="ignore"):
    signedURL: str


class SignedUrlsJsonItem(BaseModel, extra="ignore"):
    error: Optional[str]
    path: str
    signedURL: str


SignedUrlsJsonResponse = TypeAdapter(list[SignedUrlsJsonItem])

DistanceMetric: TypeAlias = Literal["cosine", "euclidean"]


class MetadataConfiguration(BaseModel, extra="ignore"):
    non_filterable_metadata_keys: Optional[List[str]] = Field(
        alias="nonFilterableMetadataKeys"
    )


class ListIndexesOptions(BaseModel, extra="ignore"):
    nextToken: Optional[str] = None
    maxResults: Optional[int] = None
    prefix: Optional[str] = None


class ListIndexesResponseItem(BaseModel, extra="ignore"):
    indexName: str


class ListVectorIndexesResponse(BaseModel, extra="ignore"):
    indexes: List[ListIndexesResponseItem]
    nextToken: Optional[str] = None


class VectorIndex(BaseModel, extra="ignore"):
    index_name: str = Field(alias="indexName")
    bucket_name: str = Field(alias="vectorBucketName")
    data_type: str = Field(alias="dataType")
    dimension: int
    distance_metric: DistanceMetric = Field(alias="distanceMetric")
    metadata: Optional[MetadataConfiguration] = Field(
        alias="metadataConfiguration", default=None
    )
    creation_time: Optional[datetime] = None


class GetVectorIndexResponse(BaseModel, extra="ignore"):
    index: VectorIndex


VectorFilter = Dict[str, Any]


class VectorData(BaseModel, extra="ignore"):
    float32: List[float]


class VectorObject(BaseModel, extra="ignore"):
    key: str
    data: VectorData
    metadata: Optional[dict[str, Union[str, bool, float]]] = None


class VectorMatch(BaseModel, extra="ignore"):
    key: str
    data: Optional[VectorData] = None
    distance: Optional[float] = None
    metadata: Optional[dict[str, Any]] = None


class GetVectorsResponse(BaseModel, extra="ignore"):
    vectors: List[VectorMatch]


class ListVectorsResponse(BaseModel, extra="ignore"):
    vectors: List[VectorMatch]
    nextToken: Optional[str] = None


class QueryVectorsResponse(BaseModel, extra="ignore"):
    vectors: List[VectorMatch]


class AnalyticsBucket(BaseModel, extra="ignore"):
    name: str
    type: Optional[Literal["ANALYTICS"]] = None
    format: Optional[str] = None
    created_at: datetime
    updated_at: datetime


SortColumn = Literal["id", "name", "created_at", "updated_at"]
SortOrder = Literal["asc", "desc"]

AnalyticsBucketsParser = TypeAdapter(List[AnalyticsBucket])


class AnalyticsBucketDeleteResponse(BaseModel, extra="ignore"):
    message: str


class VectorBucketEncryptionConfiguration(BaseModel, extra="ignore"):
    kmsKeyArn: Optional[str] = None
    sseType: Optional[str] = None


class VectorBucket(BaseModel, extra="ignore"):
    vectorBucketName: str
    creationTime: Optional[datetime] = None
    encryptionConfiguration: Optional[VectorBucketEncryptionConfiguration] = None


class GetVectorBucketResponse(BaseModel, extra="ignore"):
    vectorBucket: VectorBucket


class ListVectorBucketsItem(BaseModel, extra="ignore"):
    vectorBucketName: str


class ListVectorBucketsResponse(BaseModel, extra="ignore"):
    vectorBuckets: List[ListVectorBucketsItem]
    nextToken: Optional[str] = None
