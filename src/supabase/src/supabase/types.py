from dataclasses import dataclass

from realtime.types import (
    DEFAULT_HEARTBEAT_INTERVAL,
    DEFAULT_HEARTBEAT_TIMEOUT,
    validate_heartbeat,
)
from supabase_auth import AsyncSupportedStorage, AuthFlowType, SyncSupportedStorage
from supabase_auth.constants import STORAGE_KEY
from supabase_utils.http.request import validate_request_timeout
from supabase_utils.http.retry import RetryPolicy


@dataclass(frozen=True)
class RealtimeClientOptions:
    """Options for the realtime connections opened by `AsyncClient.realtime`."""

    heartbeat_interval: float = DEFAULT_HEARTBEAT_INTERVAL
    """Seconds between heartbeats. Must be positive."""

    heartbeat_timeout: float = DEFAULT_HEARTBEAT_TIMEOUT
    """Seconds to wait for a heartbeat reply before the connection is considered lost. Must be positive."""

    def __post_init__(self) -> None:
        validate_heartbeat(self.heartbeat_interval, self.heartbeat_timeout)


@dataclass(frozen=True, kw_only=True)
class _ServiceClientOptions:
    """Options shared by the database, auth, storage and edge functions clients."""

    request_timeout: float | None = None
    """Seconds a request to the service may go without progress before it fails with `RequestTimeoutError`. Overrides the `request_timeout` argument of the client when set."""

    retry: RetryPolicy | None = None
    """How requests to the service that failed in a way worth repeating are retried. Overrides the `retry` argument of the client when set."""

    def __post_init__(self) -> None:
        validate_request_timeout(self.request_timeout)


@dataclass(frozen=True, kw_only=True)
class PostgrestClientOptions(_ServiceClientOptions):
    """Options for the database client. Use `request_timeout()` and `retry()` on a query to override its timeout and retries for that query."""

    schema: str = "public"
    """The Postgres schema which your tables belong to. Must be on the list of exposed schemas in Supabase."""


@dataclass(frozen=True, kw_only=True)
class AuthClientOptions[Storage: (AsyncSupportedStorage, SyncSupportedStorage)](
    _ServiceClientOptions
):
    """Options for the auth client.

    `AsyncClient` takes an `AsyncSupportedStorage` as `session_storage` and
    `Client` a `SyncSupportedStorage`.
    """

    auto_refresh_token: bool = True
    """Automatically refreshes the token for logged in users."""

    session_storage: Storage | None = None
    """Where the logged in session is stored. None (the default) keeps it in memory."""

    storage_key: str = STORAGE_KEY
    """The key the session is stored under in `session_storage`. Give clients that share a `session_storage` different keys so they do not overwrite each other's session."""

    flow_type: AuthFlowType = "pkce"
    """The flow type to use for authentication."""


@dataclass(frozen=True, kw_only=True)
class StorageClientOptions(_ServiceClientOptions):
    """Options for the storage client. The default `RetryPolicy` retries GET and HEAD requests only, so an upload is not retried unless `retry` lists its method."""


@dataclass(frozen=True, kw_only=True)
class FunctionsClientOptions(_ServiceClientOptions):
    """Options for the edge functions client. Use the `request_timeout` and `retry` arguments of `invoke()` to override its timeout and retries for one invocation."""
