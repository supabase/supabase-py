from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional, TypedDict, Union

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter
from typing_extensions import ReadOnly, TypeAlias, TypeAliasType

RequestMethod = Literal["GET", "POST", "DELETE", "PUT", "HEAD"]

config = ConfigDict(extra="ignore")

# https://docs.pydantic.dev/2.11/concepts/types/#named-recursive-types
JSON = TypeAliasType(
    "JSON", "Union[None, bool, str, int, float, Sequence[JSON], Mapping[str, JSON]]"
)
JSONAdapter: TypeAdapter = TypeAdapter(JSON)


class BaseBucket(BaseModel):
    """Represents a file storage bucket."""

    model_config = config

    id: str
    name: str
    owner: str
    public: bool
    created_at: datetime
    updated_at: datetime
    file_size_limit: Optional[int]
    allowed_mime_types: Optional[list[str]]
    type: Optional[str] = None


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
    download: Union[str, bool]
    transform: TransformOptions


class CreateSignedURLsOptions(TypedDict, total=False):
    download: Union[str, bool]


class DownloadOptions(TypedDict, total=False):
    transform: TransformOptions


FileOptions = TypedDict(
    "FileOptions",
    {
        "cache-control": str,
        "content-type": str,
        "x-upsert": str,
        "upsert": str,
        "metadata": Dict[str, Any],
        "headers": Dict[str, str],
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
    signedURL: str
    signedUrl: str


class CreateSignedUrlResponse(TypedDict):
    error: Optional[str]
    path: str
    signedURL: str
    signedUrl: str


class SignedUrlJsonResponse(BaseModel):
    signedURL: str


class SignedUrlsJsonItem(BaseModel):
    error: Optional[str]
    path: str
    signedURL: str


SignedUrlsJsonResponse = TypeAdapter(list[SignedUrlsJsonItem])


class CreateSignedUploadUrlOptions(BaseModel):
    upsert: str


UploadSignedUrlFileOptions = TypedDict(
    "UploadSignedUrlFileOptions",
    {
        "cache-control": str,
        "content-type": str,
        "metadata": Dict[str, Any],
        "headers": Dict[str, str],
    },
    total=False,
)

DistanceMetric: TypeAlias = Literal["cosine", "euclidean"]


class MetadataConfiguration(BaseModel):
    non_filterable_metadata_keys: Optional[List[str]] = Field(
        alias="nonFilterableMetadataKeys"
    )


class ListIndexesOptions(BaseModel):
    nextToken: Optional[str] = None
    maxResults: Optional[int] = None
    prefix: Optional[str] = None


class ListIndexesResponseItem(BaseModel):
    indexName: str


class ListVectorIndexesResponse(BaseModel):
    indexes: List[ListIndexesResponseItem]
    nextToken: Optional[str] = None


class VectorIndex(BaseModel):
    index_name: str = Field(alias="indexName")
    bucket_name: str = Field(alias="vectorBucketName")
    data_type: str = Field(alias="dataType")
    dimension: int
    distance_metric: DistanceMetric = Field(alias="distanceMetric")
    metadata: Optional[MetadataConfiguration] = Field(
        alias="metadataConfiguration", default=None
    )
    creation_time: Optional[datetime] = None


class GetVectorIndexResponse(BaseModel):
    index: VectorIndex


VectorFilter = Dict[str, Any]


class VectorData(BaseModel):
    float32: List[float]


class VectorObject(BaseModel):
    key: str
    data: VectorData
    metadata: Optional[dict[str, Union[str, bool, float]]] = None

    def as_json(self) -> JSON:
        return {"key": self.key, "data": dict(self.data), "metadata": self.metadata}


class VectorMatch(BaseModel):
    key: str
    data: Optional[VectorData] = None
    distance: Optional[int] = None
    metadata: Optional[dict[str, Any]] = None


class GetVectorsResponse(BaseModel):
    vectors: List[VectorMatch]


class ListVectorsResponse(BaseModel):
    vectors: List[VectorMatch]
    nextToken: Optional[str] = None


class QueryVectorsResponse(BaseModel):
    matches: List[VectorMatch]


class AnalyticsBucket(BaseModel):
    name: str
    type: Optional[Literal["ANALYTICS"]] = None
    format: Optional[str] = None
    created_at: datetime
    updated_at: datetime


SortColumn = Literal["id", "name", "created_at", "updated_at"]
SortOrder = Literal["asc", "desc"]

AnalyticsBucketsParser = TypeAdapter(List[AnalyticsBucket])


class AnalyticsBucketDeleteResponse(BaseModel):
    message: str


class VectorBucketEncryptionConfiguration(BaseModel):
    kmsKeyArn: Optional[str] = None
    sseType: Optional[str] = None


class VectorBucket(BaseModel):
    vectorBucketName: str
    creationTime: Optional[datetime] = None
    encryptionConfiguration: Optional[VectorBucketEncryptionConfiguration] = None


class GetVectorBucketResponse(BaseModel):
    vectorBucket: VectorBucket


class ListVectorBucketsItem(BaseModel):
    vectorBucketName: str


class ListVectorBucketsResponse(BaseModel):
    vectorBuckets: List[ListVectorBucketsItem]
    nextToken: Optional[str] = None
