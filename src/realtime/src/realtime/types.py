from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, List, Literal, Optional, TypeVar

from pydantic import BaseModel, ConfigDict, Field, with_config
from typing_extensions import (
    Generic,
    NotRequired,
    ParamSpec,
    Required,
    TypeAlias,
    TypedDict,
)

# Constants
DEFAULT_TIMEOUT = 10
PHOENIX_CHANNEL = "phoenix"
VSN = "1.0.0"
DEFAULT_HEARTBEAT_INTERVAL = 25

# Type variables and custom types
T_ParamSpec = ParamSpec("T_ParamSpec")
T_Retval = TypeVar("T_Retval")
Callback: TypeAlias = Callable[T_ParamSpec, T_Retval]


# Enums
class ChannelEvents(str, Enum):
    """
    ChannelEvents are a bunch of constant strings that are defined according to
    what the Phoenix realtime server expects.
    """

    close = "phx_close"
    error = "phx_error"
    join = "phx_join"  # type: ignore
    reply = "phx_reply"
    leave = "phx_leave"
    heartbeat = "heartbeat"
    access_token = "access_token"
    broadcast = "broadcast"
    presence = "presence"
    presence_state = "presence_state"
    presence_diff = "presence_diff"
    system = "system"
    postgres_changes = "postgres_changes"


class ChannelStates(str, Enum):
    JOINED = "joined"
    CLOSED = "closed"
    ERRORED = "errored"
    JOINING = "joining"
    LEAVING = "leaving"


class RealtimeSubscribeStates(str, Enum):
    SUBSCRIBED = "SUBSCRIBED"
    TIMED_OUT = "TIMED_OUT"
    CLOSED = "CLOSED"
    CHANNEL_ERROR = "CHANNEL_ERROR"


class RealtimePresenceListenEvents(str, Enum):
    SYNC = "SYNC"
    JOIN = "JOIN"
    LEAVE = "LEAVE"


class RealtimeAcknowledgementStatus(str, Enum):
    Ok = "ok"
    Error = "error"
    Timeout = "timeout"


# Literals
class RealtimePostgresChangesListenEvent(str, Enum):
    All = "*"
    Insert = "INSERT"
    Update = "UPDATE"
    Delete = "DELETE"


Payload = TypeVar("Payload")


class PostgresChangesColumn(TypedDict):
    name: str
    type: str


class PostgresChangesData(TypedDict):
    schema: str
    table: str
    commit_timestamp: str
    type: RealtimePostgresChangesListenEvent
    errors: Optional[str]
    columns: List[PostgresChangesColumn]
    record: NotRequired[Optional[dict[str, Any]]]
    old_record: NotRequired[dict[str, Any]]  # todo: improve this


class PostgresChangesPayload(TypedDict):
    data: PostgresChangesData
    ids: List[int]


class BroadcastPayload(TypedDict):
    event: str
    payload: dict[str, Any]


@dataclass(frozen=True)
class BroadcastCallback:
    callback: Callable[[BroadcastPayload], None]
    event: str

    def __call__(self, payload: BroadcastPayload) -> None:
        if self.event == payload["event"]:
            return self.callback(payload)


@dataclass
class PostgresChangesCallback:
    callback: Callable[[PostgresChangesPayload], None]
    event: RealtimePostgresChangesListenEvent
    table: Optional[str]
    schema: Optional[str]
    filter: Optional[str]
    id: Optional[int] = None

    def __call__(self, payload: PostgresChangesPayload) -> None:
        event_matches = (
            self.event == payload["data"]["type"]
            or self.event == RealtimePostgresChangesListenEvent.All
        )
        if self.id and self.id in payload["ids"] and event_matches:
            return self.callback(payload)

    @property
    def binding_filter(self) -> dict[str, Optional[str]]:
        binding = {"events": self.event, "table": self.table}
        if self.schema:
            binding["schema"] = self.schema
        if self.filter:
            binding["filter"] = self.filter
        return binding


class _Hook:
    def __init__(self, status: str, callback: Callback[[Dict[str, Any]], None]):
        self.status = status
        self.callback = callback


@with_config(ConfigDict(extra="allow"))
class Presence(TypedDict):
    presence_ref: str


class PresenceEvents:
    def __init__(self, state: str, diff: str):
        self.state = state
        self.diff = diff


class PresenceOpts:
    def __init__(self, events: PresenceEvents):
        self.events = events


# TypedDicts
class RealtimeChannelBroadcastConfig(TypedDict):
    ack: bool
    self: bool


class RealtimeChannelPresenceConfig(TypedDict):
    key: str
    enabled: bool


class RealtimeChannelConfig(TypedDict):
    broadcast: Optional[RealtimeChannelBroadcastConfig]
    presence: Optional[RealtimeChannelPresenceConfig]
    private: bool


class RealtimeChannelOptions(TypedDict):
    config: RealtimeChannelConfig


@with_config(ConfigDict(extra="allow"))
class PresenceMeta(TypedDict):
    phx_ref: NotRequired[str]
    phx_ref_prev: NotRequired[str]


class RawPresenceStateEntry(TypedDict):
    metas: List[PresenceMeta]


# Custom types
PresenceOnJoinCallback = Callable[[str, List[Any], List[Presence]], None]
PresenceOnLeaveCallback = Callable[[str, List[Any], List[Presence]], None]
RealtimePresenceState = Dict[str, List[Presence]]
RawPresenceState = Dict[str, RawPresenceStateEntry]


class RawPresenceDiff(TypedDict):
    joins: RawPresenceState
    leaves: RawPresenceState


class PresenceDiff(TypedDict):
    joins: RealtimePresenceState
    leaves: RealtimePresenceState


# Specific payload types
class RealtimePresenceJoinPayload(TypedDict):
    event: Literal[RealtimePresenceListenEvents.JOIN]
    key: str
    current_presences: List[Presence]
    new_presences: List[Presence]


class RealtimePresenceLeavePayload(TypedDict):
    event: Literal[RealtimePresenceListenEvents.LEAVE]
    key: str
    current_presences: List[Presence]
    left_presences: List[Presence]
