from __future__ import annotations

import warnings
from typing import TYPE_CHECKING, Self

from pydantic import TypeAdapter
from supabase_utils.http.headers import Headers
from supabase_utils.http.io import (
    AsyncHttpIO,
    AsyncHttpSession,
    HttpMethod,
    HttpSession,
    SyncHttpIO,
    handle_http_io,
)
from supabase_utils.http.query import URLQuery
from supabase_utils.http.request import EmptyRequest, JSONRequest
from yarl import URL

from .analytics import StorageAnalyticsClient
from .exceptions import _validate_adapter, _validate_model, parse_api_error
from .file_api import StorageFileApiClient
from .types import (
    Bucket,
    BucketName,
    CreateOrUpdateBucketBody,
    LifecycleRule,
    MessageResponse,
    SortColumn,
    SortOrder,
    _LifecycleConfiguration,
)
from .vectors import StorageVectorsClient
from .version import __version__

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from types import TracebackType

    from supabase_utils.http.retry import RetryPolicy

__all__ = [
    "StorageClient",
]

ListBucketAdapter = TypeAdapter(list[Bucket])


class StorageClient[HttpIO: (SyncHttpIO, AsyncHttpIO)]:
    """Manage storage buckets and files."""

    def __init__(
        self,
        url: str,
        executor: HttpIO,
        headers: Mapping[str, str],
    ) -> None:
        supabase_headers = Headers.supabase_client_headers("storage3", __version__)
        user_headers = Headers.from_mapping(headers)
        self.executor: HttpIO = executor
        if url and url[-1] != "/":
            warnings.warn(
                "Storage endpoint URL should have a trailing slash.", stacklevel=3
            )
            url += "/"
        self.base_url = URL(url)
        self.default_headers = supabase_headers.update(user_headers)

    def from_(self, id: str) -> StorageFileApiClient[HttpIO]:
        """Run a storage file operation.

        Parameters
        ----------
        id
            The unique identifier of the bucket
        """
        return StorageFileApiClient(id, self.base_url, self.executor, self)

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
    def list_buckets(
        self,
        *,
        limit: int | None = None,
        offset: int | None = None,
        search: str | None = None,
        sort_column: SortColumn | None = None,
        sort_order: SortOrder | None = None,
    ) -> HttpMethod[list[Bucket]]:
        """Retrieves the details of the storage buckets.

        Without arguments, every bucket is returned. The arguments need
        Supabase Storage v1.25.0 or newer; older releases ignore them.

        Parameters
        ----------
        limit
            The maximum number of buckets to return.
        offset
            The number of buckets to skip.
        search
            Only returns the buckets whose name contains this text, ignoring case.
        sort_column
            The column to sort the buckets by.
        sort_order
            The direction to sort the buckets in.
        """
        params = {
            "limit": limit,
            "offset": offset,
            "search": search,
            "sortColumn": sort_column,
            "sortOrder": sort_order,
        }
        response = yield EmptyRequest(
            method="GET",
            path=["bucket"],
            query=URLQuery.from_mapping(
                {key: value for key, value in params.items() if value is not None}
            ),
        )
        return _validate_adapter(response, ListBucketAdapter)

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
        return _validate_model(response, Bucket)

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

        return _validate_model(response, BucketName)

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
        return _validate_model(response, MessageResponse)

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

        return _validate_model(response, MessageResponse)

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
        return _validate_model(response, MessageResponse)

    @handle_http_io
    def get_bucket_lifecycle(self, id: str) -> HttpMethod[list[LifecycleRule]]:
        """Retrieves the rules of the lifecycle policy of a standard bucket.

        Returns an empty list when the bucket has no lifecycle policy. Raises
        :class:`StorageApiError` when lifecycle policies are not enabled on
        the storage service, the bucket is not a standard bucket, or the
        caller is not authorized.

        Parameters
        ----------
        id
            The unique identifier of the bucket.
        """
        response = yield EmptyRequest(
            method="GET",
            path=["bucket", id, "lifecycle"],
        )
        if response.is_success:
            return _LifecycleConfiguration.model_validate_json(response.content).rules
        error = parse_api_error(response)
        if error.code == "NoSuchLifecycleConfiguration":
            return []
        raise error

    @handle_http_io
    def update_bucket_lifecycle(
        self, id: str, rules: Sequence[LifecycleRule]
    ) -> HttpMethod[list[LifecycleRule]]:
        """Replaces the lifecycle policy of a standard bucket with `rules`.

        The rules replace the whole stored policy. Use
        `delete_bucket_lifecycle` to remove the policy instead.

        Parameters
        ----------
        id
            The unique identifier of the bucket.
        rules
            The rules of the policy. Storage accepts between 1 and 1000 rules.

        Returns
        -------
        The stored rules, with the identifiers Storage generated for the
        rules that had none.
        """
        response = yield JSONRequest(
            method="PUT",
            path=["bucket", id, "lifecycle"],
            body=_LifecycleConfiguration(rules=list(rules)),
            exclude_none=True,
        )
        return _validate_model(response, _LifecycleConfiguration).rules

    @handle_http_io
    def delete_bucket_lifecycle(self, id: str) -> HttpMethod[MessageResponse]:
        """Removes the lifecycle policy of a standard bucket. Succeeds when the
        bucket has no policy.

        Parameters
        ----------
        id
            The unique identifier of the bucket.
        """
        response = yield EmptyRequest(
            method="DELETE",
            path=["bucket", id, "lifecycle"],
        )
        return _validate_model(response, MessageResponse)


