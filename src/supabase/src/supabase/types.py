from typing import Awaitable, Callable, Optional, TypedDict, Union


class RealtimeClientOptions(TypedDict, total=False):
    auto_reconnect: bool
    hb_interval: int
    max_retries: int
    initial_backoff: float
    access_token: Callable[[], Union[Awaitable[Optional[str]], Optional[str]]]
