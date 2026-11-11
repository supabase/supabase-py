from __future__ import annotations

import asyncio
import logging
import platform
from abc import ABC, abstractmethod
from functools import cached_property
from types import MappingProxyType
from typing import TYPE_CHECKING, Any, Literal, Self, overload, override

from postgrest import APIError as PostgrestAPIError
from postgrest import APIResponse as PostgrestAPIResponse
from postgrest import AsyncPostgrestClient, SyncPostgrestClient
from realtime import (
    AuthorizationError,
    MaxRetriesExceeded,
    NotConnectedError,
    RealtimeClient,
    RealtimeError,
)
from storage3 import (
    AsyncStorageClient,
    StorageApiError,
    StorageException,
    SyncStorageClient,
    VectorBucketException,
)
from supabase_auth import (
    AsyncSupabaseAuthClient,
    AsyncSupportedStorage,
    AuthApiError,
    AuthChangeEvent,
    AuthError,
    AuthImplicitGrantRedirectError,
    AuthInvalidCredentialsError,
    AuthInvalidJwtError,
    AuthPKCECodeVerifierMissingError,
    AuthRetryableError,
    AuthSessionMissingError,
    AuthUnknownError,
    AuthWeakPasswordError,
    SyncSupabaseAuthClient,
    SyncSupportedStorage,
    UserDoesNotExistError,
)
from supabase_functions import (
    AsyncFunctionsClient,
    FunctionsError,
    FunctionsHttpError,
    FunctionsRelayError,
    SyncFunctionsClient,
)
from supabase_utils.errors import SupabaseError
from supabase_utils.http.errors import (
    RequestTimeoutError,
    SupabaseAPIError,
    SupabaseTransportError,
)
from supabase_utils.http.io import (
    AsyncHttpIO,
    AsyncHttpSession,
    HttpSession,
    SyncHttpIO,
)
from supabase_utils.http.request import validate_request_timeout
from supabase_utils.http.retry import RetryPolicy
from yarl import URL

from .types import (
    AuthClientOptions,
    FunctionsClientOptions,
    PostgrestClientOptions,
    RealtimeClientOptions,
    StorageClientOptions,
)
from .version import __version__

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from collections.abc import Mapping
    from types import TracebackType

    from postgrest.client import PostgrestClient
    from postgrest.request_builder import (
        RequestBuilder,
        RPCCountRequestBuilder,
        RPCFilterRequestBuilder,
    )
    from postgrest.types import CountMethod
    from storage3.client import StorageClient
    from supabase_auth.client import SupabaseAuthHttpClient
    from supabase_auth.types import AuthStateChange
    from supabase_functions.client import FunctionsClient
    from supabase_utils.http.request import Request, Response
    from supabase_utils.types import JSON

    from .types import _ServiceClientOptions

__all__ = [
    "AsyncClient",
    "AuthApiError",
    "AuthError",
    "AuthImplicitGrantRedirectError",
    "AuthInvalidCredentialsError",
    "AuthInvalidJwtError",
    "AuthPKCECodeVerifierMissingError",
    "AuthRetryableError",
    "AuthSessionMissingError",
    "AuthUnknownError",
    "AuthWeakPasswordError",
    "AuthorizationError",
    "Client",
    "FunctionsError",
    "FunctionsHttpError",
    "FunctionsRelayError",
    "MaxRetriesExceeded",
    "NotConnectedError",
    "PostgrestAPIError",
    "PostgrestAPIResponse",
    "RealtimeError",
    "RequestTimeoutError",
    "RetryPolicy",
    "StorageApiError",
    "StorageException",
    "SupabaseAPIError",
    "SupabaseClient",
    "SupabaseError",
    "SupabaseException",
    "SupabaseTransportError",
    "UserDoesNotExistError",
    "VectorBucketException",
    "__version__",
]


