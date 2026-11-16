from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, TypeAdapter
from pydantic.dataclasses import dataclass
from supabase_utils.types import JSON


class Bucket(BaseModel, extra="ignore"):
    """Represents a file storage bucket."""

    id: str
    name: str
    owner: str
    public: bool
    created_at: datetime
    updated_at: datetime
    file_size_limit: int | None
    allowed_mime_types: list[str] | None
    type: Literal["STANDARD", "ANALYTICS"] | None = None


class BucketName(BaseModel, extra="ignore"):
    name: str


class SignedUploadUrlResponse(BaseModel):
    url: str
    token: str


@dataclass
class SignedUploadURL:
    signed_url: str
    token: str


@dataclass(frozen=True)
class TransformOptions:
    height: int | None = None
    width: int | None = None
    resize: Literal["cover", "contain", "fill"] | None = None
    format: Literal["origin", "avif"] | None = None
    quality: int | None = None


class CreateSignedUrlBody(BaseModel):
    expiresIn: int
    download: str | bool | None
    transform: TransformOptions | None


class CreateSignedUrlsBody(BaseModel):
    paths: list[str]
    expiresIn: int
    download: str | bool | None


def transform_to_dict(t: TransformOptions) -> dict[str, str]:
    return {key: str(val) for key, val in t.__dict__.items() if val}


class CreateOrUpdateBucketBody(BaseModel):
    id: str
    name: str | None
    public: bool | None
    file_size_limit: int | None
    allowed_mime_types: list[str] | None


class MessageResponse(BaseModel):
    message: str


class FileObject(BaseModel):
    id: str
    version: str
    name: str
    bucket_id: str
    created_at: datetime
    metadata: dict[str, Any]
    last_modified: datetime | None = None
    size: int | None = None
    cache_control: str | None = None
    content_type: str | None = None
    etag: str | None = None


@dataclass(frozen=True)
class SortBy:
    column: Literal["name", "updated_at", "created_at"] = "name"
    order: Literal["asc", "desc"] = "asc"


class ListBody(BaseModel):
    prefix: str | None = None
    limit: int | None = None
    cursor: str | None = None
    with_delimiter: bool | None = None
    sortBy: SortBy | None = None


class ListObject(BaseModel):
    """An object of a listing page. ``name`` is the full key."""

    id: str
    name: str
    created_at: datetime
    updated_at: datetime
    last_accessed_at: datetime | None = None
    metadata: dict[str, Any] | None
    key: str | None = None


class ListFolder(BaseModel):
    """A folder of a listing page. ``name`` is the full prefix ending in ``/``.

    The server sends a folder as a row with a null ``id`` and no metadata. Its
    timestamps, when present, are those of one of the objects below it.
    """

    name: str
    created_at: datetime | None = None
    updated_at: datetime | None = None
    last_accessed_at: datetime | None = None
    key: str | None = None


class ListResult(BaseModel):
    hasNext: bool
    folders: list[ListFolder]
    objects: list[ListObject]
    nextCursor: str | None = None


class UploadResponse(BaseModel):
    Key: str


@dataclass
class CreateSignedUrlResponse:
    error: str | None
    path: str
    signed_url: str | None


class SignedUrlJsonResponse(BaseModel, extra="ignore"):
    signedURL: str


class SignedUrlsJsonItem(BaseModel, extra="ignore"):
    error: str | None
    path: str
    signedURL: str | None


SignedUrlsJsonResponse = TypeAdapter(list[SignedUrlsJsonItem])

DistanceMetric = Literal["cosine", "euclidean"]


class MetadataConfiguration(BaseModel, extra="ignore"):
    non_filterable_metadata_keys: list[str] | None = Field(
        alias="nonFilterableMetadataKeys"
    )


class ListIndexesResponseItem(BaseModel, extra="ignore"):
    indexName: str


class ListVectorIndexesResponse(BaseModel, extra="ignore"):
    indexes: list[ListIndexesResponseItem]
    nextToken: str | None = None


class VectorIndex(BaseModel, extra="ignore"):
    index_name: str = Field(alias="indexName")
    bucket_name: str = Field(alias="vectorBucketName")
    data_type: str = Field(alias="dataType")
    dimension: int
    distance_metric: DistanceMetric = Field(alias="distanceMetric")
    metadata: MetadataConfiguration | None = Field(
        alias="metadataConfiguration", default=None
    )
    creation_time: datetime | None = Field(alias="creationTime", default=None)


class GetVectorIndexResponse(BaseModel, extra="ignore"):
    index: VectorIndex


VectorFilter = dict[str, Any]


class VectorData(BaseModel, extra="ignore"):
    float32: list[float]


class VectorObject(BaseModel, extra="ignore"):
    key: str
    data: VectorData
    metadata: dict[str, JSON] | None = None


class VectorMatch(BaseModel, extra="ignore"):
    key: str
    data: VectorData | None = None
    distance: float | None = None
    metadata: dict[str, JSON] | None = None


class GetVectorsResponse(BaseModel, extra="ignore"):
    vectors: list[VectorMatch]


class ListVectorsResponse(BaseModel, extra="ignore"):
    vectors: list[VectorMatch]
    nextToken: str | None = None


class QueryVectorsResponse(BaseModel, extra="ignore"):
    vectors: list[VectorMatch]


class AnalyticsBucket(BaseModel, extra="ignore"):
    name: str
    type: Literal["ANALYTICS"] | None = None
    format: str | None = None
    created_at: datetime
    updated_at: datetime


SortColumn = Literal["id", "name", "created_at", "updated_at"]
SortOrder = Literal["asc", "desc"]

AnalyticsBucketsParser = TypeAdapter(list[AnalyticsBucket])


class AnalyticsBucketDeleteResponse(BaseModel, extra="ignore"):
    message: str


class VectorBucketEncryptionConfiguration(BaseModel, extra="ignore"):
    kmsKeyArn: str | None = None
    sseType: str | None = None


class VectorBucket(BaseModel, extra="ignore"):
    vectorBucketName: str
    creationTime: datetime | None = None
    encryptionConfiguration: VectorBucketEncryptionConfiguration | None = None


class GetVectorBucketResponse(BaseModel, extra="ignore"):
    vectorBucket: VectorBucket


class ListVectorBucketsItem(BaseModel, extra="ignore"):
    vectorBucketName: str


class ListVectorBucketsResponse(BaseModel, extra="ignore"):
    vectorBuckets: list[ListVectorBucketsItem]
    nextToken: str | None = None
