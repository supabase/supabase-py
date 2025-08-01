from typing import TypedDict


class RealtimeClientOptions(TypedDict, total=False):
    auto_reconnect: bool
    hb_interval: int
    max_retries: int
    initial_backoff: float
