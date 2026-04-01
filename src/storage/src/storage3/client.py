from __future__ import annotations

import platform
from types import TracebackType
from typing import Generic

from pydantic import TypeAdapter
from supabase_utils.http.headers import Headers
from supabase_utils.http.io import (
    AsyncHttpIO,
    AsyncHttpSession,
    HttpIO,
    HttpMethod,
    HttpSession,
    SyncHttpIO,
    handle_http_io,
)
from supabase_utils.http.request import EmptyRequest, JSONRequest
from yarl import URL

from .analytics import StorageAnalyticsClient
from .exceptions import validate_adapter, validate_model
from .file_api import StorageFileApiClient
from .types import Bucket, BucketName, CreateOrUpdateBucketBody, MessageResponse
from .vectors import StorageVectorsClient
from .version import __version__

DEFAULT_TIMEOUT = 20

__all__ = [
    "StorageClient",
]

ListBucketAdapter = TypeAdapter(list[Bucket])


class StorageClient(Generic[HttpIO]):
    """Manage storage buckets and files."""

    def __init__(
        self,
        url: str,
        executor: HttpIO,
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

        self.executor: HttpIO = executor
        if url and url[-1] != "/":
            print("Storage endpoint URL should have a trailing slash.")
            url += "/"
        self.base_url = URL(url)
        self.default_headers = Headers.from_mapping(headers)

    def from_(self, id: str) -> StorageFileApiClient[HttpIO]:
        """Run a storage file operation.

        Parameters
        ----------
        id
            The unique identifier of the bucket
        """
        return StorageFileApiClient(
            id, self.base_url, self.executor, self.default_headers
        )

    def vectors(self) -> StorageVectorsClient[HttpIO]:
        return StorageVectorsClient(
            base_url=self.base_url.joinpath("vector"),
            default_headers=self.default_headers,
            executor=self.executor,
        )

    def analytics(self) -> StorageAnalyticsClient[HttpIO]:
        return StorageAnalyticsClient(
            default_headers=self.default_headers,
            base_url=self.base_url.joinpath("iceberg"),
            executor=self.executor,
        )

    @handle_http_io
    def list_buckets(self) -> HttpMethod[list[Bucket]]:
        """Retrieves the details of all storage buckets within an existing product."""
        # if the request doesn't error, it is assured to return a list
        response = yield EmptyRequest(
            method="GET",
            path=["bucket"],
        )
        return validate_adapter(response, ListBucketAdapter)

    @handle_http_io
    def get_bucket(self, id: str) -> HttpMethod[Bucket]:
        """Retrieves the details of an existing storage bucket.

        Parameters
        ----------
        id
            The unique identifier of the bucket you would like to retrieve.
        """
        response = yield EmptyRequest(
            method="GET",
            path=["bucket", id],
        )
        return validate_model(response, Bucket)

    @handle_http_io
    def create_bucket(
        self,
        id: str,
        name: str | None = None,
        public: bool | None = None,
        file_size_limit: int | None = None,
        allowed_mime_types: list[str] | None = None,
    ) -> HttpMethod[BucketName]:
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
        response = yield JSONRequest(
            method="POST",
            path=["bucket"],
            body=body,
            exclude_none=True,
        )

        return validate_model(response, BucketName)

    @handle_http_io
    def update_bucket(
        self,
        id: str,
        public: bool | None = None,
        file_size_limit: int | None = None,
        allowed_mime_types: list[str] | None = None,
    ) -> HttpMethod[MessageResponse]:
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
        response = yield JSONRequest(
            method="PUT",
            path=["bucket", id],
            body=body,
            exclude_none=True,
        )
        return validate_model(response, MessageResponse)

    @handle_http_io
    def empty_bucket(self, id: str) -> HttpMethod[MessageResponse]:
        """Removes all objects inside a single bucket.

        Parameters
        ----------
        id
            The unique identifier of the bucket you would like to empty.
        """
        response = yield EmptyRequest(
            method="POST",
            path=["bucket", id, "empty"],
        )

        return validate_model(response, MessageResponse)

    @handle_http_io
    def delete_bucket(self, id: str) -> HttpMethod[MessageResponse]:
        """Deletes an existing bucket. Note that you cannot delete buckets with existing objects inside. You must first
        `empty()` the bucket.

        Parameters
        ----------
        id
            The unique identifier of the bucket you would like to delete.
        """
        response = yield EmptyRequest(
            method="DELETE",
            path=["bucket", id],
        )
        return validate_model(response, MessageResponse)


class AsyncStorageClient(StorageClient[AsyncHttpIO]):
    def __init__(
        self,
        url: str,
        headers: dict[str, str],
        http_session: AsyncHttpSession,
        timeout: int | None = None,
    ) -> None:
        StorageClient.__init__(
            self,
            url=url,
            headers=headers,
            executor=AsyncHttpIO(session=http_session),
        )

    async def __aenter__(self) -> AsyncStorageClient:
        await self.executor.session.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[Exception] | None,
        exc: Exception | None,
        tb: TracebackType | None,
    ) -> None:
        await self.executor.session.__aexit__(exc_type, exc, tb)


class SyncStorageClient(StorageClient[SyncHttpIO]):
    def __init__(
        self,
        url: str,
        headers: dict[str, str],
        http_session: HttpSession,
        timeout: int | None = None,
    ) -> None:
        StorageClient.__init__(
            self,
            url=url,
            headers=headers,
            executor=SyncHttpIO(session=http_session),
        )

    def __enter__(self) -> SyncStorageClient:
        self.executor.session.__enter__()
        return self

    def __exit__(
        self,
        exc_type: type[Exception] | None,
        exc: Exception | None,
        tb: TracebackType | None,
    ) -> None:
        self.executor.session.__exit__(exc_type, exc, tb)
