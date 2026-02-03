from __future__ import annotations

import platform
import sys
from typing import Any, Dict, Optional, Union, cast
from warnings import warn

from deprecation import deprecated
from httpx import AsyncClient, Headers, QueryParams, Timeout
from yarl import URL

from ..base_client import BasePostgrestClient
from ..constants import (
    DEFAULT_POSTGREST_CLIENT_HEADERS,
    DEFAULT_POSTGREST_CLIENT_TIMEOUT,
)
from ..types import CountMethod
from ..version import __version__
from .request_builder import (
    AsyncRequestBuilder,
    AsyncRPCFilterRequestBuilder,
    RequestConfig,
)


class AsyncPostgrestClient(BasePostgrestClient):
    """PostgREST client."""

    def __init__(
        self,
        base_url: str,
        *,
        schema: str = "public",
        headers: Dict[str, str] = DEFAULT_POSTGREST_CLIENT_HEADERS,
        timeout: Union[int, float, Timeout, None] = None,
        verify: Optional[bool] = None,
        proxy: Optional[str] = None,
        http_client: Optional[AsyncClient] = None,
    ) -> None:
        headers = {
            "X-Client-Info": f"supabase-py/postgrest-py v{__version__}",
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
        self.timeout = (
            timeout
            if isinstance(timeout, Timeout)
            else (
                int(abs(timeout))
                if timeout is not None
                else DEFAULT_POSTGREST_CLIENT_TIMEOUT
            )
        )
        BasePostgrestClient.__init__(
            self,
            URL(base_url),
            schema=schema,
            headers=headers,
            timeout=self.timeout,
            verify=self.verify,
            proxy=proxy,
        )

        self.session = http_client or AsyncClient(
            base_url=base_url,
            headers=self.headers,
            timeout=timeout,
            verify=self.verify,
            proxy=proxy,
            follow_redirects=True,
            http2=True,
        )

    def schema(self, schema: str) -> AsyncPostgrestClient:
        """Switch to another schema."""
        return AsyncPostgrestClient(
            base_url=str(self.base_url),
            schema=schema,
            headers=dict(self.headers),
            timeout=self.timeout,
            verify=self.verify,
            proxy=self.proxy,
        )

    async def __aenter__(self) -> AsyncPostgrestClient:
        return self

    async def __aexit__(self, exc_type, exc, tb) -> None:
        await self.aclose()

    async def aclose(self) -> None:
        """Close the underlying HTTP connections."""
        await self.session.aclose()

    def from_(self, table: str) -> AsyncRequestBuilder:
        """Perform a table operation.

        Args:
            table: The name of the table
        Returns:
            :class:`AsyncRequestBuilder`
        """
        return AsyncRequestBuilder(
            self.session, self.base_url.joinpath(table), self.headers, self.basic_auth
        )

    def table(self, table: str) -> AsyncRequestBuilder:
        """Alias to :meth:`from_`."""
        return self.from_(table)

    @deprecated("0.2.0", "1.0.0", __version__, "Use self.from_() instead")
    def from_table(self, table: str) -> AsyncRequestBuilder:
        """Alias to :meth:`from_`."""
        return self.from_(table)

    def rpc(
        self,
        func: str,
        params: dict[str, str],
        count: Optional[CountMethod] = None,
        head: bool = False,
        get: bool = False,
    ) -> AsyncRPCFilterRequestBuilder:
        """Perform a stored procedure call.

        Args:
            func: The name of the remote procedure to run.
            params: The parameters to be passed to the remote procedure.
            count: The method to use to get the count of rows returned.
            head: When set to `true`, `data` will not be returned. Useful if you only need the count.
            get: When set to `true`, the function will be called with read-only access mode.
        Returns:
            :class:`AsyncRPCFilterRequestBuilder`
        Example:
            .. code-block:: python

                await client.rpc("foobar", {"arg": "value"}).execute()

        .. versionchanged:: 0.10.9
            This method now returns a :class:`AsyncRPCFilterRequestBuilder`.
        .. versionchanged:: 0.10.2
            This method now returns a :class:`AsyncFilterRequestBuilder` which allows you to
            filter on the RPC's resultset.
        """
        method = "HEAD" if head else "GET" if get else "POST"

        headers = Headers({"Prefer": f"count={count}"}) if count else Headers()
        headers.update(self.headers)
        # the params here are params to be sent to the RPC and not the queryparams!
        json, http_params = (
            ({}, QueryParams(params))
            if method in ("HEAD", "GET")
            else (params, QueryParams())
        )
        request = RequestConfig(
            self.session,
            self.base_url.joinpath("rpc", func),
            method,
            headers,
            http_params,
            self.basic_auth,
            json,
        )
        return AsyncRPCFilterRequestBuilder(request)
