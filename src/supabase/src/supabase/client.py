from __future__ import annotations

import copy
from abc import ABC, abstractmethod
from collections.abc import Mapping
from functools import cached_property
from types import TracebackType
from typing import Any, Generic, Literal, TypeVar, overload

from postgrest import APIError as PostgrestAPIError
from postgrest import APIResponse as PostgrestAPIResponse
from postgrest import AsyncPostgrestClient, SyncPostgrestClient
from postgrest.client import PostgrestClient
from postgrest.request_builder import (
    RequestBuilder,
    RPCCountRequestBuilder,
    RPCFilterRequestBuilder,
)
from postgrest.types import CountMethod
from realtime import AuthorizationError, NotConnectedError, connect_once
from storage3 import (
    AsyncStorageClient,
    StorageApiError,
    StorageException,
    SyncStorageClient,
    VectorBucketException,
)
from storage3 import AsyncStorageClient as AsyncSupabaseStorageClient
from storage3 import SyncStorageClient as SupabaseStorageClient
from storage3.client import StorageClient
from supabase_auth import (
    AsyncSupabaseAuthClient,
    AuthApiError,
    AuthError,
    AuthImplicitGrantRedirectError,
    AuthInvalidCredentialsError,
    AuthInvalidJwtError,
    AuthRetryableError,
    AuthSessionMissingError,
    AuthUnknownError,
    AuthWeakPasswordError,
    CustomAuthError,
    SyncSupabaseAuthClient,
    UserDoesNotExistError,
)
from supabase_auth.client import SupabaseAuthHttpClient
from supabase_auth.types import AuthChangeEvent, Session
from supabase_functions import (
    AsyncFunctionsClient,
    FunctionsError,
    FunctionsHttpError,
    FunctionsRelayError,
    SyncFunctionsClient,
)
from supabase_functions.client import FunctionsClient
from supabase_utils.http.io import (
    AsyncHttpIO,
    AsyncHttpSession,
    HttpIO,
    HttpSession,
    SyncHttpIO,
)
from supabase_utils.types import JSON
from typing_extensions import override
from yarl import URL

from .lib.client_options import AsyncClientOptions, SyncClientOptions
from .lib.client_options import AsyncClientOptions as AClientOptions
from .lib.client_options import SyncClientOptions as ClientOptions
from .version import __version__

__all__ = [
    "AClientOptions",
    "AsyncClient",
    "AsyncClientOptions",
    "AsyncSupabaseStorageClient",
    "Client",
    "ClientOptions",
    "SupabaseClient",
    "SupabaseException",
    "SupabaseStorageClient",
    "PostgrestAPIError",
    "PostgrestAPIResponse",
    "StorageApiError",
    "StorageException",
    "VectorBucketException",
    "__version__",
    "AuthApiError",
    "AuthError",
    "AuthImplicitGrantRedirectError",
    "AuthInvalidCredentialsError",
    "AuthInvalidJwtError",
    "AuthRetryableError",
    "AuthSessionMissingError",
    "AuthWeakPasswordError",
    "AuthUnknownError",
    "CustomAuthError",
    "UserDoesNotExistError",
    "FunctionsHttpError",
    "FunctionsRelayError",
    "FunctionsError",
    "AuthorizationError",
    "NotConnectedError",
]


class SupabaseException(Exception):
    """Raised when the client is created with a missing or invalid URL or key."""

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


Options = TypeVar("Options", AsyncClientOptions, SyncClientOptions)


class SupabaseClient(ABC, Generic[HttpIO, Options]):
    """Behavior shared by the async and the sync Supabase client."""

    def __init__(self, supabase_url: str, supabase_key: str, options: Options) -> None:
        """Instantiate the client.

        Parameters
        ----------
        supabase_url: str
            The URL to the Supabase instance that should be connected to.
        supabase_key: str
            The API key to the Supabase instance that should be connected to.
        options
            The options used to configure the client and its sub-clients.
        """
        if not supabase_url:
            raise SupabaseException("supabase_url is required")
        if not supabase_key:
            raise SupabaseException("supabase_key is required")

        self.supabase_url = URL(
            supabase_url if supabase_url.endswith("/") else supabase_url + "/"
        )
        if self.supabase_url.scheme not in ("http", "https") or not (
            self.supabase_url.host
        ):
            raise SupabaseException(f"Invalid URL: {supabase_url}")

        self.supabase_key = supabase_key
        self.options: Options = copy.copy(options)
        self.options.headers = {
            **options.headers,
            **self._get_auth_headers(),
        }
        self.auth_access_token = supabase_key

        self.rest_url = self.supabase_url.joinpath("rest", "v1")
        self.auth_url = self.supabase_url.joinpath("auth", "v1")
        self.storage_url = self.supabase_url.joinpath("storage", "v1", "")
        self.functions_url = self.supabase_url.joinpath("functions", "v1")

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

    def _create_auth_header(self, token: str) -> str:
        return f"Bearer {token}"

    def _get_auth_headers(self) -> dict[str, str]:
        authorization = self.options.headers.get(
            "Authorization", self._create_auth_header(self.supabase_key)
        )
        return {
            "apiKey": self.supabase_key,
            "Authorization": authorization,
        }

    def _listen_to_auth_events(
        self, event: AuthChangeEvent, session: Session | None
    ) -> None:
        self._set_access_token(session.access_token if session else self.supabase_key)

    def _set_access_token(self, access_token: str) -> None:
        authorization = self._create_auth_header(access_token)
        self.options.headers["Authorization"] = authorization
        self.auth_access_token = access_token
        self.auth.default_headers = self.auth.default_headers.override(
            "Authorization", authorization
        )
        self.postgrest.default_headers = self.postgrest.default_headers.override(
            "Authorization", authorization
        )
        self.storage.default_headers = self.storage.default_headers.override(
            "Authorization", authorization
        )
        self.functions.default_headers = self.functions.default_headers.override(
            "Authorization", authorization
        )


