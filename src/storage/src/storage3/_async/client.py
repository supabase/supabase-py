from __future__ import annotations

from typing import Optional
from warnings import warn

from httpx import AsyncClient

from storage3.constants import DEFAULT_TIMEOUT

from ..version import __version__
from .bucket import AsyncStorageBucketAPI
from .file_api import AsyncBucketProxy

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

        self.session = self._create_session(
            base_url=url,
            headers=headers,
            timeout=self.timeout,
            verify=self.verify,
            proxy=proxy,
            http_client=http_client,
        )
        super().__init__(self.session)

    def _create_session(
        self,
        base_url: str,
        headers: dict[str, str],
        timeout: int,
        verify: bool = True,
        proxy: Optional[str] = None,
        http_client: Optional[AsyncClient] = None,
    ) -> AsyncClient:
        if http_client is not None:
            http_client.base_url = base_url
            http_client.headers.update({**headers})
            return http_client

        return AsyncClient(
            base_url=base_url,
            headers=headers,
            timeout=timeout,
            proxy=proxy,
            verify=verify,
            follow_redirects=True,
            http2=True,
        )

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
        return AsyncBucketProxy(id, self._client)