_DEFAULT_HEADERS = {
    "X-Client-Info": (
        f"supabase-py/{__version__}"
        f"; platform={platform.system()}"
        f"; platform-version={platform.release()}"
        f"; runtime=python"
        f"; runtime-version={platform.python_version()}"
    )
}


class SupabaseException(SupabaseError):
    """Raised when the client is created with a missing or invalid URL or key, or
    when `auth` is used on a client returned by `with_token()`."""


def _find_authorization(headers: Mapping[str, str]) -> str | None:
    return next(
        (value for key, value in headers.items() if key.lower() == "authorization"),
        None,
    )


def _is_new_api_key(key: str) -> bool:
    return key.startswith("sb_")


class _SharedHttpSession:
    """Sends the requests with a session that another client closes."""

    def __init__(self, session: HttpSession) -> None:
        self.session = session

    def send(self, request: Request) -> Response:
        return self.session.send(request)

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        pass


class _SharedAsyncHttpSession:
    """Sends the requests with a session that another client closes."""

    def __init__(self, session: AsyncHttpSession) -> None:
        self.session = session

    async def send(self, request: Request) -> Response:
        return await self.session.send(request)

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        pass


class SupabaseClient[
    HttpIO: (SyncHttpIO, AsyncHttpIO),
    Storage: (AsyncSupportedStorage, SyncSupportedStorage),
](ABC):
    """Behavior shared by the async and the sync Supabase client."""

    def __init__(
        self,
        supabase_url: str,
        supabase_key: str,
        *,
        headers: Mapping[str, str] | None,
        request_timeout: float | None,
        retry: RetryPolicy | None,
        postgrest: PostgrestClientOptions | None,
        auth: AuthClientOptions[Storage] | None,
        storage: StorageClientOptions | None,
        functions: FunctionsClientOptions | None,
    ) -> None:
        """Instantiate the client.

        Parameters
        ----------
        supabase_url: str
            The URL to the Supabase instance that should be connected to.
        supabase_key: str
            The API key to the Supabase instance that should be connected to.
        headers
            Headers sent with every request, on top of the default ones.
        request_timeout
            Seconds a request to the database, auth, storage or edge functions
            may go without progress before it fails with `RequestTimeoutError`.
            It limits how long the connection may stall, not the whole request,
            so a large transfer that keeps moving is not cut short. None (the
            default) leaves the timeout to the HTTP client. The
            `request_timeout` of a service's options overrides it for that
            service.
        retry
            How requests to the database, auth, storage or edge functions
            that failed in a way worth repeating are retried. None (the
            default) uses the default `RetryPolicy`, which retries GET and
            HEAD requests up to three times on a rate limit, a gateway error
            or a network error. The `retry` of a service's options overrides
            it for that service.
        postgrest
            Options for the database client.
        auth
            Options for the auth client.
        storage
            Options for the storage client.
        functions
            Options for the edge functions client.
        """
        if not supabase_url:
            raise SupabaseException("supabase_url is required")
        if not supabase_key:
            raise SupabaseException("supabase_key is required")

        try:
            self.supabase_url = URL(
                supabase_url if supabase_url.endswith("/") else supabase_url + "/"
            )
        except ValueError as error:
            raise SupabaseException(f"Invalid URL: {supabase_url}") from error
        if self.supabase_url.scheme not in ("http", "https") or not (
            self.supabase_url.host
        ):
            raise SupabaseException(f"Invalid URL: {supabase_url}")

        validate_request_timeout(request_timeout)
        self.supabase_key = supabase_key
        self._request_timeout = request_timeout
        self._retry = retry
        self._postgrest_options = postgrest or PostgrestClientOptions()
        self._auth_options: AuthClientOptions[Storage] = auth or AuthClientOptions()
        self._storage_options = storage or StorageClientOptions()
        self._functions_options = functions or FunctionsClientOptions()

        custom_headers = {
            key: value
            for key, value in (headers or {}).items()
            if key.lower() not in ("apikey", "authorization")
        }
        custom_keys = {key.lower() for key in custom_headers}
        self._headers = {
            **{
                key: value
                for key, value in _DEFAULT_HEADERS.items()
                if key.lower() not in custom_keys
            },
            **custom_headers,
            **self._get_auth_headers(headers or {}),
        }
        authorization = self._headers["Authorization"]
        self._access_token = (
            authorization.removeprefix("Bearer ")
            if authorization.startswith("Bearer ")
            else supabase_key
        )

        self.rest_url = self.supabase_url.joinpath("rest", "v1")
        self.auth_url = self.supabase_url.joinpath("auth", "v1")
        self.storage_url = self.supabase_url.joinpath("storage", "v1", "")
        self.functions_url = self.supabase_url.joinpath("functions", "v1")

    @property
    def headers(self) -> Mapping[str, str]:
        """The headers sent with every request.

        `Authorization` follows the session: it holds the access token of the
        signed in user, or the API key when nobody is signed in.
        """
        return MappingProxyType(self._headers)

    def with_token(self, access_token: str) -> Self:
        """Return a client that makes its requests as the user of `access_token`.

        Use it on a server to act for the user who sent a request, so row
        level security applies to their JWT. Pass the JWT without the
        `Bearer ` prefix.

        The returned client shares the HTTP session, the headers and the
        options of this client, and does no I/O, so creating one per request
        is cheap. Leaving it or its services with `with` or `async with` does
        not close the shared HTTP session.

        `access_token` is sent as the `Authorization` header and is never
        refreshed or replaced. The returned client has no auth client, so
        using its `auth` raises `SupabaseException`. Use the `auth` of this
        client instead, for example `auth.get_claims(access_token)` to verify
        the JWT.
        """
        if not access_token:
            raise ValueError("access_token is required")
        return self._without_auth(
            {**self._headers, "Authorization": self._create_auth_header(access_token)}
        )

    @abstractmethod
    def _without_auth(self, headers: Mapping[str, str]) -> Self: ...

    def _no_auth_error(self) -> SupabaseException:
        return SupabaseException(
            "The client was created with with_token(), so it has no auth"
            " client. Use the auth of the client that with_token() was called on."
        )

    @property
    @abstractmethod
    def auth(self) -> SupabaseAuthHttpClient[HttpIO, Any]: ...

    @property
    @abstractmethod
    def postgrest(self) -> PostgrestClient[HttpIO]: ...

    @property
    @abstractmethod
    def storage(self) -> StorageClient[HttpIO]: ...

    @property
    @abstractmethod
    def functions(self) -> FunctionsClient[HttpIO]: ...

    def table(self, table_name: str) -> RequestBuilder[HttpIO]:
        """Perform a table operation.

        Note that the supabase client uses the `from` method, but in Python,
        this is a reserved keyword, so we have elected to use the name `table`.
        Alternatively you can use the `.from_()` method.
        """
        return self.from_(table_name)

    def from_(self, table_name: str) -> RequestBuilder[HttpIO]:
        """Perform a table operation.

        See the `table` method.
        """
        return self.postgrest.from_(table_name)

    @overload
    def rpc(
        self,
        fn: str,
        params: Mapping[str, JSON] | None = None,
        *,
        head: Literal[False] = False,
        count: CountMethod | None = None,
        get: bool = False,
    ) -> RPCFilterRequestBuilder[HttpIO]: ...

    @overload
    def rpc(
        self,
        fn: str,
        params: Mapping[str, JSON] | None = None,
        *,
        head: Literal[True],
        count: CountMethod | None = None,
        get: bool = False,
    ) -> RPCCountRequestBuilder[HttpIO]: ...

    @overload
    def rpc(
        self,
        fn: str,
        params: Mapping[str, JSON] | None = None,
        *,
        head: bool,
        count: CountMethod | None = None,
        get: bool = False,
    ) -> RPCFilterRequestBuilder[HttpIO] | RPCCountRequestBuilder[HttpIO]: ...

    def rpc(
        self,
        fn: str,
        params: Mapping[str, JSON] | None = None,
        *,
        head: bool = False,
        count: CountMethod | None = None,
        get: bool = False,
    ) -> RPCFilterRequestBuilder[HttpIO] | RPCCountRequestBuilder[HttpIO]:
        """Performs a stored procedure call.

        Parameters
        ----------
        fn : str
            The name of the stored procedure to call.
        params : dict of any
            Parameters passed into the stored procedure call.
        head: When set to `true`, `data` will not be returned. Useful if you only need the count.
        count: The method to use to get the count of rows returned.
        get: When set to `true`, the function will be called with read-only access mode.

        Returns
        -------
        RPCFilterRequestBuilder
            A filter builder that lets you apply filters on the response of
            the RPC. An RPCCountRequestBuilder when `head` is true.
        """
        return self.postgrest.rpc(fn, params or {}, head=head, count=count, get=get)

    def _timeout_for(self, service_options: _ServiceClientOptions) -> float | None:
        if service_options.request_timeout is not None:
            return service_options.request_timeout
        return self._request_timeout

    def _retry_for(self, service_options: _ServiceClientOptions) -> RetryPolicy | None:
        if service_options.retry is not None:
            return service_options.retry
        return self._retry

    def _create_auth_header(self, token: str) -> str:
        return f"Bearer {token}"

    def _get_auth_headers(self, headers: Mapping[str, str]) -> dict[str, str]:
        authorization = _find_authorization(headers) or self._create_auth_header(
            self.supabase_key
        )
        return {
            "apiKey": self.supabase_key,
            "Authorization": authorization,
        }

    def _functions_authorization(self, authorization: str) -> str | None:
        if _is_new_api_key(self.supabase_key) and (
            authorization == self._create_auth_header(self.supabase_key)
        ):
            return None
        return authorization

    def _functions_headers(self) -> dict[str, str]:
        headers = dict(self._headers)
        authorization = self._functions_authorization(headers.pop("Authorization"))
        return (
            headers
            if authorization is None
            else {**headers, "Authorization": authorization}
        )

    def _listen_to_auth_events(self, change: AuthStateChange) -> None:
        if change.session is not None:
            self._set_access_token(change.session.access_token)
        elif change.event is not AuthChangeEvent.INITIAL_SESSION:
            self._set_access_token(self.supabase_key)

    def _set_access_token(self, access_token: str) -> None:
        authorization = self._create_auth_header(access_token)
        self._headers["Authorization"] = authorization
        self._access_token = access_token
        self.auth.default_headers = self.auth.default_headers.override(
            "Authorization", authorization
        )
        self.postgrest.default_headers = self.postgrest.default_headers.override(
            "Authorization", authorization
        )
        self.storage.default_headers = self.storage.default_headers.override(
            "Authorization", authorization
        )
        functions_authorization = self._functions_authorization(authorization)
        self.functions.default_headers = (
            self.functions.default_headers.remove("Authorization")
            if functions_authorization is None
            else self.functions.default_headers.override(
                "Authorization", functions_authorization
            )
        )


