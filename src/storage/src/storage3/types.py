from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Literal, TypeAlias, TypedDict

from pydantic import AliasChoices, BaseModel, Field, TypeAdapter
from typing_extensions import ReadOnly, TypeAliasType

RequestMethod = Literal["GET", "POST", "DELETE", "PUT", "HEAD"]

# https://docs.pydantic.dev/2.11/concepts/types/#named-recursive-types
JSON = TypeAliasType(
    "JSON", "None | bool | str | int | float | Sequence[JSON] | Mapping[str, JSON]"
)


class BaseBucket(BaseModel, extra="ignore"):
    """Represents a file storage bucket."""

    id: str
    name: str
    owner: str
    public: bool
    created_at: datetime
    updated_at: datetime
    file_size_limit: int | None
    allowed_mime_types: list[str] | None
    type: str | None = None


# used in bucket.list method's option parameter
class _sortByType(TypedDict, total=False):
    column: str
    order: Literal["asc", "desc"]


class SignedUploadURL(TypedDict):
    signed_url: str
    signedUrl: str
    token: str
    path: str


class CreateOrUpdateBucketOptions(TypedDict, total=False):
    public: bool
    file_size_limit: int
    allowed_mime_types: list[str]


class ListBucketFilesOptions(TypedDict, total=False):
    limit: int
    offset: int
    sortBy: _sortByType
    search: str


class TransformOptions(TypedDict, total=False):
    height: ReadOnly[int]
    width: ReadOnly[int]
    resize: ReadOnly[Literal["cover", "contain", "fill"]]
    format: ReadOnly[Literal["origin", "avif"]]
    quality: ReadOnly[int]


def transform_to_dict(t: TransformOptions) -> dict[str, str]:
    return {key: str(val) for key, val in t.items()}


class URLOptions(TypedDict, total=False):
    download: str | bool
    transform: TransformOptions


class CreateSignedURLsOptions(TypedDict, total=False):
    download: str | bool


class SortByV2(TypedDict, total=False):
    column: Literal["name", "updated_at", "created_at"]
    order: Literal["asc", "desc"]


class SearchV2Options(TypedDict, total=False):
    limit: int
    prefix: str
    cursor: str
    with_delimiter: bool
    sortBy: SortByV2


class SearchV2Object(BaseModel):
    id: str
    name: str
    updated_at: datetime
    created_at: datetime
    metadata: dict[str, Any] | None
    key: str | None = None


class SearchV2Folder(BaseModel):
    key: str | None = None
    name: str
    created_at: datetime | None = None
    updated_at: datetime | None = None


class SearchV2Result(BaseModel):
    hasNext: bool
    folders: list[SearchV2Folder]
    objects: list[SearchV2Object]
    nextCursor: str | None = None


class DownloadOptions(TypedDict, total=False):
    transform: TransformOptions


FileOptions = TypedDict(
    "FileOptions",
    {
        "cache-control": str,
        "content-type": str,
        "x-upsert": str,
        "upsert": str,
        "metadata": dict[str, Any],
        "headers": dict[str, str],
    },
    total=False,
)


class UploadData(TypedDict, total=False):
    Id: str
    Key: str


@dataclass
class UploadResponse:
    path: str
    full_path: str
    fullPath: str

    def __init__(self, path: str, Key: str) -> None:
        self.path = path
        self.full_path = Key
        self.fullPath = Key

    dict = asdict


class SignedUrlResponse(TypedDict):
    signedURL: str | None
    signedUrl: str | None


class CreateSignedUrlResponse(TypedDict):
    error: str | None
    path: str
    signedURL: str | None
    signedUrl: str | None


class SignedUrlJsonResponse(BaseModel, extra="ignore"):
    signedURL: str


class SignedUrlsJsonItem(BaseModel, extra="ignore"):
    error: str | None
    path: str
    signedURL: str | None


SignedUrlsJsonResponse: TypeAdapter[list[SignedUrlsJsonItem]] = TypeAdapter(
    list[SignedUrlsJsonItem]
)


class CreateSignedUploadUrlOptions(BaseModel, extra="ignore"):
    upsert: str


UploadSignedUrlFileOptions = TypedDict(
    "UploadSignedUrlFileOptions",
    {
        "cache-control": str,
        "content-type": str,
        "metadata": dict[str, Any],
        "headers": dict[str, str],
    },
    total=False,
)

DistanceMetric: TypeAlias = Literal["cosine", "euclidean"]


class MetadataConfiguration(BaseModel, extra="ignore"):
    non_filterable_metadata_keys: list[str] | None = Field(
        default=None,
        validation_alias=AliasChoices(
            "non_filterable_metadata_keys", "nonFilterableMetadataKeys"
        ),
        serialization_alias="nonFilterableMetadataKeys",
    )


class ListIndexesOptions(BaseModel, extra="ignore"):
    nextToken: str | None = None
    maxResults: int | None = None
    prefix: str | None = None


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
    metadata: dict[str, Any] | None = None


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

AnalyticsBucketsParser: TypeAdapter[list[AnalyticsBucket]] = TypeAdapter(
    list[AnalyticsBucket]
)


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
