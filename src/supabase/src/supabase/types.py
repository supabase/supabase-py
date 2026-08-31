from typing import TypedDict
from postgrest.types import JSON, Json


class RealtimeClientOptions(TypedDict, total=False):
    auto_reconnect: bool
    hb_interval: int
    max_retries: int
    initial_backoff: float


__all__ = [
    "JSON",
    "Json",
    "RealtimeClientOptions",
]