class AsyncStorageClient(StorageClient[AsyncHttpIO]):
    def __init__(
        self,
        url: str,
        headers: Mapping[str, str],
        http_session: AsyncHttpSession,
        *,
        request_timeout: float | None = None,
        retry: RetryPolicy | None = None,
    ) -> None:
        """Create a storage client.

        Parameters
        ----------
        url
            The URL of the storage service, ending with a slash.
        headers
            Headers sent with every request.
        http_session
            The HTTP session that sends the requests.
        request_timeout
            Seconds a request may go without progress before it fails with
            `RequestTimeoutError`. None leaves the timeout to the HTTP client.
        retry
            How requests that failed in a way worth repeating are retried.
            None uses the default `RetryPolicy`, which retries GET and HEAD
            requests only, so an upload is not retried unless the policy
            lists its method.
        """
        super().__init__(
            url=url,
            headers=headers,
            executor=AsyncHttpIO(
                session=http_session, request_timeout=request_timeout, retry=retry
            ),
        )

    async def __aenter__(self) -> Self:
        await self.executor.session.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.executor.session.__aexit__(exc_type, exc, tb)


class SyncStorageClient(StorageClient[SyncHttpIO]):
    def __init__(
        self,
        url: str,
        headers: Mapping[str, str],
        http_session: HttpSession,
        *,
        request_timeout: float | None = None,
        retry: RetryPolicy | None = None,
    ) -> None:
        """Create a storage client.

        Parameters
        ----------
        url
            The URL of the storage service, ending with a slash.
        headers
            Headers sent with every request.
        http_session
            The HTTP session that sends the requests.
        request_timeout
            Seconds a request may go without progress before it fails with
            `RequestTimeoutError`. None leaves the timeout to the HTTP client.
        retry
            How requests that failed in a way worth repeating are retried.
            None uses the default `RetryPolicy`, which retries GET and HEAD
            requests only, so an upload is not retried unless the policy
            lists its method.
        """
        super().__init__(
            url=url,
            headers=headers,
            executor=SyncHttpIO(
                session=http_session, request_timeout=request_timeout, retry=retry
            ),
        )

    def __enter__(self) -> Self:
        self.executor.session.__enter__()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.executor.session.__exit__(exc_type, exc, tb)
