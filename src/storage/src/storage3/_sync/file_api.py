from __future__ import annotations

import base64
import json
import urllib.parse
from dataclasses import dataclass, field
from io import BufferedReader, FileIO
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Union, cast

from httpx import Client, Headers, HTTPStatusError, Response
from yarl import URL

from ..constants import DEFAULT_FILE_OPTIONS, DEFAULT_SEARCH_OPTIONS
from ..exceptions import StorageApiError
from ..types import (
    BaseBucket,
    CreateSignedUploadUrlOptions,
    CreateSignedUrlResponse,
    CreateSignedURLsOptions,
    DownloadOptions,
    FileOptions,
    ListBucketFilesOptions,
    RequestMethod,
    SearchV2Options,
    SearchV2Result,
    SignedUploadURL,
    SignedUrlJsonResponse,
    SignedUrlResponse,
    SignedUrlsJsonResponse,
    TransformOptions,
    UploadData,
    UploadResponse,
    UploadSignedUrlFileOptions,
    URLOptions,
    transform_to_dict,
)
from ..utils import StorageException

__all__ = ["SyncBucket"]


def relative_path_to_parts(path: str) -> tuple[str, ...]:
    url = URL(path)
    if url.absolute or url.parts[0] == "/":
        return url.parts[1:]
    return url.parts


