import copy
import dataclasses
from typing import Any, Callable, Dict, Optional

from supabase import __version__

DEFAULT_HEADERS = {"X-Client-Info": f"supabase-py/{__version__}"}


@dataclasses.dataclass
class ClientOptions:
    schema: str = "public"
    """
    The Postgres schema which your tables belong to.
    Must be on the list of exposed schemas in Supabase. Defaults to 'public'.
    """

    headers: Dict[str, str] = dataclasses.field(default_factory=DEFAULT_HEADERS.copy)
    """Optional headers for initializing the client."""

    auto_refresh_token: bool = True
    """Automatically refreshes the token for logged in users."""

    persist_session: bool = True
    """Whether to persist a logged in session to storage."""

    detect_session_in_url: bool = True
    """Detect a session from the URL. Used for OAuth login callbacks."""

    local_storage: Dict[str, Any] = dataclasses.field(default_factory=lambda: {})
    """A storage provider. Used to store the logged in session."""

    """Options passed to the realtime-py instance"""
    realtime: Optional[Dict[str, Any]] = None

    fetch: Optional[Callable] = None
    """A custom `fetch` implementation."""

    def replace(
        self,
        schema: Optional[str] = None,
        headers: Optional[Dict[str, str]] = None,
        auto_refresh_token: Optional[bool] = None,
        persist_session: Optional[bool] = None,
        detect_session_in_url: Optional[bool] = None,
        local_storage: Optional[Dict[str, Any]] = None,
        realtime: Optional[Dict[str, Any]] = None,
        fetch: Optional[Callable] = None,
    ) -> "ClientOptions":
        """Create a new SupabaseClientOptions with changes"""
        changes = {
            key: value
            for key, value in locals().items()
            if key != "self" and value is not None
        }
        client_options = dataclasses.replace(self, **changes)
        client_options = copy.deepcopy(client_options)
        return client_options
