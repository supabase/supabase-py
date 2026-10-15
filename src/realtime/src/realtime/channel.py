from __future__ import annotations

import asyncio
import json
import logging
from dataclasses import dataclass, field
from typing import (
    TYPE_CHECKING,
    Any,
    AsyncIterator,
    Callable,
    Dict,
    List,
    Mapping,
    Optional,
    TypeAlias,
)

import websockets
from supabase_utils.types import JSON
from typing_extensions import assert_never

from .message import (
    BroadcastMessage,
    ChannelCloseMessage,
    ChannelErrorMessage,
    HeartbeatMessage,
    Message,
    PostgresChangesMessage,
    PostgresChangesPayload,
    PostgresRowChange,
    PresenceDiffMessage,
    PresenceStateMessage,
    ReplyMessage,
    ReplyPostgresChanges,
    ServerMessage,
    ServerMessageAdapter,
    SuccessReplyMessage,
    SuccessSystemPayload,
    SystemMessage,
)
from .presence import PresenceEvent, RealtimePresence
from .types import (
    BroadcastPayload,
    Callback,
    ChannelEvents,
    ChannelStates,
    PostgresChangesBinding,
    PostgresChangesData,
    RealtimeAcknowledgementStatus,
    RealtimeChannelBroadcastConfig,
    RealtimeChannelConfig,
    RealtimeChannelOptionsPayload,
    RealtimeChannelPresenceConfig,
    RealtimePostgresChangesListenEvent,
    RealtimePresenceState,
    RealtimeSubscribeStates,
    ReplayOption,
)

if TYPE_CHECKING:
    from .client import RealtimeClient

logger = logging.getLogger(__name__)


@dataclass
class RealtimeChannelOptions:
    broadcast_ack: bool = False
    broadcast_self: bool = False
    broadcast_replay_since: int | None = None
    broadcast_replay_limit: int | None = None
    broadcast_replication_ready: bool = False
    presence_key: str = ""
    presence_enabled: bool = False
    is_private: bool = False
    token: str | None = None
    postgres_changes_bindings: list[PostgresChangesBinding] = field(
        default_factory=list
    )

    def broadcast(
        self,
        ack: bool = False,
        listen_self: bool = False,
        replay_since: int | None = None,
        replay_limit: int | None = None,
        replication_ready: bool = False,
    ) -> RealtimeChannelOptions:
        """
        Configure broadcast for the channel.

        :param replication_ready: When True, the server emits a ``system`` message once
            the Postgres replication connection backing the channel is ready to stream
            changes. Its payload ``status`` is ``"ok"`` on success or ``"error"`` if the
            connection is not ready in time.
        """
        self.broadcast_ack = ack
        self.broadcast_self = listen_self
        self.broadcast_replay_since = replay_since
        self.broadcast_replay_limit = replay_limit
        self.broadcast_replication_ready = replication_ready
        return self

    def presence(self, key: str = "", enabled: bool = False) -> RealtimeChannelOptions:
        self.presence_key = key
        self.presence_enabled = enabled
        return self

    def private(self, private: bool = False) -> RealtimeChannelOptions:
        self.is_private = private
        return self

    def postgres_changes(
        self,
        event: RealtimePostgresChangesListenEvent,
        table: str | None = None,
        schema: str | None = None,
        filter: str | None = None,
        id: int | None = None,
        select: list[str] | None = None,
    ) -> RealtimeChannelOptions:
        """
        Listen for Postgres database changes.

        :param event: The change event to listen for (``INSERT``, ``UPDATE``, ``DELETE`` or ``*``)
        :param table: The table name to monitor. Defaults to all tables
        :param schema: The database schema to monitor
        :param filter: Optional filter string, evaluated server-side, in the form
            ``column=operator.value`` (e.g. ``"id=eq.1"`` or ``"title=like.%foo%"``).
            Supported operators: ``eq``, ``neq``, ``lt``, ``lte``, ``gt``, ``gte``,
            ``in`` (``"status=in.(active,pending)"``), ``like``, ``ilike``, ``is``
            (``"deleted_at=is.null"``), ``match``, ``imatch`` (POSIX regex),
            ``isdistinct`` (NULL-safe inequality). Any operator can be negated with
            the ``not.`` prefix (e.g. ``"status=not.in.(draft,archived)"``). Combine
            multiple conditions with commas to apply them as an ``AND``
            (e.g. ``"amount=gt.100,status=in.(open,pending)"``).
        :param select: Optional list of columns to receive instead of the full row.
            Reduces payload size (helpful for large ``bytea``/``jsonb`` columns). The
            listed columns must be selectable by the subscribing role.
        """
        binding = PostgresChangesBinding(
            event=event,
            table=table,
            schema=schema,
            filter=filter,
            select=select,
            id=id,
        )
        self.postgres_changes_bindings.append(binding)
        return self

    def to_payload(self) -> RealtimeChannelOptionsPayload:
        replay = (
            ReplayOption(
                since=self.broadcast_replay_since,
                limit=self.broadcast_replay_limit,
            )
            if self.broadcast_replay_since is not None
            else None
        )
        payload = RealtimeChannelOptionsPayload(
            access_token=self.token,
            config=RealtimeChannelConfig(
                private=self.is_private,
                broadcast=RealtimeChannelBroadcastConfig(
                    ack=self.broadcast_ack,
                    self=self.broadcast_self,
                    replay=replay,
                    replication_ready=self.broadcast_replication_ready or None,
                ),
                presence=RealtimeChannelPresenceConfig(
                    key=self.presence_key,
                    enabled=self.presence_enabled,
                ),
                postgres_changes=[
                    binding.as_dict() for binding in self.postgres_changes_bindings
                ],
            ),
        )
        return payload


