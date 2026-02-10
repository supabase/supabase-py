from __future__ import annotations

import base64
from dataclasses import dataclass
from io import BufferedReader, FileIO
from pathlib import Path
from typing import Any, Generic, Literal

from httpx import Headers, QueryParams, Response
from pydantic import TypeAdapter
from supabase_utils.http import (
    EmptyRequest,
    Executor,
    FromHttpxResponse,
    JSONRequest,
    MultipartFormDataRequest,
    ResponseCases,
    ResponseHandler,
    handle_http_response,
    validate_adapter,
    validate_model,
)
from supabase_utils.types import JSONParser
from yarl import URL

from .exceptions import parse_api_error
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


def relative_path_to_parts(path: str) -> tuple[str, ...]:
    url = URL(path)
    if url.absolute or url.parts[0] == "/":
        return url.parts[1:]
    return url.parts


@dataclass
class StorageFileApiClient(Generic[Executor]):
    """Functions needed to access the file API."""

    id: str
    base_url: URL
    executor: Executor
    _headers: Headers

    def _parse_signed_url_response(self, response: Response) -> SignedUploadURL:
        signed_url_upload = SignedUploadUrlResponse.model_validate_json(
            response.content
        )
        path_parts = URL(signed_url_upload.url.lstrip("/"))
        url = self.base_url.join(path_parts)

        return SignedUploadURL(
            signed_url=str(url),
            token=signed_url_upload.token,
        )

    @handle_http_response
    def create_signed_upload_url(
        self,
        path: str,
        upsert: str | None = None,
    ) -> ResponseHandler[SignedUploadURL]:
        """
        Creates a signed upload URL.

        Parameters
        ----------
        path
            The file path, including the file name. For example `folder/image.png`.
        options
            Additional options for the upload url creation.
        """
        headers = Headers(self._headers)
        if upsert:
            headers["x-upsert"] = upsert

        path_parts: tuple[str, ...] = relative_path_to_parts(path)
        request = EmptyRequest(
            method="POST",
            path=["object", "upload", "sign", self.id, *path_parts],
            headers=headers,
        )

        return ResponseCases(
            request=request,
            on_success=self._parse_signed_url_response,
            on_failure=parse_api_error,
        )

    @handle_http_response
    def upload_to_signed_url(
        self,
        path: str,
        token: str,
        file: BufferedReader | bytes | FileIO | str | Path,
        content_type: str = "text/plain;charset=UTF-8",
        cache_control: str = "3600",
        metadata: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> ResponseHandler[UploadResponse]:
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
        query_params = QueryParams({"token": token})

        final_url = ["object", "upload", "sign", self.id, *path_parts]

        extra_headers = Headers(headers)
        extra_headers["x-upsert"] = "false"
        extra_headers["cache-control"] = f"max-age={cache_control}"
        extra_headers.update(self._headers)

        data = {"cacheControl": cache_control}
        filename = path_parts[-1]

        if isinstance(file, (BufferedReader, bytes, FileIO)):
            # bytes or byte-stream-like object received
            file_contents = file
        else:
            # str or pathlib.path received
            with open(file, "rb") as f:
                file_contents = f.read()
        files = {"file": (filename, file_contents, content_type)}
        request = MultipartFormDataRequest(
            method="PUT",
            path=final_url,
            files=files,
            headers=extra_headers,
            data=data,
            query_params=query_params,
        )

        return ResponseCases(
            request=request,
            on_success=validate_model(UploadResponse),
            on_failure=parse_api_error,
        )

    def _make_signed_url(self, signed_url: str, download_query: QueryParams) -> str:
        url = URL(signed_url[1:])  # ignore starting slash
        signed = self.base_url.join(url).extend_query(download_query)
        return str(signed)

    def _parse_signed_url(self, download_query: QueryParams) -> FromHttpxResponse[str]:
        def from_response(response: Response) -> str:
            signed_url_obj = SignedUrlJsonResponse.model_validate_json(response.content)
            return self._make_signed_url(signed_url_obj.signedURL, download_query)

        return from_response

    @handle_http_response
    def create_signed_url(
        self,
        path: str,
        expires_in: int,
        download: str | bool | None = None,
        transform: TransformOptions | None = None,
    ) -> ResponseHandler[str]:
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
        download_query = QueryParams()
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
        request = JSONRequest(
            method="POST",
            path=["object", "sign", self.id, *path_parts],
            headers=self._headers,
            body=body,
            exclude_none=True,
        )

        return ResponseCases(
            request=request,
            on_success=self._parse_signed_url(download_query),
            on_failure=parse_api_error,
        )

    def _parse_signed_urls(
        self, download_query: QueryParams
    ) -> FromHttpxResponse[list[CreateSignedUrlResponse]]:
        def from_response(response: Response) -> list[CreateSignedUrlResponse]:
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

        return from_response

    @handle_http_response
    def create_signed_urls(
        self,
        paths: list[str],
        expires_in: int,
        download: bool | str | None = None,
    ) -> ResponseHandler[list[CreateSignedUrlResponse]]:
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
        download_query = QueryParams()
        if download:
            download_query = download_query.set(
                "download", "" if download is True else download
            )

        body = CreateSignedUrlsBody(
            download=download,
            expiresIn=expires_in,
            paths=paths,
        )

        request = JSONRequest(
            method="POST",
            path=["object", "sign", self.id],
            body=body,
            headers=self._headers,
        )
        return ResponseCases(
            request=request,
            on_success=self._parse_signed_urls(download_query),
            on_failure=parse_api_error,
        )

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
        download_query = QueryParams()
        if download:
            download_query = download_query.set(
                "download", "" if download is True else download
            )

        render_path = ["render", "image"] if transform else ["object"]
        transformation = transform_to_dict(transform) if transform else dict()

        path_parts = relative_path_to_parts(path)
        url = (
            self.base_url.joinpath(*render_path, "public", self.id, *path_parts)
            .with_query(download_query)
            .extend_query(transformation)
        )
        return str(url)

    @handle_http_response
    def move(self, from_path: str, to_path: str) -> ResponseHandler[MessageResponse]:
        """
        Moves an existing file, optionally renaming it at the same time.

        Parameters
        ----------
        from_path
            The original file path, including the current file name. For example `folder/image.png`.
        to_path
            The new file path, including the new file name. For example `folder/image-copy.png`.
        """
        request = JSONRequest(
            method="POST",
            path=["object", "move"],
            body={
                "bucketId": self.id,
                "sourceKey": from_path,
                "destinationKey": to_path,
            },
            headers=self._headers,
        )
        return ResponseCases(
            request=request,
            on_success=validate_model(MessageResponse),
            on_failure=parse_api_error,
        )

    @handle_http_response
    def copy(self, from_path: str, to_path: str) -> ResponseHandler[UploadResponse]:
        """
        Copies an existing file to a new path in the same bucket.

        Parameters
        ----------
        from_path
            The original file path, including the current file name. For example `folder/image.png`.
        to_path
            The new file path, including the new file name. For example `folder/image-copy.png`.
        """
        request = JSONRequest(
            method="POST",
            path=["object", "copy"],
            body={
                "bucketId": self.id,
                "sourceKey": from_path,
                "destinationKey": to_path,
            },
            headers=self._headers,
        )

        return ResponseCases(
            request=request,
            on_success=validate_model(UploadResponse),
            on_failure=parse_api_error,
        )

    @handle_http_response
    def remove(self, paths: list[str]) -> ResponseHandler[list[FileObject]]:
        """
        Deletes files within the same bucket

        Parameters
        ----------
        paths
            An array or list of files to be deletes, including the path and file name. For example [`folder/image.png`].
        """
        request = JSONRequest(
            method="DELETE",
            path=["object", self.id],
            body={"prefixes": paths},
            headers=self._headers,
        )
        return ResponseCases(
            request=request,
            on_success=validate_adapter(TypeAdapter(list[FileObject])),
            on_failure=parse_api_error,
        )

    @handle_http_response
    def info(
        self,
        path: str,
    ) -> ResponseHandler[FileObject]:
        """
        Lists info for a particular file.

        Parameters
        ----------
        path
            The path to the file.
        """
        path_parts: tuple[str, ...] = relative_path_to_parts(path)  # split paths by /
        request = EmptyRequest(
            method="GET",
            path=["object", "info", self.id, *path_parts],
            headers=self._headers,
        )
        return ResponseCases(
            request=request,
            on_success=validate_model(FileObject),
            on_failure=parse_api_error,
        )

    @handle_http_response
    def exists(
        self,
        path: str,
    ) -> ResponseHandler[bool]:
        """
        Returns True if the file exists, False otherwise.

        Parameters
        ----------
        path
            The path to the file.
        """

        def return_false_on_400(response: Response) -> bool:
            if response.is_success:
                return True
            elif 400 <= response.status_code <= 401:
                return False
            else:
                raise parse_api_error(response)

        path_parts: tuple[str, ...] = relative_path_to_parts(path)  # split paths by /
        request = EmptyRequest(
            method="HEAD",
            path=["object", self.id, *path_parts],
            headers=self._headers,
        )
        return ResponseHandler(
            request=request,
            callback=return_false_on_400,
        )

    @handle_http_response
    def list(
        self,
        path: str | None = None,
        limit: int = 100,
        offset: int = 0,
        search: str | None = None,
        sortBy: SortByType | None = None,
    ) -> ResponseHandler[list[ListFileObject]]:
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
        request = JSONRequest(
            method="POST",
            path=["object", "list", self.id],
            body=body,
            headers=self._headers,
        )
        return ResponseCases(
            request=request,
            on_success=validate_adapter(TypeAdapter(list[ListFileObject])),
            on_failure=parse_api_error,
        )

    @handle_http_response
    def list_v2(
        self,
        limit: int | None = None,
        prefix: str | None = None,
        cursor: str | None = None,
        with_delimiter: bool | None = None,
        sort_by: SortByV2 | None = None,
    ) -> ResponseHandler[SearchV2Result]:
        body = SearchV2Body(
            limit=limit,
            prefix=prefix,
            cursor=cursor,
            with_delimiter=with_delimiter,
            sortBy=sort_by,
        )
        request = JSONRequest(
            method="POST",
            path=["object", "list-v2", self.id],
            body=body,
            exclude_none=True,
            headers=self._headers,
        )
        return ResponseCases(
            request=request,
            on_success=validate_model(SearchV2Result),
            on_failure=parse_api_error,
        )

    @handle_http_response
    def download(
        self,
        path: str,
        transform: TransformOptions | None = None,
        query_params: dict[str, str] | None = None,
    ) -> ResponseHandler[bytes]:
        """
        Downloads a file.

        Parameters
        ----------
        path
            The file path to be downloaded, including the path and file name. For example `folder/image.png`.
        """
        render_path: list[str] = ["object"]
        params = QueryParams(query_params)
        if transform:
            params = params.merge(transform_to_dict(transform))
            render_path = ["render", "image", "authenticated"]
        path_parts: tuple[str, ...] = relative_path_to_parts(path)
        request = EmptyRequest(
            method="GET",
            path=[*render_path, self.id, *path_parts],
            query_params=params,
            headers=self._headers,
        )

        return ResponseCases(
            request=request,
            on_success=lambda response: response.content,
            on_failure=parse_api_error,
        )

    def _upload_or_update(
        self,
        method: Literal["POST", "PUT"],
        path: tuple[str, ...],
        file: BufferedReader | bytes | FileIO | str | Path,
        cache_control: str,
        content_type: str,
        upsert: str,
        metadata: dict[str, Any] | None,
        headers: dict[str, str] | None,
    ) -> ResponseHandler[UploadResponse]:
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

        extra_headers = Headers(headers)

        extra_headers["x-upsert"] = upsert
        extra_headers["cache-control"] = f"max-age={cache_control}"

        extra_headers.update(self._headers)

        data = {"cacheControl": cache_control}
        data = {}
        if metadata:
            metadata_bytes = JSONParser.dump_json(metadata)
            extra_headers["x-metadata"] = base64.b64encode(metadata_bytes).decode(
                "utf-8"
            )
            data["metadata"] = metadata_bytes.decode("utf-8")

        # Only include x-upsert on a POST method
        if method != "POST":
            del extra_headers["x-upsert"]

        filename = path[-1]

        if isinstance(file, (BufferedReader, bytes, FileIO)):
            # bytes or byte-stream-like object received
            file_contents = file
        else:
            # str or pathlib.path received
            with open(file, "rb") as f:
                file_contents = f.read()

        files = {"file": (filename, file_contents, content_type)}
        request = MultipartFormDataRequest(
            method=method,
            path=["object", self.id, *path],
            files=files,
            headers=extra_headers,
            data=data,
        )

        return ResponseCases(
            request=request,
            on_success=validate_model(UploadResponse),
            on_failure=parse_api_error,
        )

    @handle_http_response
    def upload(
        self,
        path: str,
        file: BufferedReader | bytes | FileIO | str | Path,
        cache_control: str = "3600",
        content_type: str = "text/plain;charset=UTF-8",
        upsert: str = "false",
        metadata: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> ResponseHandler[UploadResponse]:
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

    @handle_http_response
    def update(
        self,
        path: str,
        file: BufferedReader | bytes | FileIO | str | Path,
        cache_control: str = "3600",
        content_type: str = "text/plain;charset=UTF-8",
        upsert: str = "false",
        metadata: dict[str, Any] | None = None,
        headers: dict[str, str] | None = None,
    ) -> ResponseHandler[UploadResponse]:
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
