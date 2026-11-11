from __future__ import annotations

import asyncio
import contextlib
import logging
from collections.abc import Buffer, Sequence
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Any, Self

import websockets

from .exceptions import RealtimeError
from .message import (
    BroadcastMessage,
    ChannelCloseMessage,
    ChannelErrorMessage,
    Message,
    PostgresChangesMessage,
    PresenceDiffMessage,
    PresenceStateMessage,
    ReplyMessage,
    ServerMessageAdapter,
    SystemMessage,
)
from .presence import PresenceEvent, RealtimePresence
from .types import (
    ChannelEvents,
    ChannelStates,
    PostgresChangesBinding,
    RealtimeChannelBroadcastConfig,
    RealtimeChannelConfig,
    RealtimeChannelOptionsPayload,
    RealtimeChannelPresenceConfig,
    RealtimePostgresChangesListenEvent,
    RealtimePresenceState,
    ReplayOption,
)

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Mapping

    from supabase_utils.types import JSON
    from yarl import URL

    from .client import RealtimeClient

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
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
    postgres_changes_bindings: Sequence[PostgresChangesBinding] = ()

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "postgres_changes_bindings", tuple(self.postgres_changes_bindings)
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
        return replace(
            self,
            broadcast_ack=ack,
            broadcast_self=listen_self,
            broadcast_replay_since=replay_since,
            broadcast_replay_limit=replay_limit,
            broadcast_replication_ready=replication_ready,
        )

    def presence(self, key: str = "", enabled: bool = False) -> RealtimeChannelOptions:
        return replace(self, presence_key=key, presence_enabled=enabled)

    def private(self, private: bool = False) -> RealtimeChannelOptions:
        return replace(self, is_private=private)

    def postgres_changes(
        self,
        event: RealtimePostgresChangesListenEvent,
        table: str | None = None,
        schema: str | None = None,
        filter: str | None = None,
        id: int | None = None,
        select: Sequence[str] | None = None,
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
        return replace(
            self, postgres_changes_bindings=(*self.postgres_changes_bindings, binding)
        )

    def to_payload(self) -> RealtimeChannelOptionsPayload:
        replay = (
            ReplayOption(
                since=self.broadcast_replay_since,
                limit=self.broadcast_replay_limit,
            )
            if self.broadcast_replay_since is not None
            else None
        )
        return RealtimeChannelOptionsPayload(
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
                postgres_changes=list(self.postgres_changes_bindings),
            ),
        )