ChannelMessage: TypeAlias = (
    SystemMessage
    | BroadcastMessage
    | PostgresChangesMessage
    | ChannelErrorMessage
    | ChannelCloseMessage
    | PresenceEvent
)


class RealtimeChannel:
    """
    Channel is an abstraction for a topic subscription on an existing socket connection.
    Each Channel has its own topic and a list of event-callbacks that respond to messages.
    Should only be instantiated through `AsyncRealtimeClient.channel(topic)`.
    """

    def __init__(
        self,
        socket: RealtimeClient,
        topic: str,
        params: RealtimeChannelOptions | None = None,
    ) -> None:
        """
        Initialize the Channel object.

        :param socket: RealtimeClient object
        :param topic: Topic that it subscribes to on the realtime server
        :param params: Optional parameters for connection.
        """
        self.socket = socket
        self.params = params or RealtimeChannelOptions()
        self.topic = topic
        self.presence: RealtimePresence = RealtimePresence()
        self.state = ChannelStates.CLOSED
        self.joined = False
        self.join_ref: str | None = None
        self.message_stream: asyncio.Queue[Message] = asyncio.Queue()
        self.broadcast_endpoint_url = self._broadcast_endpoint_url()

    async def __aenter__(self) -> RealtimeChannel:
        await self.subscribe()
        return self

    async def __aexit__(self, *args) -> None:
        try:
            await self.unsubscribe()
        except websockets.ConnectionClosed:
            # in the case of disconnect, we cannot guarantee that an unsubscribe message can be sent
            pass

    async def subscribe(self) -> ReplyMessage:
        if self.socket.last_token is not None:
            self.params.token = self.socket.last_token
        payload = self.params.to_payload()
        join_ref = self.socket._make_ref()
        message = Message(
            topic=self.topic,
            event=ChannelEvents.join,
            payload=payload.model_dump(exclude_none=True),
            ref=join_ref,
            join_ref=join_ref,
        )
        msg = await self.socket.send(message)
        logger.info(f"Subscribe reply: {msg!r}")
        if msg.payload.status != "ok":
            raise Exception(
                f"error while subscribing to channel: {msg.payload.response!r}"
            )
        self.join_ref = join_ref
        self.joined = True
        self.state = ChannelStates.JOINED
        return msg

    @property
    async def messages(self) -> AsyncIterator[ChannelMessage]:
        while True:
            get_task = asyncio.create_task(self.message_stream.get())
            message = await self.socket.get_message_or_raise(get_task)
            server_message = ServerMessageAdapter.validate_python(message)
            if isinstance(server_message, PresenceStateMessage):
                for presence_event in self.presence._on_state_event(
                    server_message.payload
                ):
                    yield presence_event
            elif isinstance(server_message, PresenceDiffMessage):
                for presence_event in self.presence._on_diff_event(
                    server_message.payload
                ):
                    yield presence_event
            else:
                yield server_message

    async def unsubscribe(self) -> None:
        self.state = ChannelStates.LEAVING
        try:
            await self.send_event(ChannelEvents.leave, payload={})
        finally:
            self.joined = False
            self.state = ChannelStates.CLOSED
            self.socket._remove_channel(self)

    # Presence methods
    async def track(self, user_status: Dict[str, Any]) -> ReplyMessage:
        """
        Track presence status for the current user.

        :param user_status: Dictionary containing the user's presence information
        """
        return await self.send_presence("track", user_status)

    async def untrack(self) -> ReplyMessage:
        """
        Stop tracking presence for the current user.
        """
        return await self.send_presence("untrack", {})

    def presence_state(self) -> RealtimePresenceState:
        """
        Get the current state of presence on this channel.

        :return: Dictionary mapping presence keys to lists of presence payloads
        """
        return self.presence.state

    async def send_event(
        self, event: ChannelEvents, payload: Mapping[str, JSON]
    ) -> ReplyMessage:
        message = Message(
            topic=self.topic,
            event=event,
            ref=self.socket._make_ref(),
            join_ref=self.join_ref,
            payload=payload,
        )
        return await self.socket.send(message)

    async def send_event_no_wait(
        self, event: ChannelEvents, payload: Mapping[str, JSON]
    ) -> None:
        message = Message(
            topic=self.topic,
            event=event,
            ref=self.socket._make_ref(),
            join_ref=self.join_ref,
            payload=payload,
        )
        return await self.socket.send_no_wait(message)

    # Broadcast methods
    async def send_broadcast(self, event: str, data: JSON) -> ReplyMessage | None:
        """
        Send a broadcast message through this channel.

        :param event: The name of the broadcast event
        :param data: The payload to broadcast
        """
        payload = {"type": "broadcast", "event": event, "payload": data}
        if self.params.broadcast_ack:
            return await self.send_event(ChannelEvents.broadcast, payload)
        else:
            await self.send_event_no_wait(ChannelEvents.broadcast, payload)
            return None

    # Internal methods

    def _broadcast_endpoint_url(self):
        return self.socket.http_endpoint.joinpath("api", "broadcast")

    async def send_presence(self, event: str, data: JSON) -> ReplyMessage:
        return await self.send_event(
            ChannelEvents.presence, {"event": event, "payload": data}
        )
