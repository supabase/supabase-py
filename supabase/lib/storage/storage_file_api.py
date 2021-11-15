from typing import Any

import httpx
from httpx import HTTPError


class StorageFileAPI:
    DEFAULT_SEARCH_OPTIONS = {
        "limit": 100,
        "offset": 0,
        "sortBy": {
            "column": "name",
            "order": "asc",
        },
    }
    DEFAULT_FILE_OPTIONS = {
        "cacheControl": "3600",
        "contentType": "text/plain;charset=UTF-8",
        "x-upsert": "false",
    }

    def __init__(self, url: str, headers: dict, bucket_id: str):
        """
        Parameters
        ----------
        url
            base url for all the operation
        headers
            the base authentication headers
        bucket_id
            the id of the bucket that we want to access, you can get the list of buckets with the SupabaseStorageClient.list_buckets()
        """
        self.url = url
        self.headers = headers
        self.bucket_id = bucket_id
        # self.loop = asyncio.get_event_loop()
        # self.replace = replace

    def create_signed_url(self, path: str, expires_in: int):
        """
        Parameters
        ----------
        path
            file path to be downloaded, including the current file name.
        expires_in
            number of seconds until the signed URL expires.
        """
        try:
            _path = self._get_final_path(path)
            response = httpx.post(
                f"{self.url}/object/sign/{_path}",
                json={"expiresIn": str(expires_in)},
                headers=self.headers,
            )
            data = response.json()
            data["signedURL"] = f"{self.url}{data['signedURL']}"
            response.raise_for_status()
        except HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")  # Python 3.6
        except Exception as err:
            print(f"Other error occurred: {err}")  # Python 3.6
        else:
            return data

    def get_public_url(self, path: str):
        """
        Parameters
        ----------
        path
            file path to be downloaded, including the path and file name. For example `folder/image.png`.
        """
        try:
            _path = self._get_final_path(path)
            public_url = f"{self.url}/object/public/{_path}"
            return public_url
        except:
            print("Public URL not found")

    def move(self, from_path: str, to_path: str):
        """
        Moves an existing file, optionally renaming it at the same time.
        Parameters
        ----------
        from_path
            The original file path, including the current file name. For example `folder/image.png`.
        to_path
            The new file path, including the new file name. For example `folder/image-copy.png`.
        """
        try:
            response = httpx.post(
                f"{self.url}/object/move",
                json={
                    "bucketId": self.bucket_id,
                    "sourceKey": from_path,
                    "destinationKey": to_path,
                },
                headers=self.headers,
            )
            response.raise_for_status()
        except HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")  # Python 3.6
        except Exception as err:
            print(f"Other error occurred: {err}")  # Python 3.6
        else:
            return response.json()

    def remove(self, paths: list):
        """
        Deletes files within the same bucket
        Parameters
        ----------
        paths
            An array or list of files to be deletes, including the path and file name. For example [`folder/image.png`].
        """
        try:
            response = httpx.request(
                "DELETE",
                f"{self.url}/object/{self.bucket_id}",
                json={"prefixes": paths},
                headers=self.headers,
            )
            response.raise_for_status()
        except HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")  # Python 3.6
        except Exception as err:
            raise err  # Python 3.6
        else:
            return response.json()

    def list(self, path: str = None, options: dict = {}):
        """
        Lists all the files within a bucket.
        Parameters
        ----------
        path
            The folder path.
        options
            Search options, including `limit`, `offset`, and `sortBy`.
        """
        try:
            body = dict(self.DEFAULT_SEARCH_OPTIONS, **options)
            headers = dict(self.headers, **{"Content-Type": "application/json"})
            body["prefix"] = path if path else ""
            getdata = httpx.post(
                f"{self.url}/object/list/{self.bucket_id}",
                json=body,
                headers=headers,
            )
            getdata.raise_for_status()
        except HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")  # Python 3.6
        except Exception as err:
            raise err  # Python 3.6
        else:
            return getdata.json()

    def download(self, path: str):
        """
        Downloads a file.
        Parameters
        ----------
        path The file path to be downloaded, including the path and file name. For example `folder/image.png`.
        """
        try:
            _path = self._get_final_path(path)
            response = httpx.get(f"{self.url}/object/{_path}", headers=self.headers)

        except HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")  # Python 3.6
        except Exception as err:
            raise err  # Python 3.6
        else:
            return response.content

    def upload(self, path: str, file: Any, file_options: dict = None):
        """
        Uploads a file to an existing bucket.
        Parameters
        ----------
        path
            The relative file path including the bucket ID. Should be of the format `bucket/folder/subfolder/filename.png`. The bucket must already exist before attempting to upload.
        file
            The File object to be stored in the bucket. or a async generator of chunks
        file_options
            HTTP headers. For example `cacheControl`
        """
        if file_options is None:
            file_options = {}
        headers = dict(self.headers, **self.DEFAULT_FILE_OPTIONS)
        headers.update(file_options)
        filename = path.rsplit("/", maxsplit=1)[-1]
        files = {"file": (filename, open(file, "rb"), headers["contentType"])}
        _path = self._get_final_path(path)
        try:
            resp = httpx.post(
                f"{self.url}/object/{_path}",
                files=files,
                headers=headers,
            )
        except HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")  # Python 3.6
        except Exception as err:
            raise err  # Python 3.6
        else:
            return resp

    def _get_final_path(self, path: str):
        return f"{self.bucket_id}/{path}"
