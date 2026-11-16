from __future__ import annotations

from base64 import b64encode
from typing import TYPE_CHECKING, Literal, Self, overload

from supabase_utils.http.headers import Headers
from supabase_utils.http.io import (
    AsyncHttpIO,
    AsyncHttpSession,
    HttpSession,
    SyncHttpIO,
)
from yarl import URL

from .request_builder import (
    RequestBuilder,
    RPCCountRequestBuilder,
    RPCFilterRequestBuilder,
    pre_rpc,
)
from .utils import is_http_url
from .version import __version__

if TYPE_CHECKING:
    from collections.abc import Mapping
    from types import TracebackType

    from supabase_utils.http.retry import RetryPolicy
    from supabase_utils.types import JSON

    from .types import CountMethod


class PostgrestClient[HttpIO: (SyncHttpIO, AsyncHttpIO)]:
    """PostgREST client."""

    def __init__(
        self,
        executor: HttpIO,
        base_url: URL,
        default_headers: Headers,
        *,
        schema: str = "public",
    ) -> None:
        if not is_http_url(base_url):
            raise ValueError("base_url must be a valid HTTP URL string")
        supabase_headers = Headers.supabase_client_headers("postgrest", __version__)
        self.executor: HttpIO = executor
        self.base_url = base_url
        self.default_headers = (
            supabase_headers.update(default_headers)
            .set("Accept-Profile", schema)
            .set("Content-Profile", schema)
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
        params: Mapping[str, JSON],
        *,
        head: Literal[False] = False,
        count: CountMethod | None = None,
        get: bool = False,
    ) -> RPCFilterRequestBuilder[HttpIO]: ...

    @overload
    def rpc(
        self,
        func: str,
        params: Mapping[str, JSON],
        *,
        head: Literal[True],
        count: CountMethod | None = None,
        get: bool = False,
    ) -> RPCCountRequestBuilder[HttpIO]: ...

    @overload
    def rpc(
        self,
        func: str,
        params: Mapping[str, JSON],
        *,
        head: bool,
        count: CountMethod | None = None,
        get: bool = False,
    ) -> RPCFilterRequestBuilder[HttpIO] | RPCCountRequestBuilder[HttpIO]: ...

    def rpc(
        self,
        func: str,
        params: Mapping[str, JSON],
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
        """
        request = pre_rpc(func, params, head=head, count=count, get=get)
        if not head:
            return RPCFilterRequestBuilder(
                executor=self.executor,
                base_url=self.base_url,
                default_headers=self.default_headers,
                request=request,
            )
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
        headers: Mapping[str, str] | None = None,
        schema: str = "public",
        *,
        request_timeout: float | None = None,
        retry: RetryPolicy | None = None,
    ) -> None:
        """Create a PostgREST client.

        Args:
            base_url: The URL of the PostgREST service.
            http_session: The HTTP session that sends the requests.
            headers: Headers sent with every request.
            schema: The Postgres schema to query.
            request_timeout: Seconds a request may go without progress before
                it fails with `RequestTimeoutError`. None leaves the timeout to
                the HTTP client. Use `request_timeout()` on a query to override
                it for that query.
            retry: How GET and HEAD requests that failed in a way worth
                repeating are retried. None uses the default `RetryPolicy`.
                Use `retry()` on a query to override it for that query.
        """
        user_headers = Headers.from_mapping(headers) if headers else Headers.empty()
        super().__init__(
            executor=AsyncHttpIO(
                session=http_session, request_timeout=request_timeout, retry=retry
            ),
            base_url=URL(base_url),
            default_headers=user_headers,
            schema=schema,
        )

    def schema(self, schema: str) -> AsyncPostgrestClient:
        """Switch to another schema."""
        return AsyncPostgrestClient(
            http_session=self.executor.session,
            base_url=str(self.base_url),
            headers=dict(self.default_headers),
            schema=schema,
            request_timeout=self.executor.request_timeout,
            retry=self.executor.retry_policy,
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


class SyncPostgrestClient(PostgrestClient[SyncHttpIO]):
    def __init__(
        self,
        base_url: str,
        http_session: HttpSession,
        headers: Mapping[str, str] | None = None,
        *,
        schema: str = "public",
        request_timeout: float | None = None,
        retry: RetryPolicy | None = None,
    ) -> None:
        """Create a PostgREST client.

        Args:
            base_url: The URL of the PostgREST service.
            http_session: The HTTP session that sends the requests.
            headers: Headers sent with every request.
            schema: The Postgres schema to query.
            request_timeout: Seconds a request may go without progress before
                it fails with `RequestTimeoutError`. None leaves the timeout to
                the HTTP client. Use `request_timeout()` on a query to override
                it for that query.
            retry: How GET and HEAD requests that failed in a way worth
                repeating are retried. None uses the default `RetryPolicy`.
                Use `retry()` on a query to override it for that query.
        """
        user_headers = Headers.from_mapping(headers) if headers else Headers.empty()
        super().__init__(
            executor=SyncHttpIO(
                session=http_session, request_timeout=request_timeout, retry=retry
            ),
            base_url=URL(base_url),
            default_headers=user_headers,
            schema=schema,
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

    def schema(self, schema: str) -> SyncPostgrestClient:
        """Switch to another schema."""
        return SyncPostgrestClient(
            base_url=str(self.base_url),
            headers=dict(self.default_headers),
            schema=schema,
            http_session=self.executor.session,
            request_timeout=self.executor.request_timeout,
            retry=self.executor.retry_policy,
        )
