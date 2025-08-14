from typing import Any, List, Literal, Mapping, Optional, Union

from pydantic import BaseModel, Field, TypeAdapter
from typing_extensions import TypeAlias, TypedDict

from .types import (
    BroadcastPayload,
    ChannelEvents,
    PostgresChangesData,
    PostgresChangesPayload,
    RawPresenceDiff,
    RawPresenceState,
    RealtimeChannelOptions,
    RealtimePostgresChangesListenEvent,
)


class Message(BaseModel):
    """
    Dataclass abstraction for message
    """

    event: str
    payload: Mapping[str, Any]
    topic: str
    ref: Optional[str] = None
    join_ref: Optional[str] = None


class JoinMessage(BaseModel):
    event: Literal[ChannelEvents.join]
    topic: str
    ref: str
    payload: RealtimeChannelOptions


class PostgresRowChange(BaseModel):
    id: int
    events: RealtimePostgresChangesListenEvent
    table: str
    schema_: Optional[str] = Field(alias="schema", default=None)
    filter: Optional[str] = None


class ReplyPostgresChanges(BaseModel):
    postgres_changes: Optional[List[PostgresRowChange]] = None


class SuccessReplyMessage(BaseModel):
    status: Literal["ok"]
    response: ReplyPostgresChanges


class ErrorReplyMessage(BaseModel):
    status: Literal["error"]
    response: dict[str, Any]  # TODO: what goes in here?


class ReplyMessage(BaseModel):
    event: Literal[ChannelEvents.reply]
    topic: str
    payload: Union[SuccessReplyMessage, ErrorReplyMessage]
    ref: Optional[str]


class SuccessSystemPayload(BaseModel):
    channel: str
    extension: str
    message: str
    status: Literal["ok"]


class ErrorSystemPayload(BaseModel):
    channel: str
    extension: str
    message: str
    status: Literal["error"]


class SystemMessage(BaseModel):
    event: Literal[ChannelEvents.system]
    topic: str
    payload: Union[SuccessSystemPayload, ErrorSystemPayload]
    ref: Literal[None]


class HeartbeatPayload(BaseModel):
    pass


class HeartbeatMessage(BaseModel):
    event: Literal[ChannelEvents.heartbeat]
    topic: Literal["phoenix"]
    ref: str
    payload: HeartbeatPayload


class AccessTokenPayload(BaseModel):
    access_token: str


class AccessTokenMessage(BaseModel):
    event: Literal[ChannelEvents.access_token]
    topic: str
    payload: AccessTokenPayload
    ref: Literal[None]


class PostgresChangesMessage(BaseModel):
    event: Literal[ChannelEvents.postgres_changes]
    topic: str
    payload: PostgresChangesPayload
    ref: Literal[None]


class BroadcastMessage(BaseModel):
    event: Literal[ChannelEvents.broadcast]
    topic: str
    payload: BroadcastPayload
    ref: Literal[None]


class PresenceMessage(BaseModel):
    event: Literal[ChannelEvents.presence]
    topic: str
    payload: dict[str, Any]
    ref: Literal[None]


class PresenceStateMessage(BaseModel):
    event: Literal[ChannelEvents.presence_state]
    topic: str
    payload: RawPresenceState
    ref: Literal[None]


class PresenceDiffMessage(BaseModel):
    event: Literal[ChannelEvents.presence_diff]
    topic: str
    payload: RawPresenceDiff
    ref: Literal[None]


class ChannelErrorMessage(BaseModel):
    event: Literal[ChannelEvents.error]
    topic: str
    payload: dict[str, Any]
    ref: Optional[str]


class ChannelCloseMessage(BaseModel):
    event: Literal[ChannelEvents.close]
    topic: str
    payload: dict[str, Any]
    ref: Optional[str]


ServerMessage: TypeAlias = Union[
    SystemMessage,
    ReplyMessage,
    HeartbeatMessage,
    BroadcastMessage,
    PresenceStateMessage,
    PresenceDiffMessage,
    PostgresChangesMessage,
    ChannelErrorMessage,
    ChannelCloseMessage,
]
ServerMessageAdapter: TypeAdapter[ServerMessage] = TypeAdapter(ServerMessage)
ClientMessage: TypeAlias = Union[
    JoinMessage,
    HeartbeatMessage,
    BroadcastMessage,
    PresenceMessage,
    AccessTokenMessage,
]
