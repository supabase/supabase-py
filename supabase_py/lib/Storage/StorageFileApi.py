from typing import Optional

import aiohttp
import requests
from requests import HTTPError
import asyncio
from supabase_py.lib.Storage.RequestError import RequestError


class StorageFileApi():
    """A class used to manage storage ."""

    DEFAULT_SEARCH_OPTIONS = {
        "offset": 0,
        "sortBy": {
            "column": 'name',
            "order": 'asc',
        },
    }

    DEFAULT_FILE_OPTIONS = {
        "cacheControl": '3600',
    }

    def __init__(self, url: str, headers: dict, bucket_id: str):
        """
        Create a  storage  api manager

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
        self.loop = asyncio.get_event_loop()

    async def upload(self, path: str, file: str, file_options: dict = None):
        """
        Uploads a file to an existing bucket.

        Parameters
        ----------
        path
            The relative file path including the bucket ID. Should be of the format `bucket/folder/subfolder/filename.png`. The bucket must already exist before attempting to upload.
        file
            The File object to be stored in the bucket.
        file_options
            HTTP headers. For example `cacheControl`
        """
        if file_options is None:
            file_options = {}
        headers = dict(self.headers, **file_options)
        async with aiohttp.ClientSession(headers=headers) as session:
            files = {'file': open(file, 'rb')}
            _path = self._getFinalPath(path)

            async with session.post(f"{self.url}/object/{_path}", data=files) as response:
                if response.status != 200:
                    resp = await response.json()
                    raise RequestError(resp["statusCode"], resp["error"], resp["message"])
                return None

    async def update(self, path: str, file: str, file_options: dict = None):
        """
        Replaces an existing file at the specified path with a new one.

        Parameters
        ----------
        path
            The relative file path including the bucket ID. Should be of the format `bucket/folder/subfolder/filename.png`. The bucket must already exist before attempting to upload.
        file
            The File object to be stored in the bucket.
        file_options
            HTTP headers. For example `cacheControl`
        """
        if file_options is None:
            file_options = {}
        headers = dict(self.headers, **file_options)
        async with aiohttp.ClientSession(headers=headers) as session:
            files = {'file': open(file, 'rb')}
            _path = self._getFinalPath(path)

            async with session.put(f"{self.url}/object/{_path}", data=files) as response:
                if response.status != 200:
                    resp = await response.json()
                    raise RequestError(resp["statusCode"], resp["error"], resp["message"])
                return None

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
            response = requests.post(f"{self.url}/object/move", data={"bucketId": self.bucket_id,
                                                                      "sourceKey": from_path,
                                                                      "destinationKey": to_path},
                                     headers=self.headers)
            # If the response was successful, no Exception will be raised
            response.raise_for_status()
        except HTTPError as http_err:
            print(f'HTTP error occurred: {http_err}')  # Python 3.6
        except Exception as err:
            print(f'Other error occurred: {err}')  # Python 3.6
        else:
            return response.json()

    def create_signed_url(self, path: str, expires_in: int):
        """
        Create signed url to download file without requiring permissions. This URL can be valid for a set number of seconds.

        Parameters
        ----------
        path
            The original file path, including the current file name. For example `folder/image.png`.

        expires_in
            The number of seconds until the signed URL expires. For example, `60` for a URL which is valid for one minute.
        """

        try:
            _path = self._getFinalPath(path)
            response = requests.post(f"{self.url}/object/sign/{_path}", json={"expiresIn": str(expires_in)},

                                     headers=self.headers)
            data = response.json()
            data["signedURL"] = f"{self.url}{data['signedURL']}"
            response.raise_for_status()
        except HTTPError as http_err:
            print(f'HTTP error occurred: {http_err}')  # Python 3.6
        except Exception as err:
            print(f'Other error occurred: {err}')  # Python 3.6
        else:
            return data

    async def download(self, path: str) -> Optional[bytes]:
        """
        Downloads a file.

        Parameters
        ----------
        path
            The original file path, including the current file name. For example `folder/image.png`.

        Returns
        -------
        bytes
            The bytes of the files
        """
        async with aiohttp.ClientSession(headers=self.headers) as session:
            _path = self._getFinalPath(path)
            async with session.get(f"{self.url}/object/{_path}") as resp:
                resp.raise_for_status()
                if resp.status == 200:
                    return await resp.read()  # this is not good for big files it should be a generator.

        return None

    def remove(self, paths: list):
        """
        Deletes files within the same bucket

        Parameters
        ----------
        paths
            An array or list of files to be deletes, including the path and file name. For example [`folder/image.png`].
        """
        try:
            response = requests.delete(f"{self.url}/object/{self.bucket_id}", data={"prefixes": paths},
                                       headers=self.headers)
            response.raise_for_status()
        except HTTPError as http_err:
            print(f'HTTP error occurred: {http_err}')  # Python 3.6
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
            headers = dict(self.headers, **{'Content-Type': "application/json"})
            body["prefix"] = path if path else ''
            getdata = requests.post(f"{self.url}/object/list/{self.bucket_id}", json=body,
                                    headers=headers)
            getdata.raise_for_status()
        except HTTPError as http_err:
            print(f'HTTP error occurred: {http_err}')  # Python 3.6
        except Exception as err:
            raise err  # Python 3.6
        else:
            return getdata.json()
        #

    def _getFinalPath(self, path: str):
        return f"{self.bucket_id}/{path}"
