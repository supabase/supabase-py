from typing import TypedDict


class RealtimeClientOptions(TypedDict, total=False):
    auto_reconnect: bool
    hb_interval: int
    max_retries: int
    initial_backoff: float


class HttpxOptions(TypedDict, total=False):
    verify: bool = True
    """Either `True` to use an SSL context with the default CA bundle, `False` to disable verification."""
