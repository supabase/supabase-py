from __future__ import annotations

from collections.abc import AsyncIterable, Iterable
from datetime import datetime
from os import PathLike
from typing import Any, BinaryIO, Literal

from pydantic import (
    AliasChoices,
    BaseModel,
    ConfigDict,
    Field,
    SerializerFunctionWrapHandler,
    TypeAdapter,
    model_serializer,
)
from pydantic.dataclasses import dataclass
from supabase_utils.types import JSON

type UploadBody = (
    bytes | str | PathLike[str] | BinaryIO | Iterable[bytes] | AsyncIterable[bytes]
)
"""What an upload sends: the bytes themselves, the path of a file as a `str`
or `Path`, a binary file opened for reading, or an iterator over the bytes.
A file is streamed from disk, and an iterator is streamed as it is read. Only
the async client takes an async iterator."""


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


LifecycleRuleStatus = Literal["Enabled", "Disabled"]


class NoncurrentVersionExpiration(BaseModel):
    """When a lifecycle rule deletes the previous versions of an object.

    ``noncurrent_days`` is how many days a version is kept after a newer one
    replaces it. ``newer_noncurrent_versions`` is how many of the newest
    previous versions are kept regardless of their age; ``None`` keeps none.
    """

    model_config = ConfigDict(
        extra="ignore", frozen=True, validate_by_name=True, serialize_by_alias=True
    )

    noncurrent_days: int = Field(alias="noncurrentDays")
    newer_noncurrent_versions: int | None = Field(
        default=None, alias="newerNoncurrentVersions"
    )


class LifecycleRule(BaseModel):
    """A rule of a bucket's lifecycle policy.

    A rule applies to every object in the bucket. Its only action,
    ``noncurrent_version_expiration``, has nothing to delete until versioning
    has kept previous versions. Storage generates an ``id`` for a rule that
    has none. ``status`` is ``"Enabled"`` or ``"Disabled"``.
    """

    model_config = ConfigDict(
        extra="ignore", frozen=True, validate_by_name=True, serialize_by_alias=True
    )

    noncurrent_version_expiration: NoncurrentVersionExpiration = Field(
        alias="noncurrentVersionExpiration"
    )
    id: str | None = None
    status: LifecycleRuleStatus | str = "Enabled"

    @model_serializer(mode="wrap")
    def _serialize_with_filter(
        self, handler: SerializerFunctionWrapHandler
    ) -> dict[str, Any]:
        return {**handler(self), "filter": {}}


class _LifecycleConfiguration(BaseModel, extra="ignore"):
    rules: list[LifecycleRule]


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
    """An object of a listing page. ``name`` is the full key.

    ``created_at`` and ``last_accessed_at`` are ``None`` on Supabase Storage
    releases before v1.27.0, which do not send them.
    """

    id: str
    name: str
    created_at: datetime | None = None
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
    """The object written by an upload, update or copy.

    ``path`` is the object key within the bucket and ``full_path`` is prefixed
    with the bucket name. ``id`` is ``None`` for an upload to a signed URL,
    whose response has no object id.
    """

    id: str | None
    path: str
    full_path: str
    version: str | None


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
        default=None,
        validation_alias=AliasChoices(
            "non_filterable_metadata_keys", "nonFilterableMetadataKeys"
        ),
        serialization_alias="nonFilterableMetadataKeys",
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
