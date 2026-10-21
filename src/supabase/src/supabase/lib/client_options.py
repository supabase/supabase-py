import dataclasses
import platform
from dataclasses import dataclass, field
from typing import Any, Dict, TypeVar

from supabase_auth import (
    AsyncMemoryStorage,
    AsyncSupportedStorage,
    AuthFlowType,
    SyncMemoryStorage,
    SyncSupportedStorage,
)

from supabase.types import RealtimeClientOptions

from ..version import __version__

DEFAULT_HEADERS = {
    "X-Client-Info": (
        f"supabase-py/{__version__}"
        f"; platform={platform.system()}"
        f"; platform-version={platform.release()}"
        f"; runtime=python"
        f"; runtime-version={platform.python_version()}"
    )
}


_ClientOptions = TypeVar("_ClientOptions", bound="ClientOptions")


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

    realtime: RealtimeClientOptions | None = None
    """Options passed to the realtime-py instance"""

    flow_type: AuthFlowType = "pkce"
    """flow type to use for authentication"""

    def _replace(self: _ClientOptions, **changes: Any) -> _ClientOptions:
        return dataclasses.replace(
            self, **{key: value for key, value in changes.items() if value is not None}
        )


@dataclass
class AsyncClientOptions(ClientOptions):
    storage: AsyncSupportedStorage = field(default_factory=AsyncMemoryStorage)
    """A storage provider. Used to store the logged in session."""

    def replace(
        self,
        schema: str | None = None,
        headers: Dict[str, str] | None = None,
        auto_refresh_token: bool | None = None,
        persist_session: bool | None = None,
        storage: AsyncSupportedStorage | None = None,
        realtime: RealtimeClientOptions | None = None,
        flow_type: AuthFlowType | None = None,
    ) -> "AsyncClientOptions":
        """Create a new SupabaseClientOptions with changes"""
        return self._replace(
            schema=schema,
            headers=headers,
            auto_refresh_token=auto_refresh_token,
            persist_session=persist_session,
            storage=storage,
            realtime=realtime,
            flow_type=flow_type,
        )


@dataclass
class SyncClientOptions(ClientOptions):
    storage: SyncSupportedStorage = field(default_factory=SyncMemoryStorage)
    """A storage provider. Used to store the logged in session."""

    def replace(
        self,
        schema: str | None = None,
        headers: Dict[str, str] | None = None,
        auto_refresh_token: bool | None = None,
        persist_session: bool | None = None,
        storage: SyncSupportedStorage | None = None,
        realtime: RealtimeClientOptions | None = None,
        flow_type: AuthFlowType | None = None,
    ) -> "SyncClientOptions":
        """Create a new SupabaseClientOptions with changes"""
        return self._replace(
            schema=schema,
            headers=headers,
            auto_refresh_token=auto_refresh_token,
            persist_session=persist_session,
            storage=storage,
            realtime=realtime,
            flow_type=flow_type,
        )
