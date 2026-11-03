from typing import TypedDict


class RealtimeClientOptions(TypedDict, total=False):
    hb_interval: int
    hb_timeout: int
