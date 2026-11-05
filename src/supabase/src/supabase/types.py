from dataclasses import dataclass

from realtime.types import DEFAULT_HEARTBEAT_INTERVAL, DEFAULT_HEARTBEAT_TIMEOUT


@dataclass(frozen=True)
class RealtimeClientOptions:
    """Options for the realtime connections opened by `AsyncClient.realtime`."""

    heartbeat_interval: int = DEFAULT_HEARTBEAT_INTERVAL
    """Seconds between heartbeats. Intervals below 15 seconds are raised to 15."""

    heartbeat_timeout: int = DEFAULT_HEARTBEAT_TIMEOUT
    """Seconds to wait for a heartbeat reply before the connection is considered lost."""
