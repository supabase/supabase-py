from dataclasses import dataclass

from realtime.types import (
    DEFAULT_HEARTBEAT_INTERVAL,
    DEFAULT_HEARTBEAT_TIMEOUT,
    validate_heartbeat,
)


@dataclass(frozen=True)
class RealtimeClientOptions:
    """Options for the realtime connections opened by `AsyncClient.realtime`."""

    heartbeat_interval: float = DEFAULT_HEARTBEAT_INTERVAL
    """Seconds between heartbeats. Must be positive."""

    heartbeat_timeout: float = DEFAULT_HEARTBEAT_TIMEOUT
    """Seconds to wait for a heartbeat reply before the connection is considered lost. Must be positive."""

    def __post_init__(self) -> None:
        validate_heartbeat(self.heartbeat_interval, self.heartbeat_timeout)
