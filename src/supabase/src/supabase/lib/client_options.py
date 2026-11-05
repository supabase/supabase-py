import dataclasses
import platform
from collections.abc import Mapping
from dataclasses import dataclass, field
from typing import Self

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


@dataclass(frozen=True)
class _ClientOptionsBase[Storage: (AsyncSupportedStorage, SyncSupportedStorage)]:
    schema: str = "public"
    """
    The Postgres schema which your tables belong to.
    Must be on the list of exposed schemas in Supabase. Defaults to 'public'.
    """

    headers: Mapping[str, str] = field(default_factory=DEFAULT_HEADERS.copy)
    """Optional headers for initializing the client."""

    auto_refresh_token: bool = True
    """Automatically refreshes the token for logged in users."""

    persist_session: bool = True
    """Whether to persist a logged in session to storage."""

    realtime: RealtimeClientOptions = field(default_factory=RealtimeClientOptions)
    """Options for the realtime connections."""

    flow_type: AuthFlowType = "pkce"
    """flow type to use for authentication"""

    def __post_init__(self) -> None:
        object.__setattr__(self, "headers", dict(self.headers))

    def replace(
        self,
        *,
        schema: str | None = None,
        headers: Mapping[str, str] | None = None,
        auto_refresh_token: bool | None = None,
        persist_session: bool | None = None,
        storage: Storage | None = None,
        realtime: RealtimeClientOptions | None = None,
        flow_type: AuthFlowType | None = None,
    ) -> Self:
        """Create a copy with the given options changed. Options left as None keep their value."""
        changes = {
            "schema": schema,
            "headers": headers,
            "auto_refresh_token": auto_refresh_token,
            "persist_session": persist_session,
            "storage": storage,
            "realtime": realtime,
            "flow_type": flow_type,
        }
        return dataclasses.replace(
            self, **{key: value for key, value in changes.items() if value is not None}
        )


@dataclass(frozen=True)
class AsyncClientOptions(_ClientOptionsBase[AsyncSupportedStorage]):
    """Options for `AsyncClient`."""

    storage: AsyncSupportedStorage = field(default_factory=AsyncMemoryStorage)
    """A storage provider. Used to store the logged in session."""


@dataclass(frozen=True)
class ClientOptions(_ClientOptionsBase[SyncSupportedStorage]):
    """Options for the sync `Client`."""

    storage: SyncSupportedStorage = field(default_factory=SyncMemoryStorage)
    """A storage provider. Used to store the logged in session."""