class AsyncClient(SupabaseClient[AsyncHttpIO, AsyncSupportedStorage]):
    """Async Supabase client."""

    def __init__(
        self,
        supabase_url: str,
        supabase_key: str,
        http_session: AsyncHttpSession,
        *,
        headers: Mapping[str, str] | None = None,
        request_timeout: float | None = None,
        retry: RetryPolicy | None = None,
        postgrest: PostgrestClientOptions | None = None,
        auth: AuthClientOptions[AsyncSupportedStorage] | None = None,
        storage: StorageClientOptions | None = None,
        functions: FunctionsClientOptions | None = None,
        realtime: RealtimeClientOptions | None = None,
    ) -> None:
        """Instantiate the client.

        `http_session` sends the requests and stays open when the client is
        closed. `realtime` configures the realtime client. See
        `SupabaseClient` for the other arguments.
        """
        self.http_session = http_session
        self._owns_http_session = False
        self._realtime_options = realtime or RealtimeClientOptions()
        self._realtime_auth_tasks: set[asyncio.Task[None]] = set()
        super().__init__(
            supabase_url,
            supabase_key,
            headers=headers,
            request_timeout=request_timeout,
            retry=retry,
            postgrest=postgrest,
            auth=auth,
            storage=storage,
            functions=functions,
        )
        self.realtime_url = self.supabase_url.joinpath("realtime", "v1").with_scheme(
            "wss" if self.supabase_url.scheme == "https" else "ws"
        )
        auth_client = AsyncSupabaseAuthClient(
            url=str(self.auth_url),
            http_session=self.http_session,
            headers=self._headers,
            auto_refresh_token=self._auth_options.auto_refresh_token,
            storage=self._auth_options.session_storage,
            storage_key=self._auth_options.storage_key,
            flow_type=self._auth_options.flow_type,
            append_flow_id_to_redirects=self._auth_options.append_flow_id_to_redirects,
            request_timeout=self._timeout_for(self._auth_options),
            retry=self._retry_for(self._auth_options),
        )
        self._auth: AsyncSupabaseAuthClient | None = auth_client
        auth_client.on_auth_state_change(self._listen_to_auth_events)

    @classmethod
    async def create(
        cls,
        supabase_url: str,
        supabase_key: str,
        http_session: AsyncHttpSession,
        *,
        headers: Mapping[str, str] | None = None,
        request_timeout: float | None = None,
        retry: RetryPolicy | None = None,
        postgrest: PostgrestClientOptions | None = None,
        auth: AuthClientOptions[AsyncSupportedStorage] | None = None,
        storage: StorageClientOptions | None = None,
        functions: FunctionsClientOptions | None = None,
        realtime: RealtimeClientOptions | None = None,
    ) -> AsyncClient:
        """Create a client that uses the session in the session storage, if any."""
        client = cls(
            supabase_url,
            supabase_key,
            http_session,
            headers=headers,
            request_timeout=request_timeout,
            retry=retry,
            postgrest=postgrest,
            auth=auth,
            storage=storage,
            functions=functions,
            realtime=realtime,
        )
        auth_header = _find_authorization(headers) if headers else None

        if auth_header is None:
            try:
                session = await client.auth.get_session()
            except Exception:
                session = None
            if session:
                client._set_access_token(session.access_token)

        return client

    async def aclose(self) -> None:
        """Stop the auth auto-refresh and close the connections the client opened.

        Those are the realtime connection and the HTTP session the client
        created. A session passed in by the caller is left open. Closing the
        client more than once is safe.
        """
        if self._auth is not None:
            self._auth.session_manager.stop_auto_refresh()
        for task in self._realtime_auth_tasks:
            task.cancel()
        try:
            if "realtime" in self.__dict__:
                await self.realtime.aclose()
        finally:
            if self._owns_http_session:
                await self.http_session.__aexit__(None, None, None)

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.aclose()

    @override
    def _without_auth(self, headers: Mapping[str, str]) -> Self:
        client = type(self)(
            str(self.supabase_url),
            self.supabase_key,
            _SharedAsyncHttpSession(self.http_session),
            headers=headers,
            request_timeout=self._request_timeout,
            retry=self._retry,
            postgrest=self._postgrest_options,
            auth=self._auth_options,
            storage=self._storage_options,
            functions=self._functions_options,
            realtime=self._realtime_options,
        )
        client._auth = None
        return client

    @property
    @override
    def auth(self) -> AsyncSupabaseAuthClient:
        if self._auth is None:
            raise self._no_auth_error()
        return self._auth

    @cached_property
    @override
    def postgrest(self) -> AsyncPostgrestClient:
        return AsyncPostgrestClient(
            str(self.rest_url),
            http_session=self.http_session,
            headers=self._headers,
            schema=self._postgrest_options.schema,
            request_timeout=self._timeout_for(self._postgrest_options),
            retry=self._retry_for(self._postgrest_options),
        )

    @cached_property
    @override
    def storage(self) -> AsyncStorageClient:
        return AsyncStorageClient(
            url=str(self.storage_url),
            headers=self._headers,
            http_session=self.http_session,
            request_timeout=self._timeout_for(self._storage_options),
            retry=self._retry_for(self._storage_options),
        )

    @cached_property
    @override
    def functions(self) -> AsyncFunctionsClient:
        return AsyncFunctionsClient(
            url=str(self.functions_url),
            headers=self._functions_headers(),
            http_session=self.http_session,
            request_timeout=self._timeout_for(self._functions_options),
            retry=self._retry_for(self._functions_options),
        )

    def schema(self, schema: str) -> AsyncPostgrestClient:
        """Select a schema to query or perform an function (rpc) call.

        The schema needs to be on the list of exposed schemas inside Supabase.
        """
        return self.postgrest.schema(schema)

    @override
    def _set_access_token(self, access_token: str) -> None:
        super()._set_access_token(access_token)
        if "realtime" in self.__dict__:
            self._send_realtime_token()

    def _send_realtime_token(self) -> None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return
        task = loop.create_task(self.realtime.set_auth())
        self._realtime_auth_tasks.add(task)
        task.add_done_callback(self._realtime_auth_done)

    def _realtime_auth_done(self, task: asyncio.Task[None]) -> None:
        self._realtime_auth_tasks.discard(task)
        if not task.cancelled() and (exception := task.exception()) is not None:
            logger.warning(
                "could not send the access token to realtime: %s",
                type(exception).__name__,
            )

    async def _realtime_access_token(self) -> str | None:
        if self._auth is None:
            return self._access_token
        session = await self._auth.get_session()
        return self._access_token if session is None else session.access_token

    @cached_property
    def realtime(self) -> RealtimeClient:
        """The realtime client, which sends the access token of the session.

        It reads the token through `auth.get_session()` when it connects,
        joins a channel or sends a heartbeat, so an expiring session is
        refreshed first. Without a session it sends the `Authorization`
        token of this client, which is the API key by default. A refresh
        that fails raises from `subscribe()`.

        It connects when the first channel subscribes, and disconnects when
        its last channel is removed or this client is closed.
        """
        return RealtimeClient(
            str(self.realtime_url),
            token_callback=self._realtime_access_token,
            heartbeat_interval=self._realtime_options.heartbeat_interval,
            heartbeat_timeout=self._realtime_options.heartbeat_timeout,
        )