ChannelMessage = (
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
        options: RealtimeChannelOptions | None = None,
    ) -> None:
        """
        Initialize the Channel object.

        :param socket: RealtimeClient object
        :param topic: Topic that it subscribes to on the realtime server
        :param options: Optional channel options.
        """
        self.socket = socket
        self.options = options or RealtimeChannelOptions()
        self.topic = topic
        self.presence: RealtimePresence = RealtimePresence()
        self.state = ChannelStates.CLOSED
        self.join_ref: str | None = None
        self._subscribe_attempt: object | None = None
        self.message_stream: asyncio.Queue[Message] = asyncio.Queue()
        self.broadcast_endpoint_url = self._broadcast_endpoint_url()

    @property
    def joined(self) -> bool:
        return self.state == ChannelStates.JOINED

    async def __aenter__(self) -> Self:
        await self.subscribe()
        return self

    async def __aexit__(self, *args: object) -> None:
        with contextlib.suppress(websockets.ConnectionClosed):
            await self.unsubscribe()

    async def subscribe(self) -> ReplyMessage:
        """
        Join the channel, connecting the client first if it is not connected.

        :raises RealtimeError: If the server rejects the join, or if
            `unsubscribe()` is called before the join completes.
        """
        attempt = object()
        self._subscribe_attempt = attempt
        self._raise_if_topic_is_taken()
        await self.socket.connect()
        self._raise_if_unsubscribed(attempt)
        self._raise_if_topic_is_taken()
        self.socket.channels[self.topic] = self
        while not self.message_stream.empty():
            self.message_stream.get_nowait()
        options = self.options
        if self.socket.last_token is not None:
            options = replace(options, token=self.socket.last_token)
        payload = options.to_payload()
        join_ref = self.socket._make_ref()
        message = Message(
            topic=self.topic,
            event=ChannelEvents.join,
            payload=payload.model_dump(exclude_none=True),
            ref=join_ref,
            join_ref=join_ref,
        )
        self.join_ref = join_ref
        self.state = ChannelStates.JOINING
        try:
            msg = await self.socket._send(message)
        except BaseException as error:
            self.state = ChannelStates.CLOSED
            if isinstance(error, Exception):
                self._raise_if_unsubscribed(attempt)
            raise
        logger.info("Subscribe reply: %r", msg)
        self._raise_if_unsubscribed(attempt)
        if msg.payload.status != "ok":
            self.state = ChannelStates.CLOSED
            raise RealtimeError(
                f"error while subscribing to channel: {msg.payload.response!r}"
            )
        self.state = ChannelStates.JOINED
        return msg

    def _raise_if_unsubscribed(self, attempt: object) -> None:
        if self._subscribe_attempt is not attempt:
            raise RealtimeError(
                f"channel {self.topic!r} was unsubscribed before the join completed"
            )

    def _raise_if_topic_is_taken(self) -> None:
        if self.socket.channels.get(self.topic, self) is not self:
            raise ValueError(
                f"another channel is already registered for {self.topic!r}"
            )

    @property
    async def messages(self) -> AsyncIterator[ChannelMessage]:
        while True:
            if self.message_stream.empty():
                get_task = asyncio.create_task(self.message_stream.get())
                message = await self.socket._get_message_or_raise(get_task)
            else:
                message = self.message_stream.get_nowait()
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
        self._subscribe_attempt = None
        needs_leave = self.state in (ChannelStates.JOINED, ChannelStates.JOINING)
        self.state = ChannelStates.LEAVING
        self.socket._remove_channel(self)
        try:
            if needs_leave:
                await self._send_event(ChannelEvents.leave, payload={})
        finally:
            self.state = ChannelStates.CLOSED
            self.message_stream.put_nowait(
                Message(
                    topic=self.topic,
                    event=ChannelEvents.close,
                    payload={},
                    ref=self.join_ref,
                    join_ref=self.join_ref,
                )
            )
            await self.socket._close_if_unused()

    # Presence methods
    async def track(self, user_status: dict[str, Any]) -> ReplyMessage:
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

    async def _send_event(
        self, event: ChannelEvents, payload: Mapping[str, JSON | bytes]
    ) -> ReplyMessage:
        message = Message(
            topic=self.topic,
            event=event,
            ref=self.socket._make_ref(),
            join_ref=self.join_ref,
            payload=payload,
        )
        return await self.socket._send(message)

    async def _send_event_no_wait(
        self, event: ChannelEvents, payload: Mapping[str, JSON | bytes]
    ) -> None:
        message = Message(
            topic=self.topic,
            event=event,
            ref=self.socket._make_ref(),
            join_ref=self.join_ref,
            payload=payload,
        )
        return await self.socket._send_no_wait(message)

    # Broadcast methods
    async def send_broadcast(
        self, event: str, data: JSON | Buffer
    ) -> ReplyMessage | None:
        """
        Send a broadcast message through this channel.

        Without ``broadcast_ack``, returning means the message was written to the
        connection, not that the server received it.

        :param event: The name of the broadcast event
        :param data: The payload to broadcast. A bytes-like object, such as
            ``bytes``, ``bytearray`` or ``memoryview``, is sent as a binary frame,
            and receivers get it as ``bytes`` in ``BroadcastPayload.payload``.
            Anything else is sent as JSON.
        :raises ValueError: If ``data`` is bytes-like and the topic or the event
            is longer than 255 bytes in UTF-8.
        :raises websockets.ConnectionClosed: If the connection is closed.
        :raises Exception: If the connection already failed, the exception that
            failed it, such as a TimeoutError when a heartbeat timed out.
        """
        if isinstance(data, Buffer):
            data = bytes(data)
        payload = {"type": "broadcast", "event": event, "payload": data}
        if self.options.broadcast_ack:
            return await self._send_event(ChannelEvents.broadcast, payload)
        await self._send_event_no_wait(ChannelEvents.broadcast, payload)
        return None

    # Internal methods

    def _broadcast_endpoint_url(self) -> URL:
        return self.socket.http_endpoint.joinpath("api", "broadcast")

    async def send_presence(self, event: str, data: JSON) -> ReplyMessage:
        return await self._send_event(
            ChannelEvents.presence, {"event": event, "payload": data}
        )
