from typing_extensions import NotRequired, TypedDict


class RealtimeClientOptions(TypedDict, total=False):
    auto_reconnect: NotRequired[bool]
    hb_interval: NotRequired[int]
    max_retries: NotRequired[int]
    initial_backoff: NotRequired[float]