class Client(SupabaseClient[SyncHttpIO, SyncSupportedStorage]):
    """Sync Supabase client."""

    def __init__(
        self,
        supabase_url: str,
        supabase_key: str,
        http_session: HttpSession,
        *,
        headers: Mapping[str, str] | None = None,
        request_timeout: float | None = None,
        retry: RetryPolicy | None = None,
        postgrest: PostgrestClientOptions | None = None,
        auth: AuthClientOptions[SyncSupportedStorage] | None = None,
        storage: StorageClientOptions | None = None,
        functions: FunctionsClientOptions | None = None,
    ) -> None:
        """Instantiate the client.

        `http_session` sends the requests and stays open when the client is
        closed. See `SupabaseClient` for the other arguments.
        """
        self.http_session = http_session
        self._owns_http_session = False
        super().__init__(
            supabase_url,
            supabase_key,
            headers=headers,
            request_timeout=request_timeout,
            retry=retry,
            postgrest=postgrest,
            auth=auth,
            storage=storage,
            functions=functions,
        )
        auth_client = SyncSupabaseAuthClient(
            url=str(self.auth_url),
            http_session=self.http_session,
            headers=self._headers,
            auto_refresh_token=self._auth_options.auto_refresh_token,
            storage=self._auth_options.session_storage,
            storage_key=self._auth_options.storage_key,
            flow_type=self._auth_options.flow_type,
            append_flow_id_to_redirects=self._auth_options.append_flow_id_to_redirects,
            request_timeout=self._timeout_for(self._auth_options),
            retry=self._retry_for(self._auth_options),
        )
        self._auth: SyncSupabaseAuthClient | None = auth_client
        auth_client.on_auth_state_change(self._listen_to_auth_events)

    @classmethod
    def create(
        cls,
        supabase_url: str,
        supabase_key: str,
        http_session: HttpSession,
        *,
        headers: Mapping[str, str] | None = None,
        request_timeout: float | None = None,
        retry: RetryPolicy | None = None,
        postgrest: PostgrestClientOptions | None = None,
        auth: AuthClientOptions[SyncSupportedStorage] | None = None,
        storage: StorageClientOptions | None = None,
        functions: FunctionsClientOptions | None = None,
    ) -> Client:
        """Create a client that uses the session in the session storage, if any."""
        client = cls(
            supabase_url,
            supabase_key,
            http_session,
            headers=headers,
            request_timeout=request_timeout,
            retry=retry,
            postgrest=postgrest,
            auth=auth,
            storage=storage,
            functions=functions,
        )
        auth_header = _find_authorization(headers) if headers else None

        if auth_header is None:
            try:
                session = client.auth.get_session()
            except Exception:
                session = None
            if session:
                client._set_access_token(session.access_token)

        return client

    def close(self) -> None:
        """Stop the auth auto-refresh and close the HTTP session the client created.

        A session passed in by the caller is left open. Closing the client
        more than once is safe.
        """
        if self._auth is not None:
            self._auth.session_manager.stop_auto_refresh()
        if self._owns_http_session:
            self.http_session.__exit__(None, None, None)

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.close()

    @override
    def _without_auth(self, headers: Mapping[str, str]) -> Self:
        client = type(self)(
            str(self.supabase_url),
            self.supabase_key,
            _SharedHttpSession(self.http_session),
            headers=headers,
            request_timeout=self._request_timeout,
            retry=self._retry,
            postgrest=self._postgrest_options,
            auth=self._auth_options,
            storage=self._storage_options,
            functions=self._functions_options,
        )
        client._auth = None
        return client

    @property
    @override
    def auth(self) -> SyncSupabaseAuthClient:
        if self._auth is None:
            raise self._no_auth_error()
        return self._auth

    @cached_property
    @override
    def postgrest(self) -> SyncPostgrestClient:
        return SyncPostgrestClient(
            str(self.rest_url),
            http_session=self.http_session,
            headers=self._headers,
            schema=self._postgrest_options.schema,
            request_timeout=self._timeout_for(self._postgrest_options),
            retry=self._retry_for(self._postgrest_options),
        )

    @cached_property
    @override
    def storage(self) -> SyncStorageClient:
        return SyncStorageClient(
            url=str(self.storage_url),
            headers=self._headers,
            http_session=self.http_session,
            request_timeout=self._timeout_for(self._storage_options),
            retry=self._retry_for(self._storage_options),
        )

    @cached_property
    @override
    def functions(self) -> SyncFunctionsClient:
        return SyncFunctionsClient(
            url=str(self.functions_url),
            headers=self._functions_headers(),
            http_session=self.http_session,
            request_timeout=self._timeout_for(self._functions_options),
            retry=self._retry_for(self._functions_options),
        )

    def schema(self, schema: str) -> SyncPostgrestClient:
        """Select a schema to query or perform an function (rpc) call.

        The schema needs to be on the list of exposed schemas inside Supabase.
        """
        return self.postgrest.schema(schema)
