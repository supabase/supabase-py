from __future__ import annotations

from collections.abc import Awaitable
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, Union

from httpx import AsyncClient, Client, HTTPError

__all__ = ["Bucket", "StorageBucketAPI"]

_RequestMethod = str


class StorageException(Exception):
    """Error raised when an operation on the storage API fails."""


@dataclass
class Bucket:
    id: str
    name: str
    owner: str
    public: bool
    created_at: datetime
    updated_at: datetime

    def __post_init__(self) -> None:
        # created_at and updated_at are returned by the API as ISO timestamps
        # so we convert them to datetime objects
        self.created_at = datetime.fromisoformat(self.created_at)  # type: ignore
        self.updated_at = datetime.fromisoformat(self.updated_at)  # type: ignore


ResponseType = Union[
    Dict[
        str, str
    ],  # response from an endpoint without a custom response_class, example: create_bucket
    List[
        Bucket
    ],  # response from an endpoint which returns a list of objects, example: list_buckets
    Bucket,  # response from an endpoint which returns a single object, example: get_bucket
    None,
]


class StorageBucketAPI:
    """This class abstracts access to the endpoint to the Get, List, Empty, and Delete operations on a bucket"""

    def __init__(
        self, url: str, headers: dict[str, str], is_async: bool = False
    ) -> None:
        self.url = url
        self.headers = headers

        self._is_async = is_async

        if is_async:
            self._client = AsyncClient(headers=self.headers)
        else:
            self._client = Client(headers=self.headers)

    def _request(
        self,
        method: _RequestMethod,
        url: str,
        json: Optional[dict[Any, Any]] = None,
        response_class: Optional[Type] = None,
    ) -> Any:
        if self._is_async:
            return self._async_request(method, url, json, response_class)
        else:
            return self._sync_request(method, url, json, response_class)

    def _sync_request(
        self,
        method: _RequestMethod,
        url: str,
        json: Optional[dict[Any, Any]] = None,
        response_class: Optional[Type] = None,
    ) -> ResponseType:
        if isinstance(self._client, AsyncClient):  # only to appease the type checker
            return None

        response = self._client.request(method, url, json=json)
        try:
            response.raise_for_status()
        except HTTPError:
            raise StorageException(response.json())

        response_data = response.json()

        if not response_class:
            return response_data

        if isinstance(response_data, list):
            return [response_class(**item) for item in response_data]
        else:
            return response_class(**response_data)

    async def _async_request(
        self,
        method: _RequestMethod,
        url: str,
        json: Optional[dict[Any, Any]] = None,
        response_class: Optional[Type] = None,
    ) -> ResponseType:
        if isinstance(self._client, Client):  # only to appease the type checker
            return

        response = await self._client.request(method, url, json=json)
        try:
            response.raise_for_status()
        except HTTPError:
            raise StorageException(response.json())

        response_data = response.json()

        if not response_class:
            return response_data

        if isinstance(response_data, list):
            return [response_class(**item) for item in response_data]
        else:
            return response_class(**response_data)

    def list_buckets(self) -> Union[list[Bucket], Awaitable[list[Bucket]], None]:
        """Retrieves the details of all storage buckets within an existing product."""
        return self._request("GET", f"{self.url}/bucket", response_class=Bucket)

    def get_bucket(self, id: str) -> Union[Bucket, Awaitable[Bucket], None]:
        """Retrieves the details of an existing storage bucket.

        Parameters
        ----------
        id
            The unique identifier of the bucket you would like to retrieve.
        """
        return self._request("GET", f"{self.url}/bucket/{id}", response_class=Bucket)

    def create_bucket(
        self, id: str, name: str = None, public: bool = False
    ) -> Union[dict[str, str], Awaitable[dict[str, str]]]:
        """Creates a new storage bucket.

        Parameters
        ----------
        id
            A unique identifier for the bucket you are creating.
        name
            A name for the bucket you are creating. If not passed, the id is used as the name as well.
        public
            Whether the bucket you are creating should be publicly accessible. Defaults to False.
        """
        return self._request(
            "POST",
            f"{self.url}/bucket",
            json={"id": id, "name": name or id, "public": public},
        )

    def empty_bucket(self, id: str) -> Union[dict[str, str], Awaitable[dict[str, str]]]:
        """Removes all objects inside a single bucket.

        Parameters
        ----------
        id
            The unique identifier of the bucket you would like to empty.
        """
        return self._request("POST", f"{self.url}/bucket/{id}/empty", json={})

    def delete_bucket(
        self, id: str
    ) -> Union[dict[str, str], Awaitable[dict[str, str]]]:
        """Deletes an existing bucket. Note that you cannot delete buckets with existing objects inside. You must first
        `empty()` the bucket.

        Parameters
        ----------
        id
            The unique identifier of the bucket you would like to delete.
        """
        return self._request("DELETE", f"{self.url}/bucket/{id}", json={})
