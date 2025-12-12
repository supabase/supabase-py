from __future__ import annotations

from typing import Optional
from warnings import warn

from httpx import Client, Headers

from storage3.constants import DEFAULT_TIMEOUT

from ..version import __version__
from .analytics import SyncStorageAnalyticsClient
from .bucket import SyncStorageBucketAPI
from .file_api import SyncBucketProxy
from .request import SyncRequestBuilder
from .vectors import SyncStorageVectorsClient

__all__ = [
    "SyncStorageClient",
]


class SyncStorageClient(SyncStorageBucketAPI):
    """Manage storage buckets and files."""

    def __init__(
        self,
        url: str,
        headers: dict[str, str],
        timeout: Optional[int] = None,
        verify: Optional[bool] = None,
        proxy: Optional[str] = None,
        http_client: Optional[Client] = None,
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

        self.session = http_client or Client(
            headers=headers,
            timeout=self.timeout,
            proxy=proxy,
            verify=self.verify,
            follow_redirects=True,
            http2=True,
        )
        super().__init__(self.session, url, Headers(headers))

    def __enter__(self) -> SyncStorageClient:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.session.close()

    def from_(self, id: str) -> SyncBucketProxy:
        """Run a storage file operation.

        Parameters
        ----------
        id
            The unique identifier of the bucket
        """
        return SyncBucketProxy(id, self._base_url, self._headers, self._client)

    def vectors(self) -> SyncStorageVectorsClient:
        return SyncStorageVectorsClient(
            url=self._base_url.joinpath("vector"),
            headers=self._headers,
            session=self.session,
        )

    def analytics(self) -> SyncStorageAnalyticsClient:
        request = SyncRequestBuilder(
            session=self.session,
            headers=self._headers,
            base_url=self._base_url.joinpath("iceberg"),
        )
        return SyncStorageAnalyticsClient(request=request)
