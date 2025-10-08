from __future__ import annotations

from typing import Any, Optional

from httpx import AsyncClient, Headers, HTTPStatusError, Response
from yarl import URL

from ..exceptions import StorageApiError
from ..types import CreateOrUpdateBucketOptions, RequestMethod
from .file_api import AsyncBucket

__all__ = ["AsyncStorageBucketAPI"]


class AsyncStorageBucketAPI:
    """This class abstracts access to the endpoint to the Get, List, Empty, and Delete operations on a bucket"""

    def __init__(self, session: AsyncClient, url: str, headers: Headers) -> None:
        if url and url[-1] != "/":
            print("Storage endpoint URL should have a trailing slash.")
            url += "/"
        self._base_url = URL(url)
        self._client = session
        self._headers = headers

    async def _request(
        self,
        method: RequestMethod,
        path: list[str],
        json: Optional[dict[Any, Any]] = None,
    ) -> Response:
        try:
            url_path = self._base_url.joinpath(*path)
            response = await self._client.request(
                method, str(url_path), json=json, headers=self._headers
            )
            response.raise_for_status()
        except HTTPStatusError as exc:
            resp = exc.response.json()
            raise StorageApiError(resp["message"], resp["error"], resp["statusCode"])

        return response

    async def list_buckets(self) -> list[AsyncBucket]:
        """Retrieves the details of all storage buckets within an existing product."""
        # if the request doesn't error, it is assured to return a list
        res = await self._request("GET", ["bucket"])
        return [AsyncBucket(**bucket) for bucket in res.json()]

    async def get_bucket(self, id: str) -> AsyncBucket:
        """Retrieves the details of an existing storage bucket.

        Parameters
        ----------
        id
            The unique identifier of the bucket you would like to retrieve.
        """
        res = await self._request("GET", ["bucket", id])
        json = res.json()
        return AsyncBucket(**json)

    async def create_bucket(
        self,
        id: str,
        name: Optional[str] = None,
        options: Optional[CreateOrUpdateBucketOptions] = None,
    ) -> dict[str, str]:
        """Creates a new storage bucket.

        Parameters
        ----------
        id
            A unique identifier for the bucket you are creating.
        name
            A name for the bucket you are creating. If not passed, the id is used as the name as well.
        options
            Extra options to send while creating the bucket. Valid options are `public`, `file_size_limit` and
            `allowed_mime_types`.
        """
        json: dict[str, Any] = {"id": id, "name": name or id}
        if options:
            json.update(**options)
        res = await self._request(
            "POST",
            ["bucket"],
            json=json,
        )
        return res.json()

    async def update_bucket(
        self, id: str, options: CreateOrUpdateBucketOptions
    ) -> dict[str, str]:
        """Update a storage bucket.

        Parameters
        ----------
        id
            The unique identifier of the bucket you would like to update.
        options
            The properties you want to update. Valid options are `public`, `file_size_limit` and
            `allowed_mime_types`.
        """
        json = {"id": id, "name": id, **options}
        res = await self._request("PUT", ["bucket", id], json=json)
        return res.json()

    async def empty_bucket(self, id: str) -> dict[str, str]:
        """Removes all objects inside a single bucket.

        Parameters
        ----------
        id
            The unique identifier of the bucket you would like to empty.
        """
        res = await self._request("POST", ["bucket", id, "empty"], json={})
        return res.json()

    async def delete_bucket(self, id: str) -> dict[str, str]:
        """Deletes an existing bucket. Note that you cannot delete buckets with existing objects inside. You must first
        `empty()` the bucket.

        Parameters
        ----------
        id
            The unique identifier of the bucket you would like to delete.
        """
        res = await self._request("DELETE", ["bucket", id], json={})
        return res.json()
