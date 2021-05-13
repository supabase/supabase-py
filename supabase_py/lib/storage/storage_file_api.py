import asyncio
import json
from typing import Optional, AsyncGenerator, Union, Any, Dict

import aiohttp
import requests
from requests import HTTPError

from supabase_py.lib.storage.request_error import RequestError

DEFAULT_CHUNK_SIZE = 100 * 1024 * 1024


class StorageFileApi:
    """A class used to manage storage ."""

    DEFAULT_SEARCH_OPTIONS = {
        "offset": 0,
        "sortBy": {
            "column": "name",
            "order": "asc",
        },
    }

    # TODO : Figure out what this dictionary is supposed to contain
    DEFAULT_FILE_OPTIONS = {
        # "Content-Type": f"multipart/form-data;boundary=---------------------------293582696224464"
    }

    def __init__(self, url: str, headers: dict, bucket_id: str, replace: str):
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
        self.replace = replace

    async def _upload_request(self, session, file, path):
        _path = self._getFinalPath(path)
        async with session.post(f"{self.url}/object/{_path}", data=file) as response:
            if not response.ok:
                try:
                    resp = await response.json()
                except BaseException:
                    resp = json.loads(response.content._buffer[0])
                    # TODO: Fix the error described below
                    # this should not be done but it returns only client.Disconnect so no error out
                    if resp["statusCode"] == "23505" and self.replace:
                        return await self._update_request(session, file, path)
                raise RequestError(resp["statusCode"], resp["error"], resp["message"])
            risp = await response.text()
            return risp

    async def _upload_session(self, session, file, param_gen, content_type, path):
        with aiohttp.MultipartWriter("form-data") as mpwriter:
            cont = mpwriter.append(file(*param_gen))
            cont.set_content_disposition("form-data", filename=f"{path}")
        return await self._upload_request(session, mpwriter, path)

    async def upload(self, path: str, file: any, file_options: dict = None, stream=False, **kwargs):
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
        stream
            set to true if you want to use a generator for the uploado of the file
        **kwargs
            param_gen the parameters to call the generator function
            content_type of the file
            session if you need to make multiple request with an async code view example for more information
        """
        if file_options is None:
            file_options = {}
        headers = dict(self.headers, **file_options)
        headers.update(self.DEFAULT_FILE_OPTIONS)
        if kwargs.get("session") and stream:
            return await self._upload_session(
                kwargs["session"], file, kwargs["param_gen"], kwargs["content_type"], path
            )
        else:
            async with aiohttp.ClientSession(headers=headers) as session:
                if stream:
                    with aiohttp.MultipartWriter(kwargs["content_type"]) as mpwriter:
                        cont = mpwriter.append(file(kwargs["param_gen"]))
                        cont.set_content_disposition(kwargs["content_type"], filename=f"{path}")
                    return await self._upload_request(session, mpwriter, path)
                else:
                    files = {"file": open(file, "rb")}  #
                    return await self._upload_request(session, files, path)

    async def _update_request(self, session, file, path):
        _path = self._getFinalPath(path)
        async with session.put(f"{self.url}/object/{_path}", data=file) as response:
            # TODO: Put this in another function
            if not response.ok:
                try:
                    resp = await response.json()
                except BaseException:
                    resp = json.loads(
                        response.content._buffer[0]
                    )  # this should not be done but it returns only client.Disconnect so no error out
                raise RequestError(resp["statusCode"], resp["error"], resp["message"])
            risp = await response.text()
            return risp

    async def update(self, path: str, file: any, file_options: Optional[Dict[str, Any]] = None, stream=False, **kwargs):
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
        headers.update(self.DEFAULT_FILE_OPTIONS)
        if kwargs["session"] and stream:
            return await self._upload_session(
                kwargs["session"], file, kwargs["param_gen"], kwargs["content_type"], path
            )
        else:
            async with aiohttp.ClientSession(headers=headers) as session:
                if stream:
                    with aiohttp.MultipartWriter(kwargs["content_type"]) as mpwriter:
                        cont = mpwriter.append(file(kwargs["param_gen"]))
                        cont.set_content_disposition(kwargs["content_type"], filename=f"{path}")
                    return await self._update_request(session, mpwriter, path)
                else:
                    files = {"file": open(file, "rb")}  #
                    return await self._update_request(session, files, path)

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
            response = requests.post(
                f"{self.url}/object/move",
                data={"bucketId": self.bucket_id, "sourceKey": from_path, "destinationKey": to_path},
                headers=self.headers,
            )
            # If the response was successful, no Exception will be raised
            response.raise_for_status()
        except HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")  # Python 3.6
        except Exception as err:
            print(f"Other error occurred: {err}")  # Python 3.6
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
            response = requests.post(
                f"{self.url}/object/sign/{_path}", json={"expiresIn": str(expires_in)}, headers=self.headers
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

    # TODO:FIXARE docsting

    async def download(
        self, path: str, generator=False, session=None, chunk_size=DEFAULT_CHUNK_SIZE
    ) -> Union[AsyncGenerator, bytes, None]:
        """
        Downloads a file.
        ----------
        path
            The original file path, including the current file name. For example `folder/image.png`.
        generator
            If generator=True it returns an asynchronousgenerator and for every call to this function it returns a chunk of data
        chunk_size
            How mutch the generator should read
        Parameters
        Returns
        -------
        bytes
            The bytes of the files
        """
        _path = self._getFinalPath(path)

        if generator:
            return self._download_generator(_path, chunk_size)
        if session is None:
            session = aiohttp.ClientSession(headers=self.headers)
        async with session.get(f"{self.url}/object/{_path}") as resp:
            resp.raise_for_status()
            if resp.status == 200:
                return await resp.read()  # this is not good for big files it should be a generator.

        return None

    async def _download_generator(self, _path: str, chunk_size=DEFAULT_CHUNK_SIZE):
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
            async with session.get(f"{self.url}/object/{_path}") as resp:
                #
                if not resp.ok:
                    try:
                        resps = await resp.json()
                    except:
                        resps = json.loads(resp.content._buffer[0])
                    raise RequestError(resps["statusCode"], resps["error"], resps["message"])
                else:
                    yield resp.content.size
                    while True:
                        chunk = await resp.content.read(chunk_size)
                        yield chunk
                        if not chunk:
                            break

    def remove(self, paths: list):
        """
        Deletes files within the same bucket

        Parameters
        ----------
        paths
            An array or list of files to be deletes, including the path and file name. For example [`folder/image.png`].
        """
        try:
            response = requests.delete(
                f"{self.url}/object/{self.bucket_id}", data={"prefixes": paths}, headers=self.headers
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
            getdata = requests.post(f"{self.url}/object/list/{self.bucket_id}", json=body, headers=headers)
            getdata.raise_for_status()
        except HTTPError as http_err:
            print(f"HTTP error occurred: {http_err}")  # Python 3.6
        except Exception as err:
            raise err  # Python 3.6
        else:
            return getdata.json()

    def _getFinalPath(self, path: str):
        return f"{self.bucket_id}/{path}"
