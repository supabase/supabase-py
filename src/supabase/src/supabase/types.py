from typing_extensions import TypedDict


class RealtimeClientOptions(TypedDict, total=False, closed=True):
    hb_interval: int
    hb_timeout: int
