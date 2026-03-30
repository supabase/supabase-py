from __future__ import annotations

import base64
from dataclasses import dataclass
from io import BufferedReader, FileIO
from pathlib import Path
from typing import Any, Dict, Generic, List, Literal, Tuple

from pydantic import TypeAdapter
from supabase_utils.http.headers import Headers
from supabase_utils.http.io import (
    HttpIO,
    HttpMethod,
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
from supabase_utils.types import JSONParser
from yarl import URL

from .exceptions import parse_api_error, validate_adapter, validate_model
from .types import (
    CreateSignedUrlBody,
    CreateSignedUrlResponse,
    CreateSignedUrlsBody,
    FileObject,
    ListBody,
    ListFileObject,
    MessageResponse,
    SearchV2Body,
    SearchV2Result,
    SignedUploadURL,
    SignedUploadUrlResponse,
    SignedUrlJsonResponse,
    SignedUrlsJsonResponse,
    SortByType,
    SortByV2,
    TransformOptions,
    UploadResponse,
    transform_to_dict,
)

__all__ = ["StorageFileApiClient"]


def relative_path_to_parts(path: str) -> Tuple[str, ...]:
    url = URL(path)
    if url.absolute or url.parts[0] == "/":
        return url.parts[1:]
    return url.parts


def maybe_read_file(file: BufferedReader | bytes | FileIO | str | Path) -> bytes:
    if isinstance(file, (BufferedReader, FileIO)):
        # bytes or byte-stream-like object received
        return file.read()
    elif isinstance(file, bytes):
        return file
    else:
        # str or pathlib.path received
        with open(file, "rb") as f:
            return f.read()


FileObjectsAdapter = TypeAdapter(list[FileObject])
ListFileObjectsAdapter = TypeAdapter(list[ListFileObject])


@dataclass
class StorageFileApiClient(Generic[HttpIO]):
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
        upsert: str | None = None,
    ) -> HttpMethod[SignedUploadURL]:
        """
        Creates a signed upload URL.

        Parameters
        ----------
        path
            The file path, including the file name. For example `folder/image.png`.
        options
            Additional options for the upload url creation.
        """
        headers = Headers.empty()
        if upsert:
            headers = headers.set("x-upsert", upsert)

        path_parts: Tuple[str, ...] = relative_path_to_parts(path)
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
        metadata: Dict[str, Any] | None = None,
        headers: Dict[str, str] | None = None,
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
        path_parts: Tuple[str, ...] = relative_path_to_parts(path)
        query_params = URLQuery.from_mapping({"token": token})

        http_headers = Headers.from_mapping(headers) if headers else Headers.empty()
        http_headers = http_headers.set("x-upsert", "false").set(
            "cache-control", f"max-age={cache_control}"
        )

        cache_control_field = DataField(
            name="cacheControl",
            data=cache_control.encode("utf-8"),
        )
        fields: list[PartField] = [cache_control_field]
        if metadata is not None:
            metadata_bytes = JSONParser.dump_json(metadata)
            metadata_b64_encoded = base64.b64encode(metadata_bytes)
            http_headers = http_headers.set(
                "x-metadata", metadata_b64_encoded.decode("utf-8")
            )
            fields.append(
                DataField(
                    name="metadata",
                    data=metadata_bytes,
                )
            )
        file_field = FileField(
            name="file",
            filename=path_parts[-1],
            data=maybe_read_file(file),
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

        return validate_model(response, UploadResponse)

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

        path_parts: Tuple[str, ...] = relative_path_to_parts(path)
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
    ) -> List[CreateSignedUrlResponse]:
        if not response.is_success:
            raise parse_api_error(response)
        data = SignedUrlsJsonResponse.validate_json(response.content)
        signed_urls = []
        for item in data:
            # Prepare URL
            url = self._make_signed_url(item.signedURL, download_query)
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
        paths: List[str],
        expires_in: int,
        download: bool | str | None = None,
    ) -> HttpMethod[List[CreateSignedUrlResponse]]:
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
            paths=paths,
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
        transformation = transform_to_dict(transform) if transform else dict()

        path_parts = relative_path_to_parts(path)
        url = (
            self.base_url.joinpath(*render_path, "public", self.id, *path_parts)
            .with_query(download_query.as_query())
            .extend_query(transformation)
        )
        return str(url)

    @handle_http_io
    def move(self, from_path: str, to_path: str) -> HttpMethod[MessageResponse]:
        """
        Moves an existing file, optionally renaming it at the same time.

        Parameters
        ----------
        from_path
            The original file path, including the current file name. For example `folder/image.png`.
        to_path
            The new file path, including the new file name. For example `folder/image-copy.png`.
        """
        response = yield JSONRequest(
            method="POST",
            path=["object", "move"],
            body={
                "bucketId": self.id,
                "sourceKey": from_path,
                "destinationKey": to_path,
            },
        )
        return validate_model(response, MessageResponse)

    @handle_http_io
    def copy(self, from_path: str, to_path: str) -> HttpMethod[UploadResponse]:
        """
        Copies an existing file to a new path in the same bucket.

        Parameters
        ----------
        from_path
            The original file path, including the current file name. For example `folder/image.png`.
        to_path
            The new file path, including the new file name. For example `folder/image-copy.png`.
        """
        response = yield JSONRequest(
            method="POST",
            path=["object", "copy"],
            body={
                "bucketId": self.id,
                "sourceKey": from_path,
                "destinationKey": to_path,
            },
        )

        return validate_model(response, UploadResponse)

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
            body={"prefixes": paths},
        )
        return validate_adapter(response, FileObjectsAdapter)

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
        path_parts: Tuple[str, ...] = relative_path_to_parts(path)  # split paths by /
        response = yield EmptyRequest(
            method="GET",
            path=["object", "info", self.id, *path_parts],
        )
        return validate_model(response, FileObject)

    @handle_http_io
    def exists(
        self,
        path: str,
    ) -> HttpMethod[bool]:
        """
        Returns True if the file exists, False otherwise.

        Parameters
        ----------
        path
            The path to the file.
        """
        path_parts: Tuple[str, ...] = relative_path_to_parts(path)  # split paths by /
        response = yield EmptyRequest(
            method="HEAD",
            path=["object", self.id, *path_parts],
        )
        if response.is_success:
            return True
        elif 400 <= response.status <= 401:
            return False
        else:
            raise parse_api_error(response)

    @handle_http_io
    def list(
        self,
        path: str | None = None,
        limit: int = 100,
        offset: int = 0,
        search: str | None = None,
        sortBy: SortByType | None = None,
    ) -> HttpMethod[List[ListFileObject]]:
        """
        Lists all the files within a bucket.

        Parameters
        ----------
        path
            The folder path.
        options
            Search options, including `limit`, `offset`, `sortBy` and `search`.
        """
        body = ListBody(
            prefix=path or "",
            limit=limit,
            offset=offset,
            sortBy=sortBy or SortByType(),
            search=search,
        )
        response = yield JSONRequest(
            method="POST",
            path=["object", "list", self.id],
            body=body,
        )
        return validate_adapter(response, ListFileObjectsAdapter)

    @handle_http_io
    def list_v2(
        self,
        limit: int | None = None,
        prefix: str | None = None,
        cursor: str | None = None,
        with_delimiter: bool | None = None,
        sort_by: SortByV2 | None = None,
    ) -> HttpMethod[SearchV2Result]:
        body = SearchV2Body(
            limit=limit,
            prefix=prefix,
            cursor=cursor,
            with_delimiter=with_delimiter,
            sortBy=sort_by,
        )
        response = yield JSONRequest(
            method="POST",
            path=["object", "list-v2", self.id],
            body=body,
            exclude_none=True,
        )
        return validate_model(response, SearchV2Result)

    @handle_http_io
    def download(
        self,
        path: str,
        transform: TransformOptions | None = None,
        query_params: Dict[str, str] | None = None,
    ) -> HttpMethod[bytes]:
        """
        Downloads a file.

        Parameters
        ----------
        path
            The file path to be downloaded, including the path and file name. For example `folder/image.png`.
        """
        render_path: List[str] = ["object"]
        params = (
            URLQuery.from_mapping(query_params) if query_params else URLQuery.empty()
        )
        if transform:
            params = params.merge(URLQuery.from_mapping(transform_to_dict(transform)))
            render_path = ["render", "image", "authenticated"]
        path_parts: Tuple[str, ...] = relative_path_to_parts(path)
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
        upsert: str,
        metadata: Dict[str, Any] | None,
        headers: Dict[str, str] | None,
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
        file_options
            HTTP headers.
        """

        http_headers = Headers.from_mapping(headers) if headers else Headers.empty()

        http_headers = http_headers.set("cache-control", f"max-age={cache_control}")

        # Only include x-upsert on a POST method
        if method == "POST":
            http_headers = http_headers.set("x-upsert", upsert)

        cache_control_field = DataField(
            name="cacheControl",
            data=cache_control.encode("utf-8"),
        )
        fields: list[PartField] = [cache_control_field]
        if metadata is not None:
            metadata_bytes = JSONParser.dump_json(metadata)
            metadata_b64_encoded = base64.b64encode(metadata_bytes)
            http_headers = http_headers.set(
                "x-metadata", metadata_b64_encoded.decode("utf-8")
            )
            fields.append(
                DataField(
                    name="metadata",
                    data=metadata_bytes,
                )
            )
        file_field = FileField(
            name="file",
            filename=path[-1],
            data=maybe_read_file(file),
            content_type=content_type,
        )
        fields.append(file_field)
        response = yield MultipartFormDataRequest(
            method=method,
            path=["object", self.id, *path],
            fields=fields,
            headers=http_headers,
        )

        return validate_model(response, UploadResponse)

    @handle_http_io
    def upload(
        self,
        path: str,
        file: BufferedReader | bytes | FileIO | str | Path,
        cache_control: str = "3600",
        content_type: str = "text/plain;charset=UTF-8",
        upsert: str = "false",
        metadata: Dict[str, Any] | None = None,
        headers: Dict[str, str] | None = None,
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
        file_options
            HTTP headers.
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
        upsert: str = "false",
        metadata: Dict[str, Any] | None = None,
        headers: Dict[str, str] | None = None,
    ) -> HttpMethod[UploadResponse]:
        path_parts = relative_path_to_parts(path)
        return self._upload_or_update(
            method="PUT",
            path=path_parts,
            file=file,
            cache_control=cache_control,
            content_type=content_type,
            upsert=upsert,
            metadata=metadata,
            headers=headers,
        )
