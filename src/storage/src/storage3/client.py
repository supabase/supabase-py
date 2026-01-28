from __future__ import annotations

from typing import Generic, Optional
from warnings import warn

from httpx import Headers
from pydantic import TypeAdapter
from supabase_utils.http import (
    EndpointRequest,
    Executor,
    ServerEndpoint,
    http_endpoint,
    validate_adapter,
    validate_model,
)
from yarl import URL

from storage3.constants import DEFAULT_TIMEOUT

from .analytics import AsyncStorageAnalyticsClient
from .exceptions import parse_api_error
from .file_api import Bucket, BucketProxy
from .request import AsyncRequestBuilder
from .types import CreateOrUpdateBucketBody, MessageResponse, StorageEndpoint
from .vectors import AsyncStorageVectorsClient
from .version import __version__


class StorageClient(Generic[Executor]):
    """Manage storage buckets and files."""

    def __init__(
        self,
        url: str,
        executor: Executor,
        headers: dict[str, str],
        timeout: Optional[int] = None,
        verify: Optional[bool] = None,
        proxy: Optional[str] = None,
    ) -> None:
        headers = {
            "User-Agent": f"supabase-py/storage3 v{__version__}",
            **headers,
        }

        if timeout is not None:
            warn(
                "The 'timeout' parameter is deprecated. Please configure it in the http client instead.",
                DeprecationWarning,
                stacklevel=2,
            )
        if verify is not None:
            warn(
                "The 'verify' parameter is deprecated. Please configure it in the http client instead.",
                DeprecationWarning,
                stacklevel=2,
            )
        if proxy is not None:
            warn(
                "The 'proxy' parameter is deprecated. Please configure it in the http client instead.",
                DeprecationWarning,
                stacklevel=2,
            )

        self.verify = bool(verify) if verify is not None else True
        self.timeout = int(abs(timeout)) if timeout is not None else DEFAULT_TIMEOUT

        self.executor: Executor = executor
        if url and url[-1] != "/":
            print("Storage endpoint URL should have a trailing slash.")
            url += "/"
        self._base_url = URL(url)
        self._headers = Headers(headers)

    def from_(self, id: str) -> BucketProxy[Executor]:
        """Run a storage file operation.

        Parameters
        ----------
        id
            The unique identifier of the bucket
        """
        return BucketProxy(id, self._base_url, self.executor, self._headers)

    def vectors(self) -> AsyncStorageVectorsClient:
        return AsyncStorageVectorsClient(
            url=self._base_url.joinpath("vector"),
            headers=self._headers,
        )

    def analytics(self) -> AsyncStorageAnalyticsClient:
        request = AsyncRequestBuilder(
            headers=self._headers,
            base_url=self._base_url.joinpath("iceberg"),
        )
        return AsyncStorageAnalyticsClient(request=request)

    @http_endpoint
    def list_buckets(self) -> StorageEndpoint[list[Bucket]]:
        """Retrieves the details of all storage buckets within an existing product."""
        # if the request doesn't error, it is assured to return a list
        request = EndpointRequest(
            method="GET",
            path=["bucket"],
            headers=self._headers,
        )
        return ServerEndpoint(
            request=request,
            on_success=validate_adapter(TypeAdapter(list[Bucket])),
            on_failure=parse_api_error
        )

    @http_endpoint
    def get_bucket(self, id: str) -> StorageEndpoint[Bucket]:
        """Retrieves the details of an existing storage bucket.

        Parameters
        ----------
        id
            The unique identifier of the bucket you would like to retrieve.
        """
        request = EndpointRequest(
            method="GET",
            path=["bucket", id],
            headers=self._headers,
        )
        return ServerEndpoint(
            request=request,
            on_success=validate_model(Bucket),
            on_failure=parse_api_error
        )

    @http_endpoint
    def create_bucket(
        self,
        id: str,
        name: Optional[str] = None,
        public: Optional[bool] = None,
        file_size_limit: Optional[int] = None,
        allowed_mime_types: Optional[list[str]] = None,
    ) -> StorageEndpoint[Bucket]:
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
        body = CreateOrUpdateBucketBody(
            id=id,
            name=name or id,
            public=public,
            file_size_limit=file_size_limit,
            allowed_mime_types=allowed_mime_types
        )
        request = EndpointRequest(
            method="POST",
            path=["bucket"],
            headers=self._headers,
        ).model(body)
        return ServerEndpoint(
            request=request,
            on_success=validate_model(Bucket),
            on_failure=parse_api_error
        )

    @http_endpoint
    def update_bucket(
        self, id: str,
        public: Optional[bool] = None,
        file_size_limit: Optional[int] = None,
        allowed_mime_types: Optional[list[str]] = None,
    ) -> StorageEndpoint[MessageResponse]:
        """Update a storage bucket.

        Parameters
        ----------
        id
            The unique identifier of the bucket you would like to update.
        options
            The properties you want to update. Valid options are `public`, `file_size_limit` and
            `allowed_mime_types`.
        """
        body = CreateOrUpdateBucketBody(
            id=id,
            name=id,
            public=public,
            file_size_limit=file_size_limit,
            allowed_mime_types=allowed_mime_types
        )
        request = EndpointRequest(
            method="PUT",
            path=["bucket", id],
            headers=self._headers,
        ).model(body)
        return ServerEndpoint(
            request=request,
            on_success=validate_model(MessageResponse),
            on_failure=parse_api_error,
        )

    @http_endpoint
    def empty_bucket(self, id: str) -> StorageEndpoint[MessageResponse]:
        """Removes all objects inside a single bucket.

        Parameters
        ----------
        id
            The unique identifier of the bucket you would like to empty.
        """
        request = EndpointRequest(
            method="POST",
            path=["bucket", id, "empty"],
            headers=self._headers,
        )
        return ServerEndpoint(
            request=request,
            on_success=validate_model(MessageResponse),
            on_failure=parse_api_error,
        )
    
    @http_endpoint
    def delete_bucket(self, id: str) -> StorageEndpoint[MessageResponse]:
        """Deletes an existing bucket. Note that you cannot delete buckets with existing objects inside. You must first
        `empty()` the bucket.

        Parameters
        ----------
        id
            The unique identifier of the bucket you would like to delete.
        """
        request = EndpointRequest(
            method="DELETE",
            path=["bucket", id],
            headers=self._headers,
        )
        return ServerEndpoint(
            request=request,
            on_success=validate_model(MessageResponse),
            on_failure=parse_api_error,
        )
