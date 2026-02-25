from dataclasses import dataclass, field
from typing import Dict, Optional, Union

from httpx import AsyncClient as AsyncHttpxClient
from httpx import Client as SyncHttpxClient
from httpx import Timeout
from postgrest.constants import DEFAULT_POSTGREST_CLIENT_TIMEOUT
from storage3.constants import DEFAULT_TIMEOUT as DEFAULT_STORAGE_CLIENT_TIMEOUT
from supabase_auth import (
    AsyncMemoryStorage,
    AsyncSupportedStorage,
    AuthFlowType,
    SyncMemoryStorage,
    SyncSupportedStorage,
)
from supabase_functions.utils import DEFAULT_FUNCTION_CLIENT_TIMEOUT

from supabase.types import RealtimeClientOptions

from ..version import __version__

DEFAULT_HEADERS = {"X-Client-Info": f"supabase-py/{__version__}"}


@dataclass
class ClientOptions:
    schema: str = "public"
    """
    The Postgres schema which your tables belong to.
    Must be on the list of exposed schemas in Supabase. Defaults to 'public'.
    """

    headers: Dict[str, str] = field(default_factory=DEFAULT_HEADERS.copy)
    """Optional headers for initializing the client."""

    auto_refresh_token: bool = True
    """Automatically refreshes the token for logged in users."""

    persist_session: bool = True
    """Whether to persist a logged in session to storage."""

    realtime: Optional[RealtimeClientOptions] = None
    """Options passed to the realtime-py instance"""

    postgrest_client_timeout: Union[int, float, Timeout] = (
        DEFAULT_POSTGREST_CLIENT_TIMEOUT
    )
    """Timeout passed to the SyncPostgrestClient instance."""

    storage_client_timeout: int = DEFAULT_STORAGE_CLIENT_TIMEOUT
    """Timeout passed to the SyncStorageClient instance"""

    function_client_timeout: int = DEFAULT_FUNCTION_CLIENT_TIMEOUT
    """Timeout passed to the SyncFunctionsClient instance."""

    flow_type: AuthFlowType = "pkce"
    """flow type to use for authentication"""


@dataclass
class AsyncClientOptions(ClientOptions):
    storage: AsyncSupportedStorage = field(default_factory=AsyncMemoryStorage)
    """A storage provider. Used to store the logged in session."""

    httpx_client: Optional[AsyncHttpxClient] = None
    """httpx client instance to be used by the PostgREST, functions, auth and storage clients."""

    def replace(
        self,
        schema: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        auto_refresh_token: Optional[bool] = None,
        persist_session: Optional[bool] = None,
        storage: Optional[AsyncSupportedStorage] = None,
        realtime: Optional[RealtimeClientOptions] = None,
        httpx_client: Optional[AsyncHttpxClient] = None,
        postgrest_client_timeout: Optional[Union[int, float, Timeout]] = None,
        storage_client_timeout: Optional[int] = None,
        function_client_timeout: Optional[int] = None,
        flow_type: Optional[AuthFlowType] = None,
    ) -> "AsyncClientOptions":
        """Create a new SupabaseClientOptions with changes"""
        client_options = AsyncClientOptions()
        client_options.schema = self.schema if schema is None else schema
        selected_headers = self.headers if headers is None else headers
        client_options.headers = selected_headers.copy()
        client_options.auto_refresh_token = (
            self.auto_refresh_token
            if auto_refresh_token is None
            else auto_refresh_token
        )
        client_options.persist_session = (
            self.persist_session if persist_session is None else persist_session
        )
        client_options.storage = self.storage if storage is None else storage
        client_options.realtime = self.realtime if realtime is None else realtime
        client_options.httpx_client = (
            self.httpx_client if httpx_client is None else httpx_client
        )
        client_options.postgrest_client_timeout = (
            self.postgrest_client_timeout
            if postgrest_client_timeout is None
            else postgrest_client_timeout
        )
        client_options.storage_client_timeout = (
            self.storage_client_timeout
            if storage_client_timeout is None
            else storage_client_timeout
        )
        client_options.function_client_timeout = (
            self.function_client_timeout
            if function_client_timeout is None
            else function_client_timeout
        )
        client_options.flow_type = self.flow_type if flow_type is None else flow_type
        return client_options


@dataclass
class SyncClientOptions(ClientOptions):
    storage: SyncSupportedStorage = field(default_factory=SyncMemoryStorage)
    """A storage provider. Used to store the logged in session."""
    httpx_client: Optional[SyncHttpxClient] = None
    """httpx client instance to be used by the PostgREST, functions, auth and storage clients."""

    def replace(
        self,
        schema: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        auto_refresh_token: Optional[bool] = None,
        persist_session: Optional[bool] = None,
        storage: Optional[SyncSupportedStorage] = None,
        realtime: Optional[RealtimeClientOptions] = None,
        httpx_client: Optional[SyncHttpxClient] = None,
        postgrest_client_timeout: Optional[Union[int, float, Timeout]] = None,
        storage_client_timeout: Optional[int] = None,
        function_client_timeout: Optional[int] = None,
        flow_type: Optional[AuthFlowType] = None,
    ) -> "SyncClientOptions":
        """Create a new SupabaseClientOptions with changes"""
        client_options = SyncClientOptions()
        client_options.schema = self.schema if schema is None else schema
        selected_headers = self.headers if headers is None else headers
        client_options.headers = selected_headers.copy()
        client_options.auto_refresh_token = (
            self.auto_refresh_token
            if auto_refresh_token is None
            else auto_refresh_token
        )
        client_options.persist_session = (
            self.persist_session if persist_session is None else persist_session
        )
        client_options.storage = self.storage if storage is None else storage
        client_options.realtime = self.realtime if realtime is None else realtime
        client_options.httpx_client = (
            self.httpx_client if httpx_client is None else httpx_client
        )
        client_options.postgrest_client_timeout = (
            self.postgrest_client_timeout
            if postgrest_client_timeout is None
            else postgrest_client_timeout
        )
        client_options.storage_client_timeout = (
            self.storage_client_timeout
            if storage_client_timeout is None
            else storage_client_timeout
        )
        client_options.function_client_timeout = (
            self.function_client_timeout
            if function_client_timeout is None
            else function_client_timeout
        )
        client_options.flow_type = self.flow_type if flow_type is None else flow_type
        return client_options
