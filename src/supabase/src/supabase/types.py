from typing import TypedDict


class RealtimeClientOptions(TypedDict, total=False):
    ack: bool
    hb_interval: int
    hb_timeout: int
