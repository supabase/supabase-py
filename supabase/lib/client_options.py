from dataclasses import dataclass, field
from typing import Dict, Optional, Union

from gotrue import (
    AsyncMemoryStorage,
    AsyncSupportedStorage,
    AuthFlowType,
    SyncMemoryStorage,
    SyncSupportedStorage,
)
from httpx import AsyncClient as AsyncHttpxClient
from httpx import Client as SyncHttpxClient
from httpx import Timeout
from postgrest.constants import DEFAULT_POSTGREST_CLIENT_TIMEOUT
from storage3.constants import DEFAULT_TIMEOUT as DEFAULT_STORAGE_CLIENT_TIMEOUT
from supafunc.utils import DEFAULT_FUNCTION_CLIENT_TIMEOUT

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

    storage: SyncSupportedStorage = field(default_factory=SyncMemoryStorage)
    """A storage provider. Used to store the logged in session."""

    realtime: Optional[RealtimeClientOptions] = None
    """Options passed to the realtime-py instance"""

    httpx_client: Optional[SyncHttpxClient] = None
    """httpx client instance to be used by the PostgREST, functions, auth and storage clients."""

    postgrest_client_timeout: Union[int, float, Timeout] = (
        DEFAULT_POSTGREST_CLIENT_TIMEOUT
    )
    """Timeout passed to the SyncPostgrestClient instance."""

    storage_client_timeout: Union[int, float, Timeout] = DEFAULT_STORAGE_CLIENT_TIMEOUT
    """Timeout passed to the SyncStorageClient instance"""

    function_client_timeout: Union[int, float, Timeout] = (
        DEFAULT_FUNCTION_CLIENT_TIMEOUT
    )
    """Timeout passed to the SyncFunctionsClient instance."""

    flow_type: AuthFlowType = "pkce"
    """flow type to use for authentication"""

    def replace(
        self,
        schema: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        auto_refresh_token: Optional[bool] = None,
        persist_session: Optional[bool] = None,
        storage: Optional[SyncSupportedStorage] = None,
        realtime: Optional[RealtimeClientOptions] = None,
        httpx_client: Optional[SyncHttpxClient] = None,
        postgrest_client_timeout: Union[
            int, float, Timeout
        ] = DEFAULT_POSTGREST_CLIENT_TIMEOUT,
        storage_client_timeout: Union[
            int, float, Timeout
        ] = DEFAULT_STORAGE_CLIENT_TIMEOUT,
        flow_type: Optional[AuthFlowType] = None,
    ) -> "ClientOptions":
        """Create a new SupabaseClientOptions with changes"""
        client_options = ClientOptions()
        client_options.schema = schema or self.schema
        client_options.headers = headers or self.headers
        client_options.auto_refresh_token = (
            auto_refresh_token or self.auto_refresh_token
        )
        client_options.persist_session = persist_session or self.persist_session
        client_options.storage = storage or self.storage
        client_options.realtime = realtime or self.realtime
        client_options.httpx_client = httpx_client or self.httpx_client
        client_options.postgrest_client_timeout = (
            postgrest_client_timeout or self.postgrest_client_timeout
        )
        client_options.storage_client_timeout = (
            storage_client_timeout or self.storage_client_timeout
        )
        client_options.flow_type = flow_type or self.flow_type
        return client_options


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
        postgrest_client_timeout: Union[
            int, float, Timeout
        ] = DEFAULT_POSTGREST_CLIENT_TIMEOUT,
        storage_client_timeout: Union[
            int, float, Timeout
        ] = DEFAULT_STORAGE_CLIENT_TIMEOUT,
        flow_type: Optional[AuthFlowType] = None,
    ) -> "AsyncClientOptions":
        """Create a new SupabaseClientOptions with changes"""
        client_options = AsyncClientOptions()
        client_options.schema = schema or self.schema
        client_options.headers = headers or self.headers
        client_options.auto_refresh_token = (
            auto_refresh_token or self.auto_refresh_token
        )
        client_options.persist_session = persist_session or self.persist_session
        client_options.storage = storage or self.storage
        client_options.realtime = realtime or self.realtime
        client_options.httpx_client = httpx_client or self.httpx_client
        client_options.postgrest_client_timeout = (
            postgrest_client_timeout or self.postgrest_client_timeout
        )
        client_options.storage_client_timeout = (
            storage_client_timeout or self.storage_client_timeout
        )
        client_options.flow_type = flow_type or self.flow_type
        return client_options


@dataclass
class SyncClientOptions(ClientOptions):
    def replace(
        self,
        schema: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        auto_refresh_token: Optional[bool] = None,
        persist_session: Optional[bool] = None,
        storage: Optional[SyncSupportedStorage] = None,
        realtime: Optional[RealtimeClientOptions] = None,
        httpx_client: Optional[SyncHttpxClient] = None,
        postgrest_client_timeout: Union[
            int, float, Timeout
        ] = DEFAULT_POSTGREST_CLIENT_TIMEOUT,
        storage_client_timeout: Union[
            int, float, Timeout
        ] = DEFAULT_STORAGE_CLIENT_TIMEOUT,
        flow_type: Optional[AuthFlowType] = None,
    ) -> "SyncClientOptions":
        """Create a new SupabaseClientOptions with changes"""
        client_options = SyncClientOptions()
        client_options.schema = schema or self.schema
        client_options.headers = headers or self.headers
        client_options.auto_refresh_token = (
            auto_refresh_token or self.auto_refresh_token
        )
        client_options.persist_session = persist_session or self.persist_session
        client_options.storage = storage or self.storage
        client_options.realtime = realtime or self.realtime
        client_options.httpx_client = httpx_client or self.httpx_client
        client_options.postgrest_client_timeout = (
            postgrest_client_timeout or self.postgrest_client_timeout
        )
        client_options.storage_client_timeout = (
            storage_client_timeout or self.storage_client_timeout
        )
        client_options.flow_type = flow_type or self.flow_type
        return client_options
