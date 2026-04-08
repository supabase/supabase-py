import copy
import re
from types import TracebackType
from typing import Dict, Literal, overload

from postgrest import SyncPostgrestClient
from postgrest.request_builder import (
    RequestBuilder,
    RPCCountRequestBuilder,
    RPCFilterRequestBuilder,
)
from postgrest.types import CountMethod
from storage3 import SyncStorageClient
from supabase_auth import SyncMemoryStorage, SyncSupabaseAuthClient
from supabase_auth.types import AuthChangeEvent, Session
from supabase_functions import SyncFunctionsClient
from supabase_utils.http.io import HttpSession, SyncHttpIO
from yarl import URL

from ..lib.client_options import SyncClientOptions as ClientOptions


# Create an exception class when user does not provide a valid url or key.
class SupabaseException(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class Client:
    """Supabase client class."""

    def __init__(
        self,
        supabase_url: str,
        supabase_key: str,
        http_session: HttpSession,
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

        # Check if the url and key are valid
        if not re.match(r"^(https?)://.+", supabase_url):
            raise SupabaseException("Invalid URL")

        if options is None:
            options = ClientOptions(storage=SyncMemoryStorage())

        self.http_session: HttpSession = http_session

        self.supabase_url = (
            URL(supabase_url) if supabase_url.endswith("/") else URL(supabase_url + "/")
        )
        self.supabase_key = supabase_key
        self.options = copy.copy(options)
        self.options.headers = {
            **options.headers,
            **self._get_auth_headers(),
        }

        self.rest_url = self.supabase_url.joinpath("rest", "v1")
        self.auth_url = self.supabase_url.joinpath("auth", "v1")
        self.storage_url = self.supabase_url.joinpath("storage", "v1", "")
        self.functions_url = self.supabase_url.joinpath("functions", "v1")

        # Instantiate clients.
        self.auth = self._init_supabase_auth_client(
            auth_url=str(self.auth_url),
            client_options=self.options,
            http_session=self.http_session,
        )
        self._postgrest: SyncPostgrestClient | None = None
        self._storage: SyncStorageClient | None = None
        self._functions: SyncFunctionsClient | None = None
        self.auth.on_auth_state_change(self._listen_to_auth_events)

    @classmethod
    def create(
        cls,
        supabase_url: str,
        supabase_key: str,
        http_session: HttpSession,
        options: ClientOptions | None = None,
    ) -> "Client":
        auth_header = options.headers.get("Authorization") if options else None
        client = cls(supabase_url, supabase_key, http_session, options)

        if auth_header is None:
            try:
                session = client.auth.get_session()
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

    def __enter__(self) -> "Client":
        return self

    def __exit__(
        self,
        exc_type: type[Exception] | None,
        exc: Exception | None,
        tb: TracebackType | None,
    ) -> None:
        self.http_session.__exit__(exc_type, exc, tb)

    def table(self, table_name: str) -> RequestBuilder[SyncHttpIO]:
        """Perform a table operation.

        Note that the supabase client uses the `from` method, but in Python,
        this is a reserved keyword, so we have elected to use the name `table`.
        Alternatively you can use the `.from_()` method.
        """
        return self.from_(table_name)

    def schema(self, schema: str) -> SyncPostgrestClient:
        """Select a schema to query or perform an function (rpc) call.

        The schema needs to be on the list of exposed schemas inside Supabase.
        """
        return self.postgrest.schema(schema)

    def from_(self, table_name: str) -> RequestBuilder[SyncHttpIO]:
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
    ) -> RPCFilterRequestBuilder[SyncHttpIO]: ...

    @overload
    def rpc(
        self,
        fn: str,
        head: Literal[True],
        params: Dict[str, str] | None = None,
        count: CountMethod | None = None,
        get: bool = False,
    ) -> RPCCountRequestBuilder[SyncHttpIO]: ...

    @overload
    def rpc(
        self,
        fn: str,
    ) -> RPCCountRequestBuilder[SyncHttpIO]: ...

    def rpc(
        self,
        fn: str,
        head: bool = False,
        params: dict[str, str] | None = None,
        count: CountMethod | None = None,
        get: bool = False,
    ) -> RPCFilterRequestBuilder[SyncHttpIO] | RPCCountRequestBuilder[SyncHttpIO]:
        if params is None:
            params = {}
        return self.postgrest.rpc(fn, params, head=head, count=count, get=get)

    @property
    def postgrest(self) -> SyncPostgrestClient:
        if self._postgrest is None:
            self._postgrest = self._init_postgrest_client(
                rest_url=str(self.rest_url),
                headers=self.options.headers,
                schema=self.options.schema,
                http_session=self.http_session,
            )

        return self._postgrest

    @property
    def storage(self) -> SyncStorageClient:
        if self._storage is None:
            self._storage = self._init_storage_client(
                storage_url=str(self.storage_url),
                headers=self.options.headers,
                http_session=self.http_session,
            )
        return self._storage

    @property
    def functions(self) -> SyncFunctionsClient:
        if self._functions is None:
            self._functions = SyncFunctionsClient(
                url=str(self.functions_url),
                headers=self.options.headers,
            )
        return self._functions

    @staticmethod
    def _init_storage_client(
        storage_url: str,
        headers: Dict[str, str],
        http_session: HttpSession,
    ) -> SyncStorageClient:
        return SyncStorageClient(
            url=storage_url,
            headers=headers,
            http_session=http_session,
        )

    @staticmethod
    def _init_supabase_auth_client(
        auth_url: str,
        client_options: ClientOptions,
        http_session: HttpSession,
    ) -> SyncSupabaseAuthClient:
        """Creates a wrapped instance of the GoTrue Client."""
        return SyncSupabaseAuthClient(
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
        http_session: HttpSession,
    ) -> SyncPostgrestClient:
        """Private helper for creating an instance of the Postgrest client."""
        return SyncPostgrestClient(
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
