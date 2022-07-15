from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional

from gotrue import SyncMemoryStorage, SyncSupportedStorage

from supabase import __version__

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

    local_storage: SyncSupportedStorage = field(default_factory=SyncMemoryStorage)
    """A storage provider. Used to store the logged in session."""

    realtime: Optional[Dict[str, Any]] = None
    """Options passed to the realtime-py instance"""

    fetch: Optional[Callable] = None
    """A custom `fetch` implementation."""

    def replace(
        self,
        schema: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        auto_refresh_token: Optional[bool] = None,
        persist_session: Optional[bool] = None,
        local_storage: Optional[SyncSupportedStorage] = None,
        realtime: Optional[Dict[str, Any]] = None,
        fetch: Optional[Callable] = None,
    ) -> "ClientOptions":
        """Create a new SupabaseClientOptions with changes"""
        client_options = ClientOptions()
        client_options.schema = schema or self.schema
        client_options.headers = headers or self.headers
        client_options.auto_refresh_token = (
            auto_refresh_token or self.auto_refresh_token
        )
        client_options.persist_session = persist_session or self.persist_session
        client_options.local_storage = local_storage or self.local_storage
        client_options.realtime = realtime or self.realtime
        client_options.fetch = fetch or self.fetch
        return client_options
