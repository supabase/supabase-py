from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, Literal, Optional, TypedDict, Union

from pydantic import BaseModel, ConfigDict, TypeAdapter
from typing_extensions import ReadOnly

RequestMethod = Literal["GET", "POST", "DELETE", "PUT", "HEAD"]

config = ConfigDict(extra="ignore")


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
