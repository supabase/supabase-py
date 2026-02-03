from __future__ import annotations

import platform
from types import TracebackType
from typing import Generic, Optional

from httpx import AsyncClient, Client, Headers
from pydantic import TypeAdapter
from supabase_utils.http import (
    AsyncExecutor,
    EmptyRequest,
    Executor,
    JSONRequest,
    ResponseCases,
    ResponseHandler,
    SyncExecutor,
    handle_http_response,
    validate_adapter,
    validate_model,
)
from yarl import URL

from .analytics import StorageAnalyticsClient
from .exceptions import parse_api_error
from .file_api import StorageFileApiClient
from .types import Bucket, BucketName, CreateOrUpdateBucketBody, MessageResponse
from .vectors import StorageVectorsClient
from .version import __version__

DEFAULT_TIMEOUT = 20

__all__ = [
    "StorageClient",
]


class StorageClient(Generic[Executor]):
    """Manage storage buckets and files."""

    def __init__(
        self,
        url: str,
        executor: Executor,
        headers: dict[str, str],
    ) -> None:
        headers = {
            "X-Client-Info": f"supabase-py/storage3 v{__version__}",
            "X-Supabase-Client-Platform": platform.system(),
            "X-Supabase-Client-Platform-Version": platform.release(),
            "X-Supabase-Client-Runtime": "python",
            "X-Supabase-Client-Runtime-Version": platform.python_version(),
            **headers,
        }

        self.executor: Executor = executor
        if url and url[-1] != "/":
            print("Storage endpoint URL should have a trailing slash.")
            url += "/"
        self.base_url = URL(url)
        self._headers = Headers(headers)

    def from_(self, id: str) -> StorageFileApiClient[Executor]:
        """Run a storage file operation.

        Parameters
        ----------
        id
            The unique identifier of the bucket
        """
        return StorageFileApiClient(id, self.base_url, self.executor, self._headers)

    def vectors(self) -> StorageVectorsClient[Executor]:
        return StorageVectorsClient(
            base_url=self.base_url.joinpath("vector"),
            _headers=self._headers,
            executor=self.executor,
        )

    def analytics(self) -> StorageAnalyticsClient[Executor]:
        return StorageAnalyticsClient(
            _headers=self._headers,
            base_url=self.base_url.joinpath("iceberg"),
            executor=self.executor,
        )

    @handle_http_response
    def list_buckets(self) -> ResponseHandler[list[Bucket]]:
        """Retrieves the details of all storage buckets within an existing product."""
        # if the request doesn't error, it is assured to return a list
        request = EmptyRequest(
            method="GET",
            path=["bucket"],
            headers=self._headers,
        )
        return ResponseCases(
            request=request,
            on_success=validate_adapter(TypeAdapter(list[Bucket])),
            on_failure=parse_api_error,
        )

    @handle_http_response
    def get_bucket(self, id: str) -> ResponseHandler[Bucket]:
        """Retrieves the details of an existing storage bucket.

        Parameters
        ----------
        id
            The unique identifier of the bucket you would like to retrieve.
        """
        request = EmptyRequest(
            method="GET",
            path=["bucket", id],
            headers=self._headers,
        )
        return ResponseCases(
            request=request,
            on_success=validate_model(Bucket),
            on_failure=parse_api_error,
        )

    @handle_http_response
    def create_bucket(
        self,
        id: str,
        name: Optional[str] = None,
        public: Optional[bool] = None,
        file_size_limit: Optional[int] = None,
        allowed_mime_types: Optional[list[str]] = None,
    ) -> ResponseHandler[BucketName]:
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
            allowed_mime_types=allowed_mime_types,
        )
        request = JSONRequest(
            method="POST",
            path=["bucket"],
            headers=self._headers,
            body=body,
            exclude_none=True,
        )

        return ResponseCases(
            request=request,
            on_success=validate_model(BucketName),
            on_failure=parse_api_error,
        )

    @handle_http_response
    def update_bucket(
        self,
        id: str,
        public: Optional[bool] = None,
        file_size_limit: Optional[int] = None,
        allowed_mime_types: Optional[list[str]] = None,
    ) -> ResponseHandler[MessageResponse]:
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
            allowed_mime_types=allowed_mime_types,
        )
        request = JSONRequest(
            method="PUT",
            path=["bucket", id],
            headers=self._headers,
            body=body,
            exclude_none=True,
        )
        return ResponseCases(
            request=request,
            on_success=validate_model(MessageResponse),
            on_failure=parse_api_error,
        )

    @handle_http_response
    def empty_bucket(self, id: str) -> ResponseHandler[MessageResponse]:
        """Removes all objects inside a single bucket.

        Parameters
        ----------
        id
            The unique identifier of the bucket you would like to empty.
        """
        request = EmptyRequest(
            method="POST",
            path=["bucket", id, "empty"],
            headers=self._headers,
        )

        return ResponseCases(
            request=request,
            on_success=validate_model(MessageResponse),
            on_failure=parse_api_error,
        )

    @handle_http_response
    def delete_bucket(self, id: str) -> ResponseHandler[MessageResponse]:
        """Deletes an existing bucket. Note that you cannot delete buckets with existing objects inside. You must first
        `empty()` the bucket.

        Parameters
        ----------
        id
            The unique identifier of the bucket you would like to delete.
        """
        request = EmptyRequest(
            method="DELETE",
            path=["bucket", id],
            headers=self._headers,
        )
        return ResponseCases(
            request=request,
            on_success=validate_model(MessageResponse),
            on_failure=parse_api_error,
        )


class AsyncStorageClient(StorageClient[AsyncExecutor]):
    def __init__(
        self,
        url: str,
        headers: dict[str, str],
        timeout: Optional[int] = None,
        http_client: Optional[AsyncClient] = None,
    ) -> None:
        client = http_client or AsyncClient(
            headers=headers,
            timeout=timeout or DEFAULT_TIMEOUT,
            http2=True,
            follow_redirects=True,
        )
        StorageClient.__init__(
            self, url=url, headers=headers, executor=AsyncExecutor(session=client)
        )

    async def __aenter__(self) -> AsyncStorageClient:
        return self

    async def __aexit__(
        self,
        exc_type: Optional[type[Exception]],
        exc: Optional[Exception],
        tb: Optional[TracebackType],
    ) -> None:
        await self.executor.session.aclose()


class SyncStorageClient(StorageClient[SyncExecutor]):
    def __init__(
        self,
        url: str,
        headers: dict[str, str],
        timeout: Optional[int] = None,
        http_client: Optional[Client] = None,
    ) -> None:
        client = http_client or Client(
            headers=headers,
            timeout=timeout or DEFAULT_TIMEOUT,
            http2=True,
            follow_redirects=True,
        )
        StorageClient.__init__(
            self, url=url, headers=headers, executor=SyncExecutor(session=client)
        )

    def __enter__(self) -> SyncStorageClient:
        return self

    def __exit__(
        self,
        exc_type: Optional[type[Exception]],
        exc: Optional[Exception],
        tb: Optional[TracebackType],
    ) -> None:
        self.executor.session.close()