class SyncBucketActionsMixin:
    """Functions needed to access the file API."""

    id: str
    _base_url: URL
    _client: Client
    _headers: Headers

    def _request(
        self,
        method: RequestMethod,
        path: list[str],
        headers: Optional[dict[str, Any]] = None,
        json: Optional[dict[Any, Any]] = None,
        files: Optional[Any] = None,
        query_params: Optional[dict[str, str]] = None,
        **kwargs: Any,
    ) -> Response:
        try:
            url_path = self._base_url.joinpath(*path).with_query(query_params)
            headers = headers or dict()
            headers.update(self._headers)
            response = self._client.request(
                method,
                str(url_path),
                headers=headers,
                json=json,
                files=files,
                **kwargs,
            )
            response.raise_for_status()
        except HTTPStatusError as exc:
            try:
                resp = exc.response.json()
                raise StorageApiError(
                    resp["message"], resp["error"], resp["statusCode"]
                ) from exc
            except KeyError as err:
                message = f"Unable to parse error message: {resp.text}"
                raise StorageApiError(message, "InternalError", 400) from err

        # close the resource before returning the response
        if files and "file" in files and isinstance(files["file"][1], BufferedReader):
            files["file"][1].close()

        return response

    def create_signed_upload_url(
        self,
        path: str,
        options: Optional[CreateSignedUploadUrlOptions] = None,
    ) -> SignedUploadURL:
        """
        Creates a signed upload URL.

        Parameters
        ----------
        path
            The file path, including the file name. For example `folder/image.png`.
        options
            Additional options for the upload url creation.
        """
        headers: dict[str, str] = dict()
        if options is not None and options.upsert:
            headers.update({"x-upsert": options.upsert})

        path_parts = relative_path_to_parts(path)
        response = self._request(
            "POST", ["object", "upload", "sign", self.id, *path_parts], headers=headers
        )
        data = response.json()
        full_url: urllib.parse.ParseResult = urllib.parse.urlparse(
            str(self._base_url) + cast(str, data["url"]).lstrip("/")
        )
        query_params = urllib.parse.parse_qs(full_url.query)
        if not query_params.get("token"):
            raise StorageException("No token sent by the API")
        return {
            "signed_url": full_url.geturl(),
            "signedUrl": full_url.geturl(),
            "token": query_params["token"][0],
            "path": path,
        }

    def upload_to_signed_url(
        self,
        path: str,
        token: str,
        file: Union[BufferedReader, bytes, FileIO, str, Path],
        file_options: Optional[UploadSignedUrlFileOptions] = None,
    ) -> UploadResponse:
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
        file_options
            Additional options for the uploaded file
        """
        path_parts = relative_path_to_parts(path)
        query_params = {"token": token}

        final_url = ["object", "upload", "sign", self.id, *path_parts]

        options: UploadSignedUrlFileOptions = file_options or {}
        cache_control = options.get("cache-control")
        # cacheControl is also passed as form data
        # https://github.com/supabase/storage-js/blob/fa44be8156295ba6320ffeff96bdf91016536a46/src/packages/StorageFileApi.ts#L89
        _data = {}
        if cache_control:
            options["cache-control"] = f"max-age={cache_control}"
            _data = {"cacheControl": cache_control}
        headers = {
            **self._client.headers,
            **DEFAULT_FILE_OPTIONS,
            **options,
        }
        filename = path_parts[-1]

        if (
            isinstance(file, BufferedReader)
            or isinstance(file, bytes)
            or isinstance(file, FileIO)
        ):
            # bytes or byte-stream-like object received
            _file = {"file": (filename, file, headers.pop("content-type"))}
        else:
            # str or pathlib.path received
            _file = {
                "file": (
                    filename,
                    open(file, "rb"),
                    headers.pop("content-type"),
                )
            }
        response = self._request(
            "PUT",
            final_url,
            files=_file,
            headers=headers,
            data=_data,
            query_params=query_params,
        )
        data: UploadData = response.json()

        return UploadResponse(path=path, Key=data["Key"])

    def _make_signed_url(
        self, signed_url: str, download_query: dict[str, str]
    ) -> SignedUrlResponse:
        url = URL(signed_url[1:])  # ignore starting slash
        signedURL = self._base_url.join(url).extend_query(download_query)
        return {"signedURL": str(signedURL), "signedUrl": str(signedURL)}

    def create_signed_url(
        self, path: str, expires_in: int, options: Optional[URLOptions] = None
    ) -> SignedUrlResponse:
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
        json: dict[str, str | bool | TransformOptions] = {"expiresIn": str(expires_in)}
        download_query = {}
        url_options = options or {}
        if download := url_options.get("download"):
            json.update({"download": download})
            download_query = {"download": "" if download is True else download}
        if transform := url_options.get("transform"):
            json.update({"transform": transform})

        path_parts = relative_path_to_parts(path)
        response = self._request(
            "POST",
            ["object", "sign", self.id, *path_parts],
            json=json,
        )

        data = SignedUrlJsonResponse.model_validate_json(response.content)
        return self._make_signed_url(data.signedURL, download_query)

    def create_signed_urls(
        self,
        paths: List[str],
        expires_in: int,
        options: Optional[CreateSignedURLsOptions] = None,
    ) -> List[CreateSignedUrlResponse]:
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
        json: dict[str, str | bool | None | list[str]] = {
            "paths": paths,
            "expiresIn": str(expires_in),
        }
        download_query = {}
        url_options = options or {}
        if download := url_options.get("download"):
            json.update({"download": download})
            download_query = {"download": "" if download is True else download}

        response = self._request(
            "POST",
            ["object", "sign", self.id],
            json=json,
        )
        data = SignedUrlsJsonResponse.validate_json(response.content)
        signed_urls = []
        for item in data:
            # Prepare URL
            url = self._make_signed_url(item.signedURL, download_query)
            signed_item: CreateSignedUrlResponse = {
                "error": item.error,
                "path": item.path,
                "signedURL": url["signedURL"],
                "signedUrl": url["signedURL"],
            }
            signed_urls.append(signed_item)
        return signed_urls

    def get_public_url(self, path: str, options: Optional[URLOptions] = None) -> str:
        """
        Parameters
        ----------
        path
            file path, including the path and file name. For example `folder/image.png`.
        """
        download_query = {}
        url_options = options or {}
        if download := url_options.get("download"):
            download_query = {"download": "" if download is True else download}

        render_path = (
            ["render", "image"] if url_options.get("transform") else ["object"]
        )
        transformation = (
            transform_to_dict(t) if (t := url_options.get("transform")) else dict()
        )

        path_parts = relative_path_to_parts(path)
        url = (
            self._base_url.joinpath(*render_path, "public", self.id, *path_parts)
            .with_query(download_query)
            .extend_query(transformation)
        )
        return str(url)

    def move(self, from_path: str, to_path: str) -> dict[str, str]:
        """
        Moves an existing file, optionally renaming it at the same time.

        Parameters
        ----------
        from_path
            The original file path, including the current file name. For example `folder/image.png`.
        to_path
            The new file path, including the new file name. For example `folder/image-copy.png`.
        """
        res = self._request(
            "POST",
            ["object", "move"],
            json={
                "bucketId": self.id,
                "sourceKey": from_path,
                "destinationKey": to_path,
            },
        )
        return res.json()

    def copy(self, from_path: str, to_path: str) -> dict[str, str]:
        """
        Copies an existing file to a new path in the same bucket.

        Parameters
        ----------
        from_path
            The original file path, including the current file name. For example `folder/image.png`.
        to_path
            The new file path, including the new file name. For example `folder/image-copy.png`.
        """
        res = self._request(
            "POST",
            ["object", "copy"],
            json={
                "bucketId": self.id,
                "sourceKey": from_path,
                "destinationKey": to_path,
            },
        )
        return res.json()

    def remove(self, paths: list[str]) -> list[dict[str, Any]]:
        """
        Deletes files within the same bucket

        Parameters
        ----------
        paths
            An array or list of files to be deletes, including the path and file name. For example [`folder/image.png`].
        """
        response = self._request(
            "DELETE",
            ["object", self.id],
            json={"prefixes": paths},
        )
        return response.json()

    def info(
        self,
        path: str,
    ) -> dict[str, Any]:
        """
        Lists info for a particular file.

        Parameters
        ----------
        path
            The path to the file.
        """
        path_parts = relative_path_to_parts(path)  # split paths by /
        response = self._request(
            "GET",
            ["object", "info", self.id, *path_parts],
        )
        return response.json()

    def exists(
        self,
        path: str,
    ) -> bool:
        """
        Returns True if the file exists, False otherwise.

        Parameters
        ----------
        path
            The path to the file.
        """
        try:
            path_parts = relative_path_to_parts(path)  # split paths by /
            response = self._request(
                "HEAD",
                ["object", self.id, *path_parts],
            )
            return response.status_code == 200
        except json.JSONDecodeError:
            return False

    def list(
        self,
        path: Optional[str] = None,
        options: Optional[ListBucketFilesOptions] = None,
    ) -> list[dict[str, Any]]:
        """
        Lists all the files within a bucket.

        Parameters
        ----------
        path
            The folder path.
        options
            Search options, including `limit`, `offset`, `sortBy` and `search`.
        """
        extra_options = options or {}
        extra_headers = {"Content-Type": "application/json"}
        body = {
            **DEFAULT_SEARCH_OPTIONS,
            **extra_options,
            "prefix": path or "",
        }
        response = self._request(
            "POST",
            ["object", "list", self.id],
            json=body,
            headers=extra_headers,
        )
        return response.json()

    def list_v2(
        self,
        options: Optional[SearchV2Options] = None,
    ) -> SearchV2Result:
        body = {**options} if options else {}
        response = self._request(
            "POST",
            ["object", "list-v2", self.id],
            json=body,
        )
        return SearchV2Result.model_validate_json(response.content)

    def download(
        self,
        path: str,
        options: Optional[DownloadOptions] = None,
        query_params: Optional[Dict[str, str]] = None,
    ) -> bytes:
        """
        Downloads a file.

        Parameters
        ----------
        path
            The file path to be downloaded, including the path and file name. For example `folder/image.png`.
        """
        url_options = options or DownloadOptions()
        render_path = (
            ["render", "image", "authenticated"]
            if url_options.get("transform")
            else ["object"]
        )

        transform_options = url_options.get("transform") or TransformOptions()

        path_parts = relative_path_to_parts(path)
        response = self._request(
            "GET",
            [*render_path, self.id, *path_parts],
            query_params={
                **transform_to_dict(transform_options),
                **(query_params or {}),
            },
        )
        return response.content

    def _upload_or_update(
        self,
        method: Literal["POST", "PUT"],
        path: tuple[str, ...],
        file: Union[BufferedReader, bytes, FileIO, str, Path],
        file_options: Optional[FileOptions] = None,
    ) -> UploadResponse:
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
        if file_options is None:
            file_options = {}
        cache_control = file_options.pop("cache-control", None)
        _data = {}

        upsert = file_options.pop("upsert", None)
        if upsert:
            file_options.update({"x-upsert": upsert})

        metadata = file_options.pop("metadata", None)
        file_opts_headers = file_options.pop("headers", None)

        headers = {
            **self._client.headers,
            **DEFAULT_FILE_OPTIONS,
            **file_options,
        }

        if metadata:
            metadata_str = json.dumps(metadata)
            headers["x-metadata"] = base64.b64encode(metadata_str.encode())
            _data.update({"metadata": metadata_str})

        if file_opts_headers:
            headers.update({**file_opts_headers})

        # Only include x-upsert on a POST method
        if method != "POST":
            del headers["x-upsert"]

        filename = path[-1]

        if cache_control:
            headers["cache-control"] = f"max-age={cache_control}"
            _data.update({"cacheControl": cache_control})

        if (
            isinstance(file, BufferedReader)
            or isinstance(file, bytes)
            or isinstance(file, FileIO)
        ):
            # bytes or byte-stream-like object received
            files = {"file": (filename, file, headers.pop("content-type"))}
        else:
            # str or pathlib.path received
            files = {
                "file": (
                    filename,
                    open(file, "rb"),
                    headers.pop("content-type"),
                )
            }

        response = self._request(
            method, ["object", self.id, *path], files=files, headers=headers, data=_data
        )

        data: UploadData = response.json()

        return UploadResponse(path="/".join(path), Key=data["Key"])

    def upload(
        self,
        path: str,
        file: Union[BufferedReader, bytes, FileIO, str, Path],
        file_options: Optional[FileOptions] = None,
    ) -> UploadResponse:
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
        return self._upload_or_update("POST", path_parts, file, file_options)

    def update(
        self,
        path: str,
        file: Union[BufferedReader, bytes, FileIO, str, Path],
        file_options: Optional[FileOptions] = None,
    ) -> UploadResponse:
        path_parts = relative_path_to_parts(path)
        return self._upload_or_update("PUT", path_parts, file, file_options)


class SyncBucket(BaseBucket):
    """Represents a storage bucket."""


@dataclass
class SyncBucketProxy(SyncBucketActionsMixin):
    """A bucket proxy, this contains the minimum required fields to query the File API."""

    id: str
    _base_url: URL
    _headers: Headers
    _client: Client = field(repr=False)
