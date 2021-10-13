from __future__ import annotations

from collections.abc import Awaitable
from typing import Any, Literal, Optional, Union

from httpx import AsyncClient, Client

RequestMethod = Literal["GET", "POST", "PUT", "DELETE", "PATCH"]
# dict is returned when the request was synchronous, awaitable when async, None if there was an error
_SyncOrAsyncResponse = Union[dict[str, Any], Awaitable, None]


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
        self, method: RequestMethod, url: str, json: Optional[dict[Any, Any]] = None
    ) -> Union[dict[Any, Any], Awaitable, None]:
        if self._is_async:
            return self._async_request(method, url, json)
        else:
            return self._sync_request(method, url, json)

    def _sync_request(
        self, method: RequestMethod, url: str, json: Optional[dict[Any, Any]] = None
    ) -> Optional[dict[Any, Any]]:
        if isinstance(self._client, AsyncClient):  # only to appease the type checker
            return

        response = self._client.request(method, url, json=json)
        response.raise_for_status()
        return response.json()

    async def _async_request(
        self, method: RequestMethod, url: str, json: Optional[dict[Any, Any]] = None
    ) -> Optional[dict[Any, Any]]:
        if isinstance(self._client, Client):  # only to appease the type checker
            return

        response = await self._client.request(method, url, json=json)
        response.raise_for_status()
        return response.json()

    def list_buckets(self) -> _SyncOrAsyncResponse:
        """Retrieves the details of all storage buckets within an existing product."""
        return self._request("GET", f"{self.url}/bucket")

    def get_bucket(self, id: str) -> _SyncOrAsyncResponse:
        """Retrieves the details of an existing storage bucket.

        Parameters
        ----------
        id
            The unique identifier of the bucket you would like to retrieve.
        """
        return self._request("GET", f"{self.url}/bucket/{id}")

    def create_bucket(
        self, id: str, name: str, public: bool = False
    ) -> _SyncOrAsyncResponse:
        """Creates a new storage bucket.

        Parameters
        ----------
        id
            A unique identifier for the bucket you are creating.
        """
        return self._request(
            "POST",
            f"{self.url}/bucket",
            json={"id": id, "name": name, "public": public},
        )

    def empty_bucket(self, id: str) -> _SyncOrAsyncResponse:
        """Removes all objects inside a single bucket.

        Parameters
        ----------
        id
            The unique identifier of the bucket you would like to empty.
        """
        return self._request("POST", f"{self.url}/bucket/{id}/empty", json={})

    def delete_bucket(self, id: str) -> _SyncOrAsyncResponse:
        """Deletes an existing bucket. Note that you cannot delete buckets with existing objects inside. You must first
        `empty()` the bucket.

        Parameters
        ----------
        id
            The unique identifier of the bucket you would like to delete.
        """
        return self._request("DELETE", f"{self.url}/bucket/{id}", json={})
