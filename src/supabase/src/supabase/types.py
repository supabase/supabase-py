from dataclasses import dataclass

from realtime.types import (
    DEFAULT_HEARTBEAT_INTERVAL,
    DEFAULT_HEARTBEAT_TIMEOUT,
    validate_heartbeat,
)
from supabase_utils.http.request import validate_request_timeout


@dataclass(frozen=True)
class RealtimeClientOptions:
    """Options for the realtime connections opened by `AsyncClient.realtime`."""

    heartbeat_interval: float = DEFAULT_HEARTBEAT_INTERVAL
    """Seconds between heartbeats. Must be positive."""

    heartbeat_timeout: float = DEFAULT_HEARTBEAT_TIMEOUT
    """Seconds to wait for a heartbeat reply before the connection is considered lost. Must be positive."""

    def __post_init__(self) -> None:
        validate_heartbeat(self.heartbeat_interval, self.heartbeat_timeout)


@dataclass(frozen=True)
class _ServiceClientOptions:
    """Options shared by the database, auth, storage and edge functions clients."""

    request_timeout: float | None = None
    """Seconds a request to the service may go without progress before it fails with `RequestTimeoutError`. Overrides `request_timeout` of the client options when set."""

    def __post_init__(self) -> None:
        validate_request_timeout(self.request_timeout)


@dataclass(frozen=True)
class PostgrestClientOptions(_ServiceClientOptions):
    """Options for the database client. Use `request_timeout()` on a query to override its timeout for that query."""


@dataclass(frozen=True)
class AuthClientOptions(_ServiceClientOptions):
    """Options for the auth client."""


@dataclass(frozen=True)
class StorageClientOptions(_ServiceClientOptions):
    """Options for the storage client."""


@dataclass(frozen=True)
class FunctionsClientOptions(_ServiceClientOptions):
    """Options for the edge functions client. Use the `request_timeout` argument of `invoke()` to override its timeout for one invocation."""
