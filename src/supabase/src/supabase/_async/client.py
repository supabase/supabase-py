import copy
from types import TracebackType
from typing import Dict, Literal, overload

from postgrest import AsyncPostgrestClient
from postgrest.request_builder import (
    RequestBuilder,
    RPCCountRequestBuilder,
    RPCFilterRequestBuilder,
)
from postgrest.types import CountMethod
from realtime import connect_once
from storage3 import AsyncStorageClient
from supabase_auth import AsyncMemoryStorage, AsyncSupabaseAuthClient
from supabase_auth.types import AuthChangeEvent, Session
from supabase_functions import AsyncFunctionsClient
from supabase_utils.http.io import AsyncHttpIO, AsyncHttpSession
from yarl import URL

from ..lib.client_options import AsyncClientOptions as ClientOptions


# Create an exception class when user does not provide a valid url or key.
class SupabaseException(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class AsyncClient:
    """Supabase client class."""

    def __init__(
        self,
        supabase_url: str,
        supabase_key: str,
        http_session: AsyncHttpSession,
        options: ClientOptions | None = None,
    ) -> None:
        """Instantiate the client.

        Parameters
        ----------
        supabase_url: str
            The URL to the Supabase instance that should be connected to.
        supabase_key: str
            The API key to the Supabase instance that should be connected to.
        **options
            Any extra settings to be optionally specified - also see the
            `DEFAULT_OPTIONS` dict.
        """

        if not supabase_url:
            raise SupabaseException("supabase_url is required")
        if not supabase_key:
            raise SupabaseException("supabase_key is required")

        self.supabase_url = (
            URL(supabase_url) if supabase_url.endswith("/") else URL(supabase_url + "/")
        )
        # Check if the url and key are valid
        if not (
            self.supabase_url.scheme == "https" or self.supabase_url.scheme == "http"
        ):
            raise SupabaseException(f"Invalid URL: {self.supabase_url}")

        if options is None:
            options = ClientOptions(storage=AsyncMemoryStorage())

        self.http_session: AsyncHttpSession = http_session

        self.supabase_key = supabase_key
        self.options = copy.copy(options)
        self.options.headers = {
            **options.headers,
            **self._get_auth_headers(),
        }

        self.rest_url = self.supabase_url.joinpath("rest", "v1")
        self.realtime_url = self.supabase_url.joinpath("realtime", "v1").with_scheme(
            "wss" if self.supabase_url.scheme == "https" else "ws"
        )
        self.auth_url = self.supabase_url.joinpath("auth", "v1")
        self.storage_url = self.supabase_url.joinpath("storage", "v1", "")
        self.functions_url = self.supabase_url.joinpath("functions", "v1")

        self.auth_access_token = supabase_key

        self.auth.on_auth_state_change(self._listen_to_auth_events)

    async def __aenter__(self) -> "AsyncClient":
        return self

    async def __aexit__(
        self,
        exc_type: type[Exception] | None,
        exc: Exception | None,
        tb: TracebackType | None,
    ) -> None:
        await self.http_session.__aexit__(exc_type, exc, tb)

    @classmethod
    async def create(
        cls,
        supabase_url: str,
        supabase_key: str,
        http_session: AsyncHttpSession,
        options: ClientOptions | None = None,
    ) -> "AsyncClient":
        auth_header = options.headers.get("Authorization") if options else None
        client = cls(supabase_url, supabase_key, http_session, options)

        if auth_header is None:
            try:
                session = await client.auth.get_session()
                session_access_token = (
                    client._create_auth_header(session.access_token)
                    if session
                    else None
                )
            except Exception:
                session_access_token = None

            client.options.headers.update(
                client._get_auth_headers(session_access_token)
            )

        return client

    def table(self, table_name: str) -> RequestBuilder[AsyncHttpIO]:
        """Perform a table operation.

        Note that the supabase client uses the `from` method, but in Python,
        this is a reserved keyword, so we have elected to use the name `table`.
        Alternatively you can use the `.from_()` method.
        """
        return self.from_(table_name)

    def schema(self, schema: str) -> AsyncPostgrestClient:
        """Select a schema to query or perform an function (rpc) call.

        The schema needs to be on the list of exposed schemas inside Supabase.
        """
        return self.postgrest.schema(schema)

    def from_(self, table_name: str) -> RequestBuilder[AsyncHttpIO]:
        """Perform a table operation.

        See the `table` method.
        """
        return self.postgrest.from_(table_name)

    @overload
    def rpc(
        self,
        fn: str,
        head: Literal[False],
        params: Dict[str, str] | None = None,
        count: CountMethod | None = None,
        get: bool = False,
    ) -> RPCFilterRequestBuilder[AsyncHttpIO]: ...

    @overload
    def rpc(
        self,
        fn: str,
        head: Literal[True],
        params: Dict[str, str] | None = None,
        count: CountMethod | None = None,
        get: bool = False,
    ) -> RPCCountRequestBuilder[AsyncHttpIO]: ...

    @overload
    def rpc(
        self,
        fn: str,
    ) -> RPCFilterRequestBuilder[AsyncHttpIO]: ...

    def rpc(
        self,
        fn: str,
        head: bool = False,
        params: Dict[str, str] | None = None,
        count: CountMethod | None = None,
        get: bool = False,
    ) -> RPCFilterRequestBuilder[AsyncHttpIO] | RPCCountRequestBuilder[AsyncHttpIO]:
        """Performs a stored procedure call.

        Parameters
        ----------
        fn : callable
            The stored procedure call to be executed.
        params : dict of any
            Parameters passed into the stored procedure call.
        count: The method to use to get the count of rows returned.
        head: When set to `true`, `data` will not be returned. Useful if you only need the count.
        get: When set to `true`, the function will be called with read-only access mode.

        Returns
        -------
        AsyncFilterRequestBuilder
            Returns a filter builder. This lets you apply filters on the response
            of an RPC.
        """
        if params is None:
            params = {}
        return self.postgrest.rpc(fn, params, count=count, head=head, get=get)

    @property
    def auth(self) -> AsyncSupabaseAuthClient:
        return self._init_supabase_auth_client(
            auth_url=str(self.auth_url),
            client_options=self.options,
            http_session=self.http_session,
        )

    @property
    def postgrest(self) -> AsyncPostgrestClient:
        return self._init_postgrest_client(
            rest_url=str(self.rest_url),
            headers=self.options.headers,
            schema=self.options.schema,
            http_session=self.http_session,
        )

    @property
    def storage(self) -> AsyncStorageClient:
        return self._init_storage_client(
            storage_url=str(self.storage_url),
            headers=self.options.headers,
            http_session=self.http_session,
        )

    @property
    def functions(self) -> AsyncFunctionsClient:
        return AsyncFunctionsClient(
            url=str(self.functions_url),
            headers=self.options.headers,
        )

    async def realtime_get_token_callback(self) -> str | None:
        return self.auth_access_token

    @property
    def realtime(
        self,
    ) -> connect_once:
        """Private method for creating an instance of the realtime-py client."""
        return connect_once(
            str(self.realtime_url),
            token_callback=self.realtime_get_token_callback,
            **(self.options.realtime or {}),
        )

    @staticmethod
    def _init_storage_client(
        storage_url: str,
        headers: Dict[str, str],
        http_session: AsyncHttpSession,
    ) -> AsyncStorageClient:
        return AsyncStorageClient(
            url=storage_url,
            headers=headers,
            http_session=http_session,
        )

    @staticmethod
    def _init_supabase_auth_client(
        auth_url: str,
        client_options: ClientOptions,
        http_session: AsyncHttpSession,
    ) -> AsyncSupabaseAuthClient:
        """Creates a wrapped instance of the GoTrue Client."""
        return AsyncSupabaseAuthClient(
            url=auth_url,
            auto_refresh_token=client_options.auto_refresh_token,
            persist_session=client_options.persist_session,
            storage=client_options.storage,
            headers=client_options.headers,
            flow_type=client_options.flow_type,
            http_session=http_session,
        )

    @staticmethod
    def _init_postgrest_client(
        rest_url: str,
        headers: Dict[str, str],
        schema: str,
        http_session: AsyncHttpSession,
    ) -> AsyncPostgrestClient:
        """Private helper for creating an instance of the Postgrest client."""
        return AsyncPostgrestClient(
            rest_url,
            headers=headers,
            schema=schema,
            http_session=http_session,
        )

    def _create_auth_header(self, token: str) -> str:
        return f"Bearer {token}"

    def _get_auth_headers(self, authorization: str | None = None) -> Dict[str, str]:
        if authorization is None:
            authorization = self.options.headers.get(
                "Authorization", self._create_auth_header(self.supabase_key)
            )

        """Helper method to get auth headers."""
        return {
            "apiKey": self.supabase_key,
            "Authorization": authorization,
        }

    def _listen_to_auth_events(
        self, event: AuthChangeEvent, session: Session | None
    ) -> None:
        access_token = self.supabase_key
        if event in ["SIGNED_IN", "TOKEN_REFRESHED", "SIGNED_OUT"]:
            # reset postgrest and storage instance on event change
            self._postgrest = None
            self._storage = None
            self._functions = None
            access_token = session.access_token if session else self.supabase_key
        auth_header = self._create_auth_header(access_token)
        self.options.headers["Authorization"] = auth_header
        self.auth.default_headers = self.auth.default_headers.override(
            "Authorization", auth_header
        )
        self.auth_access_token = access_token
