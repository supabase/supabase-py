import dataclasses
import platform
from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import Enum
from typing import Literal, Self

from supabase_auth import (
    AsyncMemoryStorage,
    AsyncSupportedStorage,
    AuthFlowType,
    SyncMemoryStorage,
    SyncSupportedStorage,
)
from supabase_utils.http.request import validate_request_timeout

from supabase.types import (
    AuthClientOptions,
    FunctionsClientOptions,
    PostgrestClientOptions,
    RealtimeClientOptions,
    StorageClientOptions,
)

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


class _Unchanged(Enum):
    UNCHANGED = "unchanged"


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

    request_timeout: float | None = None
    """
    Seconds a request to the database, auth, storage or edge functions may go
    without progress before it fails with `RequestTimeoutError`. It limits how
    long the connection may stall, not the whole request, so a large transfer
    that keeps moving is not cut short. None (the default) leaves the timeout
    to the HTTP client. The `request_timeout` of a service's options overrides
    it for that service.
    """

    postgrest_options: PostgrestClientOptions = field(
        default_factory=PostgrestClientOptions
    )
    """Options for the database client."""

    auth_options: AuthClientOptions = field(default_factory=AuthClientOptions)
    """Options for the auth client."""

    storage_options: StorageClientOptions = field(default_factory=StorageClientOptions)
    """Options for the storage client."""

    functions_options: FunctionsClientOptions = field(
        default_factory=FunctionsClientOptions
    )
    """Options for the edge functions client."""

    def __post_init__(self) -> None:
        validate_request_timeout(self.request_timeout)
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
        request_timeout: float | None | Literal[_Unchanged.UNCHANGED] = (
            _Unchanged.UNCHANGED
        ),
        postgrest_options: PostgrestClientOptions | None = None,
        auth_options: AuthClientOptions | None = None,
        storage_options: StorageClientOptions | None = None,
        functions_options: FunctionsClientOptions | None = None,
    ) -> Self:
        """Create a copy with the given options changed.

        Options left as None keep their value, except `request_timeout`, where
        None leaves the timeout to the HTTP client. Leave `request_timeout` out
        to keep its value.
        """
        changes = {
            "schema": schema,
            "headers": headers,
            "auto_refresh_token": auto_refresh_token,
            "persist_session": persist_session,
            "storage": storage,
            "realtime": realtime,
            "flow_type": flow_type,
            "postgrest_options": postgrest_options,
            "auth_options": auth_options,
            "storage_options": storage_options,
            "functions_options": functions_options,
        }
        updated = dataclasses.replace(
            self, **{key: value for key, value in changes.items() if value is not None}
        )
        if request_timeout is _Unchanged.UNCHANGED:
            return updated
        return dataclasses.replace(updated, request_timeout=request_timeout)


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
