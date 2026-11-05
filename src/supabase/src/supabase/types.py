from typing_extensions import TypedDict


class RealtimeClientOptions(TypedDict, total=False, closed=True):
    heartbeat_interval: int
    heartbeat_timeout: int
