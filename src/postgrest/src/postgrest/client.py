from __future__ import annotations

from base64 import b64encode
from types import TracebackType
from typing import Generic, Literal, overload

from supabase_utils.http.headers import Headers
from supabase_utils.http.io import (
    AsyncHttpIO,
    AsyncHttpSession,
    HttpIO,
    HttpSession,
    SyncHttpIO,
)
from supabase_utils.http.query import URLQuery
from supabase_utils.http.request import HTTPRequestMethod, JSONRequest
from typing_extensions import Self
from yarl import URL

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
        self.default_headers = default_headers.set("Accept-Profile", schema).set(
            "Content-Profile", schema
        )

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
        self.default_headers = self.default_headers.override(
            "Authorization", f"Bearer {token}"
        )
        return self

    def set_auth_with_password(
        self,
        username: str,
        password: str,
    ) -> Self:
        userpass = f"{username}:{password}"
        token = b64encode(userpass.encode("utf8")).decode()
        self.default_headers = self.default_headers.override(
            "Authorization", f"Basic {token}"
        )
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
        )

    def table(self, table: str) -> RequestBuilder[HttpIO]:
        """Alias to :meth:`from_`."""
        return self.from_(table)

    @overload
    def rpc(
        self,
        func: str,
        params: dict[str, str],
        *,
        head: Literal[False],
        count: CountMethod | None = None,
        get: bool = False,
    ) -> RPCFilterRequestBuilder[HttpIO]: ...

    @overload
    def rpc(
        self,
        func: str,
        params: dict[str, str],
        *,
        head: Literal[True],
        count: CountMethod | None = None,
        get: bool = False,
    ) -> RPCCountRequestBuilder[HttpIO]: ...

    @overload
    def rpc(
        self,
        func: str,
        params: dict[str, str],
    ) -> RPCFilterRequestBuilder[HttpIO]: ...

    @overload
    def rpc(
        self,
        func: str,
        params: dict[str, str],
        *,
        get: Literal[True],
    ) -> RPCFilterRequestBuilder[HttpIO]: ...

    @overload
    def rpc(
        self,
        func: str,
        params: dict[str, str],
        *,
        count: CountMethod | None = None,
        get: Literal[False],
    ) -> RPCFilterRequestBuilder[HttpIO] | RPCCountRequestBuilder[HttpIO]: ...
    @overload
    def rpc(
        self,
        func: str,
        params: dict[str, str],
        *,
        count: CountMethod | None = None,
        get: Literal[True],
    ) -> RPCFilterRequestBuilder[HttpIO]: ...

    def rpc(
        self,
        func: str,
        params: dict[str, str],
        *,
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

        headers = (
            Headers.from_mapping({"Prefer": f"count={count}"})
            if count
            else Headers.empty()
        )

        # the params here are params to be sent to the RPC and not the queryparams!
        json, http_params = (
            ({}, URLQuery.from_mapping(params))
            if method in ("HEAD", "GET")
            else (params, URLQuery.empty())
        )
        request = JSONRequest(
            path=["rpc", func],
            method=method,
            headers=headers,
            query=http_params,
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
        http_session: AsyncHttpSession,
        headers: dict[str, str] | None = None,
        schema: str = "public",
    ) -> None:
        PostgrestClient.__init__(
            self,
            executor=AsyncHttpIO(session=http_session),
            base_url=URL(base_url),
            default_headers=Headers.from_mapping(headers)
            if headers
            else Headers.empty(),
            schema=schema,
        )

    def schema(self, schema: str) -> AsyncPostgrestClient:
        """Switch to another schema."""
        return AsyncPostgrestClient(
            http_session=self.executor.session,
            base_url=str(self.base_url),
            headers=dict(self.default_headers),
            schema=schema,
        )

    async def __aenter__(self) -> AsyncPostgrestClient:
        await self.executor.session.__aenter__()
        return self

    async def __aexit__(
        self,
        exc_type: type[Exception] | None,
        exc: Exception | None,
        tb: TracebackType | None,
    ) -> None:
        await self.executor.session.__aexit__(exc_type, exc, tb)


class SyncPostgrestClient(PostgrestClient[SyncHttpIO]):
    def __init__(
        self,
        base_url: str,
        http_session: HttpSession,
        headers: dict[str, str] | None = None,
        *,
        schema: str = "public",
    ) -> None:
        PostgrestClient.__init__(
            self,
            executor=SyncHttpIO(session=http_session),
            base_url=URL(base_url),
            default_headers=Headers.from_mapping(headers)
            if headers
            else Headers.empty(),
            schema=schema,
        )

    def __enter__(self) -> SyncPostgrestClient:
        self.executor.session.__enter__()
        return self

    def __exit__(
        self,
        exc_type: type[Exception] | None,
        exc: Exception | None,
        tb: TracebackType | None,
    ) -> None:
        self.executor.session.__exit__(exc_type, exc, tb)

    def schema(self, schema: str) -> SyncPostgrestClient:
        """Switch to another schema."""
        return SyncPostgrestClient(
            base_url=str(self.base_url),
            headers=dict(self.default_headers),
            schema=schema,
            http_session=self.executor.session,
        )
