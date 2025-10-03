from __future__ import annotations

from typing import Any, Dict, Optional, Union, cast
from warnings import warn

from deprecation import deprecated
from httpx import Client, Headers, QueryParams, Timeout

from ..base_client import BasePostgrestClient
from ..constants import (
    DEFAULT_POSTGREST_CLIENT_HEADERS,
    DEFAULT_POSTGREST_CLIENT_TIMEOUT,
)
from ..types import CountMethod
from ..version import __version__
from .request_builder import SyncRequestBuilder, SyncRPCFilterRequestBuilder


class SyncPostgrestClient(BasePostgrestClient):
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
        http_client: Optional[Client] = None,
    ) -> None:
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
            base_url,
            schema=schema,
            headers=headers,
            timeout=self.timeout,
            verify=self.verify,
            proxy=proxy,
            http_client=http_client,
        )
        self.session: Client = self.session

    def create_session(
        self,
        base_url: str,
        headers: Dict[str, str],
        timeout: Union[int, float, Timeout],
        verify: bool = True,
        proxy: Optional[str] = None,
    ) -> Client:
        http_client = None
        if isinstance(self.http_client, Client):
            http_client = self.http_client

        if http_client is not None:
            http_client.base_url = base_url
            http_client.headers.update({**headers})
            return http_client

        return Client(
            base_url=base_url,
            headers=headers,
            timeout=timeout,
            verify=verify,
            proxy=proxy,
            follow_redirects=True,
            http2=True,
        )

    def schema(self, schema: str):
        """Switch to another schema."""
        return SyncPostgrestClient(
            base_url=self.base_url,
            schema=schema,
            headers=self.headers,
            timeout=self.timeout,
            verify=self.verify,
            proxy=self.proxy,
        )

    def __enter__(self) -> SyncPostgrestClient:
        return self

    def __exit__(self, exc_type, exc, tb) -> None:
        self.aclose()

    def aclose(self) -> None:
        """Close the underlying HTTP connections."""
        self.session.close()

    def from_(self, table: str) -> SyncRequestBuilder:
        """Perform a table operation.

        Args:
            table: The name of the table
        Returns:
            :class:`AsyncRequestBuilder`
        """
        return SyncRequestBuilder(self.session, f"/{table}")

    def table(self, table: str) -> SyncRequestBuilder:
        """Alias to :meth:`from_`."""
        return self.from_(table)

    @deprecated("0.2.0", "1.0.0", __version__, "Use self.from_() instead")
    def from_table(self, table: str) -> SyncRequestBuilder:
        """Alias to :meth:`from_`."""
        return self.from_(table)

    def rpc(
        self,
        func: str,
        params: dict,
        count: Optional[CountMethod] = None,
        head: bool = False,
        get: bool = False,
    ) -> SyncRPCFilterRequestBuilder:
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

        if method in ("HEAD", "GET"):
            return SyncRPCFilterRequestBuilder(
                self.session,
                f"/rpc/{func}",
                method,
                headers,
                QueryParams(params),
                json={},
            )
        # the params here are params to be sent to the RPC and not the queryparams!
        return SyncRPCFilterRequestBuilder(
            self.session, f"/rpc/{func}", method, headers, QueryParams(), json=params
        )
