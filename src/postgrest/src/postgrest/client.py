from __future__ import annotations

from base64 import b64encode
from types import TracebackType
from typing import Generic, Literal, overload

from httpx import AsyncClient, BasicAuth, Client, Headers, QueryParams
from supabase_utils.http import (
    AsyncHttpIO,
    HttpIO,
    HTTPRequestMethod,
    JSONRequest,
    SyncHttpIO,
)
from typing_extensions import Self
from yarl import URL

from .constants import DEFAULT_POSTGREST_CLIENT_HEADERS
from .request_builder import (
    RequestBuilder,
    RPCCountRequestBuilder,
    RPCFilterRequestBuilder,
)
from .types import CountMethod


class PostgrestClient(Generic[HttpIO]):
    """PostgREST client."""

    def __init__(
        self,
        executor: HttpIO,
        base_url: URL,
        default_headers: Headers,
        *,
        schema: str = "public",
    ) -> None:
        self.executor: HttpIO = executor
        self.base_url = base_url
        self.default_headers = default_headers
        self.default_headers["Accept-Profile"] = schema
        self.default_headers["Content-Profile"] = schema
        self.basic_auth: BasicAuth | None = None

    def set_auth(
        self,
        token: str,
    ) -> Self:
        """
        Authenticate the client with either bearer token or basic authentication.

        Raises:
            `ValueError`: If neither authentication scheme is provided.

        .. note::
            Bearer token is preferred if both ones are provided.
        """
        self.default_headers["Authorization"] = f"Bearer {token}"
        return self

    def set_auth_with_password(
        self,
        username: str,
        password: str,
    ) -> Self:
        userpass = f"{username}:{password}"
        token = b64encode(userpass.encode("utf8")).decode()
        self.default_headers["Authorization"] = f"Basic {token}"
        return self

    def from_(self, table: str) -> RequestBuilder[HttpIO]:
        """Perform a table operation.

        Args:
            table: The name of the table
        Returns:
            :class:`AsyncRequestBuilder`
        """
        return RequestBuilder(
            executor=self.executor,
            base_url=self.base_url.joinpath(table),
            default_headers=self.default_headers,
            basic_auth=self.basic_auth,
        )

    def table(self, table: str) -> RequestBuilder[HttpIO]:
        """Alias to :meth:`from_`."""
        return self.from_(table)

    @overload
    def rpc(
        self,
        func: str,
        params: dict[str, str],
        head: Literal[False],
        count: CountMethod | None = None,
        get: bool = False,
    ) -> RPCFilterRequestBuilder[HttpIO]: ...

    @overload
    def rpc(
        self,
        func: str,
        params: dict[str, str],
        head: Literal[True],
        count: CountMethod | None = None,
        get: bool = False,
    ) -> RPCCountRequestBuilder[HttpIO]: ...

    @overload
    def rpc(
        self,
        func: str,
        params: dict[str, str],
        head: bool,
        count: CountMethod | None = None,
        get: bool = False,
    ) -> RPCFilterRequestBuilder[HttpIO] | RPCCountRequestBuilder[HttpIO]: ...

    def rpc(
        self,
        func: str,
        params: dict[str, str],
        head: bool = False,
        count: CountMethod | None = None,
        get: bool = False,
    ) -> RPCFilterRequestBuilder[HttpIO] | RPCCountRequestBuilder[HttpIO]:
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
        method: HTTPRequestMethod = "HEAD" if head else "GET" if get else "POST"

        headers = Headers({"Prefer": f"count={count}"}) if count else Headers()

        # the params here are params to be sent to the RPC and not the queryparams!
        json, http_params = (
            ({}, QueryParams(params))
            if method in ("HEAD", "GET")
            else (params, QueryParams())
        )
        request = JSONRequest(
            path=["rpc", func],
            method=method,
            headers=headers,
            query_params=http_params,
            body=json,
        )
        if not head:
            return RPCFilterRequestBuilder(
                executor=self.executor,
                base_url=self.base_url,
                default_headers=self.default_headers,
                request=request,
            )
        else:
            return RPCCountRequestBuilder(
                executor=self.executor,
                base_url=self.base_url,
                default_headers=self.default_headers,
                request=request,
            )


class AsyncPostgrestClient(PostgrestClient[AsyncHttpIO]):
    def __init__(
        self,
        base_url: str,
        headers: dict[str, str] = DEFAULT_POSTGREST_CLIENT_HEADERS,
        http_client: AsyncClient | None = None,
        schema: str = "public",
    ) -> None:
        client = http_client or AsyncClient(
            verify=True,
            http2=True,
        )
        PostgrestClient.__init__(
            self,
            executor=AsyncHttpIO(session=client),
            base_url=URL(base_url),
            default_headers=Headers(headers),
            schema=schema,
        )

    def schema(self, schema: str) -> AsyncPostgrestClient:
        """Switch to another schema."""
        return AsyncPostgrestClient(
            http_client=self.executor.session,
            base_url=str(self.base_url),
            headers=dict(self.default_headers),
            schema=schema,
        )

    async def __aenter__(self) -> AsyncPostgrestClient:
        return self

    async def __aexit__(
        self,
        exc_type: type[Exception] | None,
        exc: Exception | None,
        tb: TracebackType | None,
    ) -> None:
        await self.executor.session.aclose()


class SyncPostgrestClient(PostgrestClient[SyncHttpIO]):
    def __init__(
        self,
        base_url: str,
        headers: dict[str, str] = DEFAULT_POSTGREST_CLIENT_HEADERS,
        http_client: Client | None = None,
        *,
        schema: str = "public",
    ) -> None:
        client = http_client or Client(
            verify=True,
            http2=True,
        )
        PostgrestClient.__init__(
            self,
            executor=SyncHttpIO(session=client),
            base_url=URL(base_url),
            default_headers=Headers(headers),
            schema=schema,
        )

    def __enter__(self) -> SyncPostgrestClient:
        return self

    def __exit__(
        self,
        exc_type: type[Exception] | None,
        exc: Exception | None,
        tb: TracebackType | None,
    ) -> None:
        self.executor.session.close()

    def schema(self, schema: str) -> SyncPostgrestClient:
        """Switch to another schema."""
        return SyncPostgrestClient(
            http_client=self.executor.session,
            base_url=str(self.base_url),
            headers=dict(self.default_headers),
            schema=schema,
        )
