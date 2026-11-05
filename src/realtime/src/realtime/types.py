from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Annotated, Any, Literal, TypeAlias, TypeVar

from pydantic import BaseModel, ConfigDict, Field
from typing_extensions import ParamSpec

# Constants
DEFAULT_TIMEOUT = 10
PHOENIX_CHANNEL = "phoenix"
PROTOCOL_VERSION = "1.0.0"
DEFAULT_HEARTBEAT_INTERVAL = 25
DEFAULT_HEARTBEAT_TIMEOUT = 5

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
    join = "phx_join"  # pyrefly: ignore[bad-override-mutable-attribute]
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


class PostgresChangesColumn(BaseModel):
    name: str
    type: str


class PostgresChangesData(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    schema_: str = Field(alias="schema")
    table: str
    commit_timestamp: str
    type: RealtimePostgresChangesListenEvent
    errors: list[str] | None
    columns: list[PostgresChangesColumn]
    record: dict[str, Any] | None = None
    old_record: dict[str, Any] | None = None


@dataclass
class PostgresChangesBinding:
    event: RealtimePostgresChangesListenEvent
    table: str | None
    schema: str | None
    filter: str | None
    select: list[str] | None = None
    id: Annotated[int | None, Field(exclude=True)] = None


class PostgresChangesPayload(BaseModel):
    data: PostgresChangesData
    ids: list[int]


class BroadcastMeta(BaseModel):
    replayed: bool | None = None
    id: str | None = None


class BroadcastPayload(BaseModel):
    event: str
    payload: dict[str, Any]
    type: str | None = None
    meta: BroadcastMeta | None = None


class Presence(BaseModel):
    model_config = ConfigDict(extra="allow")

    presence_ref: str


class PresenceEvents:
    def __init__(self, state: str, diff: str):
        self.state = state
        self.diff = diff


class PresenceOptions:
    def __init__(self, events: PresenceEvents):
        self.events = events


class ReplayOption(BaseModel):
    since: int
    limit: int | None


class RealtimeChannelBroadcastConfig(BaseModel):
    ack: bool
    self: bool
    replay: ReplayOption | None = None
    replication_ready: bool | None = None


class RealtimeChannelPresenceConfig(BaseModel):
    key: str
    enabled: bool


class RealtimeChannelConfig(BaseModel):
    broadcast: RealtimeChannelBroadcastConfig
    presence: RealtimeChannelPresenceConfig
    postgres_changes: list[PostgresChangesBinding]
    private: bool


class RealtimeChannelOptionsPayload(BaseModel):
    config: RealtimeChannelConfig
    access_token: str | None = None


class PresenceMeta(BaseModel):
    model_config = ConfigDict(extra="allow")

    phx_ref: str
    phx_ref_prev: str | None = None


class RawPresenceStateEntry(BaseModel):
    metas: list[PresenceMeta]


RealtimePresenceState = dict[str, list[Presence]]
RawPresenceState = dict[str, RawPresenceStateEntry]


class RawPresenceDiff(BaseModel):
    joins: RawPresenceState
    leaves: RawPresenceState


class PresenceDiff(BaseModel):
    joins: RealtimePresenceState
    leaves: RealtimePresenceState


class RealtimePresenceJoinPayload(BaseModel):
    event: Literal[RealtimePresenceListenEvents.JOIN]
    key: str
    current_presences: list[Presence]
    new_presences: list[Presence]


class RealtimePresenceLeavePayload(BaseModel):
    event: Literal[RealtimePresenceListenEvents.LEAVE]
    key: str
    current_presences: list[Presence]
    left_presences: list[Presence]
