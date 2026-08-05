from typing import Annotated, Any, List, Literal, Mapping, Optional, Union

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter
from supabase_utils.types import JSON
from typing_extensions import TypeAlias, TypedDict

from .types import (
    BroadcastPayload,
    ChannelEvents,
    PostgresChangesPayload,
    RawPresenceDiff,
    RawPresenceState,
    RealtimeChannelOptionsPayload,
    RealtimePostgresChangesListenEvent,
)


class Message(BaseModel):
    """
    Dataclass abstraction for message
    """

    event: str
    payload: Mapping[str, JSON]
    topic: str
    ref: str | None = None
    join_ref: str | None = None


class JoinMessage(BaseModel):
    event: Literal[ChannelEvents.join]
    topic: str
    ref: str
    payload: RealtimeChannelOptionsPayload


class PostgresRowChange(BaseModel):
    id: int
    event: RealtimePostgresChangesListenEvent
    table: str | None = None
    schema_: str | None = Field(alias="schema", default=None)
    filter: str | None = None


class ReplyPostgresChanges(BaseModel):
    postgres_changes: List[PostgresRowChange] | None = None


class SuccessReplyMessage(BaseModel):
    status: Literal["ok"]
    response: ReplyPostgresChanges


class ErrorReplyMessage(BaseModel):
    status: Literal["error"]
    response: dict[str, JSON]  # TODO: what goes in here?


class ReplyMessage(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event: Literal[ChannelEvents.reply]
    topic: str
    payload: SuccessReplyMessage | ErrorReplyMessage
    ref: str | None


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
    model_config = ConfigDict(from_attributes=True)

    event: Literal[ChannelEvents.system]
    topic: str
    payload: SuccessSystemPayload | ErrorSystemPayload
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
    model_config = ConfigDict(from_attributes=True)

    event: Literal[ChannelEvents.postgres_changes]
    topic: str
    payload: PostgresChangesPayload
    ref: Literal[None]


class BroadcastMessage(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event: Literal[ChannelEvents.broadcast]
    topic: str
    payload: BroadcastPayload
    ref: Literal[None]


class PresenceMessage(BaseModel):
    event: Literal[ChannelEvents.presence]
    topic: str
    payload: dict[str, JSON]
    ref: Literal[None]


class PresenceStateMessage(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event: Literal[ChannelEvents.presence_state]
    topic: str
    payload: RawPresenceState
    ref: Literal[None]


class PresenceDiffMessage(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event: Literal[ChannelEvents.presence_diff]
    topic: str
    payload: RawPresenceDiff
    ref: Literal[None]


class ChannelErrorMessage(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event: Literal[ChannelEvents.error]
    topic: str
    payload: dict[str, JSON]
    ref: str | None


class ChannelCloseMessage(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event: Literal[ChannelEvents.close]
    topic: str
    payload: dict[str, JSON]
    ref: str | None


class ChannelLeaveMessage(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    event: Literal[ChannelEvents.leave]
    topic: str
    payload: dict[str, JSON]
    ref: str


ServerMessage: TypeAlias = Annotated[
    SystemMessage
    | BroadcastMessage
    | PresenceStateMessage
    | PresenceDiffMessage
    | PostgresChangesMessage
    | ChannelErrorMessage
    | ChannelCloseMessage,
    Field(discriminator="event"),
]
ServerMessageAdapter: TypeAdapter[ServerMessage] = TypeAdapter(ServerMessage)

ClientMessage: TypeAlias = (
    JoinMessage
    | HeartbeatMessage
    | BroadcastMessage
    | PresenceMessage
    | AccessTokenMessage
    | ChannelLeaveMessage
)
