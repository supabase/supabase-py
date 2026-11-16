from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Annotated, Any, Literal, TypeVar

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    Strict,
    field_validator,
    model_validator,
)

# Constants
DEFAULT_TIMEOUT = 10
PHOENIX_CHANNEL = "phoenix"
PROTOCOL_VERSION = "2.0.0"
DEFAULT_HEARTBEAT_INTERVAL = 25
DEFAULT_HEARTBEAT_TIMEOUT = 5


def validate_heartbeat(interval: float, timeout: float) -> None:
    """Raise `ValueError` unless both heartbeat durations are positive seconds."""
    if not interval > 0:
        raise ValueError(f"heartbeat_interval must be positive, got {interval}")
    if not timeout > 0:
        raise ValueError(f"heartbeat_timeout must be positive, got {timeout}")


# Type variables and custom types
type Callback[**T_ParamSpec, T_Retval] = Callable[T_ParamSpec, T_Retval]


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


@dataclass(frozen=True)
class PostgresChangesBinding:
    event: RealtimePostgresChangesListenEvent
    table: str | None = None
    schema: str = "public"
    filter: str | None = None
    select: Sequence[str] | None = None
    id: Annotated[int | None, Field(exclude=True)] = None

    def __post_init__(self) -> None:
        if self.select is not None:
            object.__setattr__(self, "select", tuple(self.select))


class PostgresChangesPayload(BaseModel):
    """A row change the server read from the Postgres write-ahead log.

    The server nests the change under ``data``, next to the ``ids`` of the
    bindings it matched; both are read into this one model.
    """

    model_config = ConfigDict(populate_by_name=True)

    event: RealtimePostgresChangesListenEvent = Field(alias="type")
    """The statement that made the change: ``INSERT``, ``UPDATE`` or ``DELETE``."""

    schema_: str = Field(alias="schema")
    """The schema of the changed table."""

    table: str
    """The changed table."""

    commit_timestamp: datetime
    """When the transaction committed."""

    columns: list[PostgresChangesColumn] = []
    """The columns of the table, with their Postgres type names."""

    record: dict[str, Any] | None = None
    """The row after the change, or ``None`` for a delete."""

    old_record: dict[str, Any] | None = None
    """The row before the change, or ``None`` for an insert.

    Without ``REPLICA IDENTITY FULL`` on the table, or under row level
    security, it holds only the primary key columns.
    """

    errors: list[str] = []
    """Errors the server reported for the change, such as
    ``"Error 413: Payload Too Large"``. The records of a change with errors
    can be incomplete."""

    ids: list[int] = []
    """The ids of the bindings of the channel the change matched."""

    @model_validator(mode="before")
    @classmethod
    def _unwrap_data(cls, value: object) -> object:
        if isinstance(value, Mapping) and "data" in value:
            return {**value["data"], "ids": value.get("ids", [])}
        return value

    @field_validator("errors", mode="before")
    @classmethod
    def _errors_as_list(cls, value: object) -> object:
        if value is None:
            return ()
        if isinstance(value, str):
            return (value,)
        return value


class BroadcastMeta(BaseModel):
    replayed: bool | None = None
    id: str | None = None


class BroadcastPayload(BaseModel):
    event: str
    payload: dict[str, Any] | Annotated[bytes, Strict()]
    type: str | None = None
    meta: BroadcastMeta | None = None


class Presence(BaseModel):
    model_config = ConfigDict(extra="allow")

    presence_ref: str


class PresenceEvents:
    def __init__(self, state: str, diff: str) -> None:
        self.state = state
        self.diff = diff


class PresenceOptions:
    def __init__(self, events: PresenceEvents) -> None:
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
