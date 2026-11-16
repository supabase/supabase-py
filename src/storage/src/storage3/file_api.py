from __future__ import annotations

import base64
from dataclasses import dataclass
from io import BufferedReader, FileIO
from typing import TYPE_CHECKING, Any, Literal

from pydantic import BaseModel, TypeAdapter
from supabase_utils.http.headers import Headers
from supabase_utils.http.io import (
    AsyncHttpIO,
    HttpMethod,
    SyncHttpIO,
    handle_http_io,
)
from supabase_utils.http.query import URLQuery
from supabase_utils.http.request import (
    DataField,
    EmptyRequest,
    FileField,
    JSONRequest,
    MultipartFormDataRequest,
    PartField,
    Response,
)
from supabase_utils.types import JSON, JSONParser
from yarl import URL

from .exceptions import _validate_adapter, _validate_model, parse_api_error
from .types import (
    CreateSignedUrlBody,
    CreateSignedUrlResponse,
    CreateSignedUrlsBody,
    FileObject,
    ListBody,
    ListResult,
    MessageResponse,
    SignedUploadURL,
    SignedUploadUrlResponse,
    SignedUrlJsonResponse,
    SignedUrlsJsonResponse,
    SortBy,
    TransformOptions,
    UploadResponse,
    transform_to_dict,
)

if TYPE_CHECKING:
    import builtins
    from pathlib import Path

__all__ = ["StorageFileApiClient"]


def relative_path_to_parts(path: str) -> tuple[str, ...]:
    parts = tuple(path.lstrip("/").split("/"))
    if parts == ("",):
        raise ValueError(f"Object keys must not be empty: {path!r}")
    if {".", ".."} & set(parts):
        raise ValueError(f"Object keys must not contain dot segments: {path!r}")
    if "" in parts[:-1]:
        raise ValueError(f"Object keys must not contain empty segments: {path!r}")
    return parts


def _normalize_object_key(path: str) -> str:
    return "/".join(relative_path_to_parts(path))


def _bool_header(value: bool) -> str:
    if not isinstance(value, bool):
        raise TypeError(f"upsert must be a bool, not {type(value).__name__}")
    return "true" if value else "false"


def _maybe_read_file(file: BufferedReader | bytes | FileIO | str | Path) -> bytes:
    if isinstance(file, (BufferedReader, FileIO)):
        # bytes or byte-stream-like object received
        return file.read()
    if isinstance(file, bytes):
        return file
    # str or pathlib.path received
    with open(file, "rb") as f:
        return f.read()


FileObjectsAdapter = TypeAdapter(list[FileObject])


class _UploadJsonResponse(BaseModel, extra="ignore"):
    Key: str
    Id: str | None = None
    version: str | None = None


def _parse_upload_response(response: Response, path: str) -> UploadResponse:
    data = _validate_model(response, _UploadJsonResponse)
    return UploadResponse(
        id=data.Id, path=path, full_path=data.Key, version=data.version
    )


