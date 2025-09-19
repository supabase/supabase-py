from __future__ import annotations

import base64
import json
import urllib.parse
from dataclasses import dataclass, field
from io import BufferedReader, FileIO
from pathlib import Path
from typing import Any, Literal, Optional, Union, cast

from httpx import Client, HTTPStatusError, Response

from ..constants import DEFAULT_FILE_OPTIONS, DEFAULT_SEARCH_OPTIONS
from ..exceptions import StorageApiError
from ..types import (
    BaseBucket,
    CreateSignedUrlResponse,
    CreateSignedURLsOptions,
    DownloadOptions,
    FileOptions,
    ListBucketFilesOptions,
    RequestMethod,
    SignedUploadURL,
    SignedUrlResponse,
    TransformOptions,
    UploadData,
    UploadResponse,
    URLOptions,
)
from ..utils import StorageException

__all__ = ["SyncBucket"]


class SyncBucketActionsMixin:
    """Functions needed to access the file API."""

    id: str
    _client: Client

    def _request(
        self,
        method: RequestMethod,
        url: str,
        headers: Optional[dict[str, Any]] = None,
        json: Optional[dict[Any, Any]] = None,
        files: Optional[Any] = None,
        **kwargs: Any,
    ) -> Response:
        try:
            response = self._client.request(
                method, url, headers=headers or {}, json=json, files=files, **kwargs
            )
            response.raise_for_status()
        except HTTPStatusError as exc:
            resp = exc.response.json()
            raise StorageApiError(resp["message"], resp["error"], resp["statusCode"])

        # close the resource before returning the response
        if files and "file" in files and isinstance(files["file"][1], BufferedReader):
            files["file"][1].close()

        return response

    def create_signed_upload_url(self, path: str) -> SignedUploadURL:
        """
        Creates a signed upload URL.

        Parameters
        ----------
        path
            The file path, including the file name. For example `folder/image.png`.
        """
        _path = self._get_final_path(path)
        response = self._request("POST", f"/object/upload/sign/{_path}")
        data = response.json()
        full_url: urllib.parse.ParseResult = urllib.parse.urlparse(
            str(self._client.base_url) + cast(str, data["url"]).lstrip("/")
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
        file_options: Optional[FileOptions] = None,
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
        _path = self._get_final_path(path)
        _url = urllib.parse.urlparse(f"/object/upload/sign/{_path}")
        query_params = urllib.parse.urlencode({"token": token})
        final_url = f"{_url.geturl()}?{query_params}"

        if file_options is None:
            file_options = {}

        cache_control = file_options.get("cache-control")
        # cacheControl is also passed as form data
        # https://github.com/supabase/storage-js/blob/fa44be8156295ba6320ffeff96bdf91016536a46/src/packages/StorageFileApi.ts#L89
        _data = {}
        if cache_control:
            file_options["cache-control"] = f"max-age={cache_control}"
            _data = {"cacheControl": cache_control}
        headers = {
            **self._client.headers,
            **DEFAULT_FILE_OPTIONS,
            **file_options,
        }
        filename = path.rsplit("/", maxsplit=1)[-1]

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
            "PUT", final_url, files=_file, headers=headers, data=_data
        )
        data: UploadData = response.json()

        return UploadResponse(path=path, Key=data.get("Key"))

    def create_signed_url(
        self, path: str, expires_in: int, options: URLOptions = {}
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
        download_query = ""
        if options.get("download"):
            json.update({"download": options["download"]})

            download_query = (
                "&download="
                if options.get("download") is True
                else f"&download={options.get('download')}"
            )
        if options.get("transform"):
            json.update({"transform": options["transform"]})

        path = self._get_final_path(path)
        response = self._request(
            "POST",
            f"/object/sign/{path}",
            json=json,
        )
        data = response.json()

        # Prepare URL
        url = urllib.parse.urlparse(data["signedURL"])
        url = urllib.parse.quote(url.path) + f"?{url.query}"

        signedURL = (
            f"{self._client.base_url}{cast(str, url).lstrip('/')}{download_query}"
        )
        data: SignedUrlResponse = {"signedURL": signedURL, "signedUrl": signedURL}
        return data

    def create_signed_urls(
        self, paths: list[str], expires_in: int, options: CreateSignedURLsOptions = {}
    ) -> list[CreateSignedUrlResponse]:
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
        download_query = ""
        if options.get("download"):
            json.update({"download": options.get("download")})

            download_query = (
                "&download="
                if options.get("download") is True
                else f"&download={options.get('download')}"
            )

        response = self._request(
            "POST",
            f"/object/sign/{self.id}",
            json=json,
        )
        data = response.json()
        signed_urls = []
        for item in data:
            # Prepare URL
            url = urllib.parse.urlparse(item["signedURL"])
            url = urllib.parse.quote(url.path) + f"?{url.query}"

            signedURL = (
                f"{self._client.base_url}{cast(str, url).lstrip('/')}{download_query}"
            )
            signed_item: CreateSignedUrlResponse = {
                "error": item["error"],
                "path": item["path"],
                "signedURL": signedURL,
                "signedUrl": signedURL,
            }
            signed_urls.append(signed_item)
        return signed_urls

    def get_public_url(self, path: str, options: URLOptions = {}) -> str:
        """
        Parameters
        ----------
        path
            file path, including the path and file name. For example `folder/image.png`.
        """
        _query_string = []
        download_query = ""
        if options.get("download"):
            download_query = (
                "&download="
                if options.get("download") is True
                else f"&download={options.get('download')}"
            )

        if download_query:
            _query_string.append(download_query)

        render_path = "render/image" if options.get("transform") else "object"
        transformation_query = (
            urllib.parse.urlencode(t) if (t := options.get("transform")) else None
        )

        if transformation_query:
            _query_string.append(transformation_query)

        query_string = "&".join(_query_string)
        query_string = f"?{query_string}"
        _path = self._get_final_path(path)
        return f"{self._client.base_url}{render_path}/public/{_path}{query_string}"

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
            "/object/move",
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
            "/object/copy",
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
            f"/object/{self.id}",
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
        response = self._request(
            "GET",
            f"/object/info/{self.id}/{path}",
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
            response = self._request(
                "HEAD",
                f"/object/{self.id}/{path}",
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
            f"/object/list/{self.id}",
            json=body,
            headers=extra_headers,
        )
        return response.json()

    def download(self, path: str, options: DownloadOptions = {}) -> bytes:
        """
        Downloads a file.

        Parameters
        ----------
        path
            The file path to be downloaded, including the path and file name. For example `folder/image.png`.
        """
        render_path = (
            "render/image/authenticated" if options.get("transform") else "object"
        )
        transformation_query = urllib.parse.urlencode(options.get("transform") or {})
        query_string = f"?{transformation_query}" if transformation_query else ""

        _path = self._get_final_path(path)
        response = self._request(
            "GET",
            f"{render_path}/{_path}{query_string}",
        )
        return response.content

    def _upload_or_update(
        self,
        method: Literal["POST", "PUT"],
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

        filename = path.rsplit("/", maxsplit=1)[-1]

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

        _path = self._get_final_path(path)

        response = self._request(
            method, f"/object/{_path}", files=files, headers=headers, data=_data
        )

        data: UploadData = response.json()

        return UploadResponse(path=path, Key=data.get("Key"))

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
        return self._upload_or_update("POST", path, file, file_options)

    def update(
        self,
        path: str,
        file: Union[BufferedReader, bytes, FileIO, str, Path],
        file_options: Optional[FileOptions] = None,
    ) -> UploadResponse:
        return self._upload_or_update("PUT", path, file, file_options)

    def _get_final_path(self, path: str) -> str:
        return f"{self.id}/{path}"


class SyncBucket(BaseBucket):
    """Represents a storage bucket."""


@dataclass
class SyncBucketProxy(SyncBucketActionsMixin):
    """A bucket proxy, this contains the minimum required fields to query the File API."""

    id: str
    _client: Client = field(repr=False)