class AsyncClient(SupabaseClient[AsyncHttpIO, AsyncClientOptions]):
    """Async Supabase client."""

    def __init__(
        self,
        supabase_url: str,
        supabase_key: str,
        http_session: AsyncHttpSession,
        options: AsyncClientOptions | None = None,
    ) -> None:
        self.http_session = http_session
        super().__init__(supabase_url, supabase_key, options or AsyncClientOptions())
        self.realtime_url = self.supabase_url.joinpath("realtime", "v1").with_scheme(
            "wss" if self.supabase_url.scheme == "https" else "ws"
        )
        self.auth.on_auth_state_change(self._listen_to_auth_events)

    @classmethod
    async def create(
        cls,
        supabase_url: str,
        supabase_key: str,
        http_session: AsyncHttpSession,
        options: AsyncClientOptions | None = None,
    ) -> AsyncClient:
        auth_header = options.headers.get("Authorization") if options else None
        client = cls(supabase_url, supabase_key, http_session, options)

        if auth_header is None:
            try:
                session = await client.auth.get_session()
            except Exception:
                session = None
            if session:
                client._set_access_token(session.access_token)

        return client

    async def __aenter__(self) -> AsyncClient:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.http_session.__aexit__(exc_type, exc, tb)

    @cached_property
    @override
    def auth(self) -> AsyncSupabaseAuthClient:
        return AsyncSupabaseAuthClient(
            url=str(self.auth_url),
            http_session=self.http_session,
            auto_refresh_token=self.options.auto_refresh_token,
            persist_session=self.options.persist_session,
            storage=self.options.storage,
            headers=self.options.headers,
            flow_type=self.options.flow_type,
        )

    @cached_property
    @override
    def postgrest(self) -> AsyncPostgrestClient:
        return AsyncPostgrestClient(
            str(self.rest_url),
            http_session=self.http_session,
            headers=self.options.headers,
            schema=self.options.schema,
        )

    @cached_property
    @override
    def storage(self) -> AsyncStorageClient:
        return AsyncStorageClient(
            url=str(self.storage_url),
            headers=self.options.headers,
            http_session=self.http_session,
        )

    @cached_property
    @override
    def functions(self) -> AsyncFunctionsClient:
        return AsyncFunctionsClient(
            url=str(self.functions_url),
            headers=self.options.headers,
            http_session=self.http_session,
        )

    def schema(self, schema: str) -> AsyncPostgrestClient:
        """Select a schema to query or perform an function (rpc) call.

        The schema needs to be on the list of exposed schemas inside Supabase.
        """
        return self.postgrest.schema(schema)

    async def realtime_get_token_callback(self) -> str | None:
        return self.auth_access_token

    @property
    def realtime(self) -> connect_once:
        """Create a realtime connection that uses the client's access token."""
        return connect_once(
            str(self.realtime_url),
            token_callback=self.realtime_get_token_callback,
            **(self.options.realtime or {}),
        )


class Client(SupabaseClient[SyncHttpIO, SyncClientOptions]):
    """Sync Supabase client."""

    def __init__(
        self,
        supabase_url: str,
        supabase_key: str,
        http_session: HttpSession,
        options: SyncClientOptions | None = None,
    ) -> None:
        self.http_session = http_session
        super().__init__(supabase_url, supabase_key, options or SyncClientOptions())
        self.auth.on_auth_state_change(self._listen_to_auth_events)

    @classmethod
    def create(
        cls,
        supabase_url: str,
        supabase_key: str,
        http_session: HttpSession,
        options: SyncClientOptions | None = None,
    ) -> Client:
        auth_header = options.headers.get("Authorization") if options else None
        client = cls(supabase_url, supabase_key, http_session, options)

        if auth_header is None:
            try:
                session = client.auth.get_session()
            except Exception:
                session = None
            if session:
                client._set_access_token(session.access_token)

        return client

    def __enter__(self) -> Client:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.http_session.__exit__(exc_type, exc, tb)

    @cached_property
    @override
    def auth(self) -> SyncSupabaseAuthClient:
        return SyncSupabaseAuthClient(
            url=str(self.auth_url),
            http_session=self.http_session,
            auto_refresh_token=self.options.auto_refresh_token,
            persist_session=self.options.persist_session,
            storage=self.options.storage,
            headers=self.options.headers,
            flow_type=self.options.flow_type,
        )

    @cached_property
    @override
    def postgrest(self) -> SyncPostgrestClient:
        return SyncPostgrestClient(
            str(self.rest_url),
            http_session=self.http_session,
            headers=self.options.headers,
            schema=self.options.schema,
        )

    @cached_property
    @override
    def storage(self) -> SyncStorageClient:
        return SyncStorageClient(
            url=str(self.storage_url),
            headers=self.options.headers,
            http_session=self.http_session,
        )

    @cached_property
    @override
    def functions(self) -> SyncFunctionsClient:
        return SyncFunctionsClient(
            url=str(self.functions_url),
            headers=self.options.headers,
            http_session=self.http_session,
        )

    def schema(self, schema: str) -> SyncPostgrestClient:
        """Select a schema to query or perform an function (rpc) call.

        The schema needs to be on the list of exposed schemas inside Supabase.
        """
        return self.postgrest.schema(schema)
