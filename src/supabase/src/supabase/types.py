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
class PostgrestClientOptions:
    """Options for the database client."""

    request_timeout: float | None = None
    """Seconds a request to the database may go without progress before it fails with `RequestTimeoutError`. Overrides `request_timeout` of the client options when set. Use `request_timeout()` on a query to override it for that query."""

    def __post_init__(self) -> None:
        validate_request_timeout(self.request_timeout)


@dataclass(frozen=True)
class AuthClientOptions:
    """Options for the auth client."""

    request_timeout: float | None = None
    """Seconds a request to auth may go without progress before it fails with `RequestTimeoutError`. Overrides `request_timeout` of the client options when set."""

    def __post_init__(self) -> None:
        validate_request_timeout(self.request_timeout)


@dataclass(frozen=True)
class StorageClientOptions:
    """Options for the storage client."""

    request_timeout: float | None = None
    """Seconds a request to storage may go without progress before it fails with `RequestTimeoutError`. Overrides `request_timeout` of the client options when set."""

    def __post_init__(self) -> None:
        validate_request_timeout(self.request_timeout)


@dataclass(frozen=True)
class FunctionsClientOptions:
    """Options for the edge functions client."""

    request_timeout: float | None = None
    """Seconds a request to edge functions may go without progress before it fails with `RequestTimeoutError`. Overrides `request_timeout` of the client options when set. Use the `request_timeout` argument of `invoke()` to override it for one invocation."""

    def __post_init__(self) -> None:
        validate_request_timeout(self.request_timeout)
