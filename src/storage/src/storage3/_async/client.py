from __future__ import annotations

import platform
import sys
from typing import Optional
from warnings import warn

from httpx import AsyncClient, Headers

from storage3.constants import DEFAULT_TIMEOUT

from ..version import __version__
from .analytics import AsyncStorageAnalyticsClient
from .bucket import AsyncStorageBucketAPI
from .file_api import AsyncBucketProxy
from .request import AsyncRequestBuilder
from .vectors import AsyncStorageVectorsClient

__all__ = [
    "AsyncStorageClient",
]


class AsyncStorageClient(AsyncStorageBucketAPI):
    """Manage storage buckets and files."""

    def __init__(
        self,
        url: str,
        headers: dict[str, str],
        timeout: Optional[int] = None,
        verify: Optional[bool] = None,
        proxy: Optional[str] = None,
        http_client: Optional[AsyncClient] = None,
    ) -> None:
        headers = {
            "X-Client-Info": f"supabase-py/storage3 v{__version__}",
            "X-Supabase-Client-Platform": platform.system(),
            "X-Supabase-Client-Platform-Version": platform.release(),
            "X-Supabase-Client-Runtime": "python",
            "X-Supabase-Client-Runtime-Version": platform.python_version(),
            **headers,
        }

        if sys.version_info < (3, 10):
            warn(
                "Python versions below 3.10 are deprecated and will not be supported in future versions. Please upgrade to Python 3.10 or newer.",
                DeprecationWarning,
                stacklevel=2,
            )

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

        self.session = http_client or AsyncClient(
            headers=headers,
            timeout=self.timeout,
            proxy=proxy,
            verify=self.verify,
            follow_redirects=True,
            http2=True,
        )
        super().__init__(self.session, url, Headers(headers))

    async def __aenter__(self) -> AsyncStorageClient:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.session.aclose()

    def from_(self, id: str) -> AsyncBucketProxy:
        """Run a storage file operation.

        Parameters
        ----------
        id
            The unique identifier of the bucket
        """
        return AsyncBucketProxy(id, self._base_url, self._headers, self._client)

    def vectors(self) -> AsyncStorageVectorsClient:
        return AsyncStorageVectorsClient(
            url=self._base_url.joinpath("vector"),
            headers=self._headers,
            session=self.session,
        )

    def analytics(self) -> AsyncStorageAnalyticsClient:
        request = AsyncRequestBuilder(
            session=self.session,
            headers=self._headers,
            base_url=self._base_url.joinpath("iceberg"),
        )
        return AsyncStorageAnalyticsClient(request=request)