@dataclass
class StorageFileApiClient[HttpIO: (SyncHttpIO, AsyncHttpIO)]:
    """Functions needed to access the file API."""

    id: str
    base_url: URL
    executor: HttpIO
    default_headers: Headers

    def _parse_signed_url_response(self, response: Response) -> SignedUploadURL:
        if not response.is_success:
            raise parse_api_error(response)
        signed_url_upload = SignedUploadUrlResponse.model_validate_json(
            response.content
        )
        path_parts = URL(signed_url_upload.url.lstrip("/"))
        url = self.base_url.join(path_parts)

        return SignedUploadURL(
            signed_url=str(url),
            token=signed_url_upload.token,
        )

    @handle_http_io
    def create_signed_upload_url(
        self,
        path: str,
        upsert: bool | None = None,
    ) -> HttpMethod[SignedUploadURL]:
        """
        Creates a signed upload URL.

        Parameters
        ----------
        path
            The file path, including the file name. For example `folder/image.png`.
        upsert
            Whether a later upload with the returned token may overwrite an
            existing file. The server default applies when omitted.
        """
        headers = Headers.empty()
        if upsert is not None:
            headers = headers.set("x-upsert", _bool_header(upsert))

        path_parts: tuple[str, ...] = relative_path_to_parts(path)
        response = yield EmptyRequest(
            method="POST",
            path=["object", "upload", "sign", self.id, *path_parts],
            headers=headers,
        )

        return self._parse_signed_url_response(response)

    @handle_http_io
    def upload_to_signed_url(
        self,
        path: str,
        token: str,
        file: BufferedReader | bytes | FileIO | str | Path,
        content_type: str = "text/plain;charset=UTF-8",
        cache_control: str = "3600",
        metadata: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> HttpMethod[UploadResponse]:
        """
        Upload a file with a token generated from :meth:`.create_signed_url`

        Parameters
        ----------
        path
            The file path, including the file name
        token
            The token generated from :meth:`.create_signed_url`
        file
            The file contents or a file-like object to upload
        """
        path_parts: tuple[str, ...] = relative_path_to_parts(path)
        query_params = URLQuery.from_mapping({"token": token})

        http_headers = Headers.empty().set("x-upsert", "false")
        if headers:
            http_headers = http_headers.update(Headers.from_mapping(headers))

        cache_control_field = DataField(
            name="cacheControl",
            data=cache_control.encode("utf-8"),
        )
        fields: list[PartField] = [cache_control_field]
        if metadata is not None:
            fields.append(
                DataField(
                    name="metadata",
                    data=JSONParser.dump_json(metadata),
                )
            )
        file_field = FileField(
            name="file",
            filename=path_parts[-1],
            data=_maybe_read_file(file),
            content_type=content_type,
        )
        fields.append(file_field)
        response = yield MultipartFormDataRequest(
            method="PUT",
            path=["object", "upload", "sign", self.id, *path_parts],
            fields=fields,
            headers=http_headers,
            query=query_params,
        )

        return _parse_upload_response(response, "/".join(path_parts))

    def _make_signed_url(self, signed_url: str, download_query: URLQuery) -> str:
        url = URL(signed_url[1:])  # ignore starting slash
        signed = self.base_url.join(url).extend_query(download_query.as_query())
        return str(signed)

    def _parse_signed_url(self, response: Response, download_query: URLQuery) -> str:
        if not response.is_success:
            raise parse_api_error(response)
        signed_url_obj = SignedUrlJsonResponse.model_validate_json(response.content)
        return self._make_signed_url(signed_url_obj.signedURL, download_query)

    @handle_http_io
    def create_signed_url(
        self,
        path: str,
        expires_in: int,
        download: str | bool | None = None,
        transform: TransformOptions | None = None,
    ) -> HttpMethod[str]:
        """
        Parameters
        ----------
        path
            file path to be downloaded, including the current file name.
        expires_in
            number of seconds until the signed URL expires.
        options
            options to be passed for downloading or transforming the file.
        """
        download_query = URLQuery.empty()
        if download:
            download_query = download_query.set(
                "download", "" if download is True else download
            )

        path_parts: tuple[str, ...] = relative_path_to_parts(path)
        body = CreateSignedUrlBody(
            expiresIn=expires_in,
            download=download,
            transform=transform,
        )
        response = yield JSONRequest(
            method="POST",
            path=["object", "sign", self.id, *path_parts],
            body=body,
            exclude_none=True,
        )

        return self._parse_signed_url(response, download_query)

    def _parse_signed_urls(
        self, response: Response, download_query: URLQuery
    ) -> builtins.list[CreateSignedUrlResponse]:
        if not response.is_success:
            raise parse_api_error(response)
        data = SignedUrlsJsonResponse.validate_json(response.content)
        signed_urls = []
        for item in data:
            # Prepare URL
            url = (
                self._make_signed_url(item.signedURL, download_query)
                if item.signedURL
                else None
            )
            signed_item = CreateSignedUrlResponse(
                error=item.error,
                path=item.path,
                signed_url=url,
            )
            signed_urls.append(signed_item)
        return signed_urls

    @handle_http_io
    def create_signed_urls(
        self,
        paths: builtins.list[str],
        expires_in: int,
        download: bool | str | None = None,
    ) -> HttpMethod[builtins.list[CreateSignedUrlResponse]]:
        """
        Parameters
        ----------
        path
            file path to be downloaded, including the current file name.
        expires_in
            number of seconds until the signed URL expires.
        options
            options to be passed for downloading the file.
        """
        download_query = URLQuery.empty()
        if download:
            download_query = download_query.set(
                "download", "" if download is True else download
            )

        body = CreateSignedUrlsBody(
            download=download,
            expiresIn=expires_in,
            paths=[_normalize_object_key(path) for path in paths],
        )
        response = yield JSONRequest(
            method="POST",
            path=["object", "sign", self.id],
            body=body,
        )
        return self._parse_signed_urls(response, download_query)

    def get_public_url(
        self,
        path: str,
        download: bool | str | None = None,
        transform: TransformOptions | None = None,
    ) -> str:
        """
        Parameters
        ----------
        path
            file path, including the path and file name. For example `folder/image.png`.
        """
        download_query = URLQuery.empty()
        if download:
            download_query = download_query.set(
                "download", "" if download is True else download
            )

        render_path = ["render", "image"] if transform else ["object"]
        transformation = transform_to_dict(transform) if transform else {}

        path_parts = relative_path_to_parts(path)
        url = (
            self.base_url.joinpath(*render_path, "public", self.id, *path_parts)
            .with_query(download_query.as_query())
            .extend_query(transformation)
        )
        return str(url)

    @handle_http_io
    def move(
        self,
        from_path: str,
        to_path: str,
        *,
        destination_bucket: str | None = None,
    ) -> HttpMethod[MessageResponse]:
        """
        Moves an existing file, optionally renaming it at the same time.

        Parameters
        ----------
        from_path
            The original file path, including the current file name. For example `folder/image.png`.
        to_path
            The new file path, including the new file name. For example `folder/image-copy.png`.
        destination_bucket
            The bucket to move the file to. Defaults to this bucket.
        """
        response = yield JSONRequest(
            method="POST",
            path=["object", "move"],
            body=self._destination_body(from_path, to_path, destination_bucket),
        )
        return _validate_model(response, MessageResponse)

    @handle_http_io
    def copy(
        self,
        from_path: str,
        to_path: str,
        *,
        destination_bucket: str | None = None,
        upsert: bool = False,
        copy_metadata: bool = True,
        metadata: dict[str, Any] | None = None,
        cache_control: str | None = None,
        content_type: str | None = None,
        content_encoding: str | None = None,
    ) -> HttpMethod[UploadResponse]:
        """
        Copies an existing file to a new path.

        Parameters
        ----------
        from_path
            The original file path, including the current file name. For example `folder/image.png`.
        to_path
            The new file path, including the new file name. For example `folder/image-copy.png`.
        destination_bucket
            The bucket to copy the file to. Defaults to this bucket.
        upsert
            Whether to overwrite the file at `to_path` if it already exists.
        copy_metadata
            Whether the copy keeps the metadata of the original file. Set it to
            `False` to replace the custom metadata with `metadata` and to
            override the file metadata given below.
        metadata
            The custom metadata of the copy. Requires `copy_metadata=False`.
        cache_control
            The full `Cache-Control` value of the copy, for example
            `max-age=3600`. Requires `copy_metadata=False`.
        content_type
            The `Content-Type` of the copy. Requires `copy_metadata=False`.
        content_encoding
            The `Content-Encoding` of the copy. An empty string clears it. It
            changes the metadata only, not the bytes of the file. Requires
            `copy_metadata=False` and Supabase Storage v1.80.0 or newer.
        """
        file_metadata = {
            key: value
            for key, value in (
                ("cacheControl", cache_control),
                ("mimetype", content_type),
                ("contentEncoding", content_encoding),
            )
            if value is not None
        }
        if copy_metadata and (metadata is not None or file_metadata):
            raise ValueError(
                "metadata, cache_control, content_type and content_encoding "
                "require copy_metadata=False"
            )

        headers = Headers.empty().set("x-upsert", _bool_header(upsert))
        to_key = _normalize_object_key(to_path)
        body = self._destination_body(from_path, to_key, destination_bucket)
        if not copy_metadata:
            body["copyMetadata"] = False
            if file_metadata:
                body["metadata"] = file_metadata
            if metadata is not None:
                headers = headers.set(
                    "x-metadata",
                    base64.b64encode(JSONParser.dump_json(metadata)).decode("ascii"),
                )

        response = yield JSONRequest(
            method="POST",
            path=["object", "copy"],
            body=body,
            headers=headers,
        )
        return _parse_upload_response(response, to_key)

    def _destination_body(
        self, from_path: str, to_path: str, destination_bucket: str | None
    ) -> dict[str, JSON]:
        body: dict[str, JSON] = {
            "bucketId": self.id,
            "sourceKey": _normalize_object_key(from_path),
            "destinationKey": _normalize_object_key(to_path),
        }
        if destination_bucket is not None:
            body["destinationBucket"] = destination_bucket
        return body

    @handle_http_io
    def remove(self, paths: list[str]) -> HttpMethod[list[FileObject]]:
        """
        Deletes files within the same bucket

        Parameters
        ----------
        paths
            An array or list of files to be deletes, including the path and file name. For example [`folder/image.png`].
        """
        response = yield JSONRequest(
            method="DELETE",
            path=["object", self.id],
            body={"prefixes": [_normalize_object_key(path) for path in paths]},
        )
        return _validate_adapter(response, FileObjectsAdapter)

    @handle_http_io
    def info(
        self,
        path: str,
    ) -> HttpMethod[FileObject]:
        """
        Lists info for a particular file.

        Parameters
        ----------
        path
            The path to the file.
        """
        path_parts: tuple[str, ...] = relative_path_to_parts(path)  # split paths by /
        response = yield EmptyRequest(
            method="GET",
            path=["object", "info", self.id, *path_parts],
        )
        return _validate_model(response, FileObject)

    @handle_http_io
    def exists(
        self,
        path: str,
    ) -> HttpMethod[bool]:
        """
        Returns True if the file exists, False if it does not.

        Raises :class:`StorageApiError` for any other error, such as an
        invalid token or a missing bucket.

        Parameters
        ----------
        path
            The path to the file.
        """
        response = yield EmptyRequest(
            method="GET",
            path=["object", "info", self.id, *relative_path_to_parts(path)],
        )
        if response.is_success:
            return True
        error = parse_api_error(response)
        if error.code == "NoSuchKey":
            return False
        raise error

    @handle_http_io
    def list(
        self,
        prefix: str | None = None,
        *,
        limit: int | None = None,
        cursor: str | None = None,
        with_delimiter: bool | None = None,
        sort_by: SortBy | None = None,
    ) -> HttpMethod[ListResult]:
        """
        Lists one page of the objects in the bucket.

        Needs Supabase Storage v1.19.0 or newer.

        Parameters
        ----------
        prefix
            The start of the object keys to list. It is sent as given: `photos`
            also selects `photos-old/a.png`, while `photos/` selects the keys
            under that folder.
        limit
            The page size. The server default and maximum are 1000.
        cursor
            The `nextCursor` of the previous page. Pass it with the same
            arguments as the first page.
        with_delimiter
            When `True`, lists one level: the keys below the next `/` after
            `prefix` are collapsed into `folders`, named by their full prefix
            ending in `/`. Otherwise every key at every depth is listed and
            `folders` is empty.
        sort_by
            The column and order to sort by. Defaults to `name` ascending.
        """
        body = ListBody(
            prefix=prefix,
            limit=limit,
            cursor=cursor,
            with_delimiter=with_delimiter,
            sortBy=sort_by,
        )
        response = yield JSONRequest(
            method="POST",
            path=["object", "list-v2", self.id],
            body=body,
        )
        return _validate_model(response, ListResult)

    @handle_http_io
    def download(
        self,
        path: str,
        transform: TransformOptions | None = None,
        query_params: dict[str, str] | None = None,
    ) -> HttpMethod[bytes]:
        """
        Downloads a file.

        Parameters
        ----------
        path
            The file path to be downloaded, including the path and file name. For example `folder/image.png`.
        """
        render_path: list[str] = ["object"]
        params = (
            URLQuery.from_mapping(query_params) if query_params else URLQuery.empty()
        )
        if transform:
            params = params.merge(URLQuery.from_mapping(transform_to_dict(transform)))
            render_path = ["render", "image", "authenticated"]
        path_parts: tuple[str, ...] = relative_path_to_parts(path)
        response = yield EmptyRequest(
            method="GET",
            path=[*render_path, self.id, *path_parts],
            query=params,
        )
        if not response.is_success:
            raise parse_api_error(response)
        return response.content

    def _upload_or_update(
        self,
        method: Literal["POST", "PUT"],
        path: tuple[str, ...],
        file: BufferedReader | bytes | FileIO | str | Path,
        cache_control: str,
        content_type: str,
        upsert: bool | None,
        metadata: dict[str, Any] | None,
        headers: dict[str, str] | None,
    ) -> HttpMethod[UploadResponse]:
        """
        Uploads a file to an existing bucket.

        Parameters
        ----------
        path
            The relative file path including the bucket ID. Should be of the format `bucket/folder/subfolder/filename.png`.
            The bucket must already exist before attempting to upload.
        file
            The File object to be stored in the bucket. or a async generator of chunks
        upsert
            Sent as the `x-upsert` header, or left out when `None`.
        """

        http_headers = Headers.empty()
        if upsert is not None:
            http_headers = http_headers.set("x-upsert", _bool_header(upsert))

        if headers:
            http_headers = http_headers.update(Headers.from_mapping(headers))

        cache_control_field = DataField(
            name="cacheControl",
            data=cache_control.encode("utf-8"),
        )
        fields: list[PartField] = [cache_control_field]
        if metadata is not None:
            fields.append(
                DataField(
                    name="metadata",
                    data=JSONParser.dump_json(metadata),
                )
            )
        file_field = FileField(
            name="file",
            filename=path[-1],
            data=_maybe_read_file(file),
            content_type=content_type,
        )
        fields.append(file_field)
        response = yield MultipartFormDataRequest(
            method=method,
            path=["object", self.id, *path],
            fields=fields,
            headers=http_headers,
        )

        return _parse_upload_response(response, "/".join(path))

    @handle_http_io
    def upload(
        self,
        path: str,
        file: BufferedReader | bytes | FileIO | str | Path,
        cache_control: str = "3600",
        content_type: str = "text/plain;charset=UTF-8",
        upsert: bool = False,
        metadata: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> HttpMethod[UploadResponse]:
        """
        Uploads a file to an existing bucket.

        Parameters
        ----------
        path
            The relative file path including the bucket ID. Should be of the format `bucket/folder/subfolder/filename.png`.
            The bucket must already exist before attempting to upload.
        file
            The File object to be stored in the bucket. or a async generator of chunks
        upsert
            Whether to overwrite the file if it already exists.
        """
        path_parts = relative_path_to_parts(path)
        return self._upload_or_update(
            method="POST",
            path=path_parts,
            file=file,
            cache_control=cache_control,
            content_type=content_type,
            upsert=upsert,
            metadata=metadata,
            headers=headers,
        )

    @handle_http_io
    def update(
        self,
        path: str,
        file: BufferedReader | bytes | FileIO | str | Path,
        cache_control: str = "3600",
        content_type: str = "text/plain;charset=UTF-8",
        metadata: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> HttpMethod[UploadResponse]:
        path_parts = relative_path_to_parts(path)
        return self._upload_or_update(
            method="PUT",
            path=path_parts,
            file=file,
            cache_control=cache_control,
            content_type=content_type,
            upsert=None,
            metadata=metadata,
            headers=headers,
        )
