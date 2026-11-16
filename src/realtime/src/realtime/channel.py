from __future__ import annotations

import asyncio
import contextlib
import logging
from collections.abc import Buffer, Sequence
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Any, Self

import websockets

from .exceptions import (
    AuthorizationError,
    NotConnectedError,
    RealtimeError,
    RealtimeTimeoutError,
    _is_fatal,
    _join_error,
)
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
    SuccessReplyMessage,
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
    from .message import PostgresRowChange

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
        schema: str = "public",
        filter: str | None = None,
        id: int | None = None,
        select: Sequence[str] | None = None,
    ) -> RealtimeChannelOptions:
        """
        Listen for Postgres database changes.

        :param event: The change event to listen for (``INSERT``, ``UPDATE``, ``DELETE`` or ``*``)
        :param table: The table name to monitor. Defaults to all tables
        :param schema: The database schema to monitor. Defaults to ``public``
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


@dataclass(frozen=True)
class ChannelStateChange:
    """
    Yielded by `RealtimeChannel.messages` when the connection of a joined
    channel drops, with the state `ERRORED` and the error that dropped it, and
    when the client joined the channel again, with the state `JOINED`.
    """

    state: ChannelStates
    error: Exception | None = None


@dataclass(frozen=True)
class _ChannelFailed:
    error: Exception


QueuedMessage = Message | ChannelStateChange | _ChannelFailed

ChannelMessage = (
    SystemMessage
    | BroadcastMessage
    | PostgresChangesMessage
    | ChannelErrorMessage
    | ChannelCloseMessage
    | PresenceEvent
    | ChannelStateChange
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
        self._rejoin_pending = False
        self._rejoin_authorization_failed = False
        self._tracked: dict[str, Any] | None = None
        self._dropping_messages = False
        self.message_stream: asyncio.Queue[QueuedMessage] = asyncio.Queue(
            maxsize=socket.max_queued_messages
        )
        self.broadcast_endpoint_url = self._broadcast_endpoint_url()

    @property
    def joined(self) -> bool:
        return self.state == ChannelStates.JOINED

    def _receive(self, message: Message) -> None:
        if message.event in (ChannelEvents.error, ChannelEvents.close):
            if message.join_ref is not None and message.join_ref != self.join_ref:
                logger.info(
                    "Ignoring %s of an earlier join: %r", message.event, message
                )
                return
            if message.event == ChannelEvents.error:
                self._on_error()
            else:
                self._on_close()
        self._enqueue(message)

    def _enqueue(self, message: QueuedMessage) -> None:
        if self.message_stream.empty():
            self._dropping_messages = False
        elif self.message_stream.full():
            self.message_stream.get_nowait()
            if not self._dropping_messages:
                logger.warning(
                    "the message queue of channel %s is full, dropping its oldest "
                    "messages until it is read",
                    self.topic,
                )
            self._dropping_messages = True
        self.message_stream.put_nowait(message)

    def _on_connection_lost(self, error: Exception) -> bool:
        if self._rejoin_pending:
            self.state = ChannelStates.ERRORED
            return True
        if self.state == ChannelStates.JOINED:
            logger.info("channel %s lost its connection", self.topic)
            self.state = ChannelStates.ERRORED
            self._rejoin_pending = True
            self._enqueue(ChannelStateChange(ChannelStates.ERRORED, error))
            return True
        if self.state in (ChannelStates.LEAVING, ChannelStates.CLOSED):
            return False
        self._on_error()
        self._enqueue(_ChannelFailed(error))
        return False

    def _on_client_stopped(self) -> None:
        if self.state == ChannelStates.JOINING:
            self._subscribe_attempt = None
        self._rejoin_pending = False
        self.state = ChannelStates.CLOSED

    def _on_error(self) -> None:
        if self.state in (ChannelStates.LEAVING, ChannelStates.CLOSED):
            return
        logger.info("channel %s errored", self.topic)
        self.state = ChannelStates.ERRORED

    def _on_close(self) -> None:
        if self.state == ChannelStates.LEAVING:
            return
        logger.info("channel %s was closed by the server", self.topic)
        self.state = ChannelStates.CLOSED

    async def __aenter__(self) -> Self:
        await self.subscribe()
        return self

    async def __aexit__(self, *args: object) -> None:
        with contextlib.suppress(websockets.ConnectionClosed):
            await self.unsubscribe()

    async def subscribe(self) -> ReplyMessage:
        """
        Join the channel, connecting the client first if it is not connected.

        When the connection of the joined channel drops, the client joins it
        again on its own once it reconnected.

        :raises AuthorizationError: If the server rejects the access token, or
            the row level security policies deny the join of a private channel.
        :raises ChannelJoinError: If the server rejects the join for another
            reason, given in its ``reason`` attribute.
        :raises RealtimeTimeoutError: If the server does not reply within the
            ``timeout`` of the client.
        :raises NotConnectedError: If the connection drops before the server
            replies.
        :raises RealtimeError: If the ``postgres_changes`` bindings in the
            server's reply do not match the requested ones (the channel is left
            first), or if `unsubscribe()` or `RealtimeClient.aclose()` is called
            before the join completes.
        """
        attempt = object()
        self._subscribe_attempt = attempt
        self._rejoin_pending = False
        self._raise_if_topic_is_taken()
        await self.socket.connect()
        return await self._join(attempt, clear_messages=True)

    async def _join(self, attempt: object, *, clear_messages: bool) -> ReplyMessage:
        await self.socket._refresh_token()
        self._raise_if_join_was_stopped(attempt)
        self._raise_if_topic_is_taken()
        self.socket.channels[self.topic] = self
        if clear_messages:
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
        failure = self.socket._connection_failure
        try:
            msg = await self.socket._send(message)
        except asyncio.CancelledError:
            self.state = ChannelStates.CLOSED
            await self._stop_cancelled_join(attempt, join_ref, failure)
            raise
        except RealtimeTimeoutError:
            self.state = ChannelStates.CLOSED
            self._raise_if_join_was_stopped(attempt)
            await self._leave_cancelled_join(join_ref, failure)
            raise
        except (websockets.ConnectionClosed, TimeoutError, OSError) as exc:
            self.state = ChannelStates.CLOSED
            self._raise_if_join_was_stopped(attempt)
            raise NotConnectedError(
                "RealtimeChannel.subscribe",
                f"the connection dropped before the join of {self.topic!r} completed",
            ) from exc
        except Exception:
            self.state = ChannelStates.CLOSED
            self._raise_if_join_was_stopped(attempt)
            raise
        logger.info("Subscribe reply: %r", msg)
        self._raise_if_join_was_stopped(attempt)
        if not isinstance(msg.payload, SuccessReplyMessage):
            self.state = ChannelStates.CLOSED
            reason = msg.payload.response.get("reason")
            raise _join_error(
                self.topic,
                reason if isinstance(reason, str) else repr(msg.payload.response),
            )
        if not self._postgres_changes_match(msg.payload.response.postgres_changes):
            with contextlib.suppress(Exception):
                await self.unsubscribe()
            raise RealtimeError(
                "mismatch between server and client bindings for postgres changes"
            )
        if self.state == ChannelStates.JOINING:
            self.state = ChannelStates.JOINED
        try:
            await self.socket._send_token_if_changed(self, payload.access_token)
        except asyncio.CancelledError:
            await self._stop_cancelled_join(attempt, join_ref, failure)
            raise
        return msg

    async def _rejoin(self) -> None:
        attempt = object()
        self._subscribe_attempt = attempt
        try:
            await self._join(attempt, clear_messages=False)
        except Exception as error:
            if self._subscribe_attempt is not attempt or not self._rejoin_pending:
                return
            retry_authorization = (
                isinstance(error, AuthorizationError)
                and not self._rejoin_authorization_failed
            )
            if _is_fatal(error) and not retry_authorization:
                self._fail_rejoin(error)
                return
            self._rejoin_authorization_failed = isinstance(error, AuthorizationError)
            self.state = ChannelStates.ERRORED
            logger.warning("could not join channel %s again: %r", self.topic, error)
            return
        if self._subscribe_attempt is not attempt:
            return
        self._rejoin_pending = False
        self._rejoin_authorization_failed = False
        logger.info("joined channel %s again", self.topic)
        self._enqueue(ChannelStateChange(ChannelStates.JOINED))
        if self._tracked is not None:
            try:
                await self.track(self._tracked)
            except Exception as error:
                logger.warning(
                    "could not track the presence on channel %s again: %r",
                    self.topic,
                    error,
                )

    def _fail_rejoin(self, error: Exception) -> None:
        logger.error("gave up joining channel %s again: %r", self.topic, error)
        self._rejoin_pending = False
        self._rejoin_authorization_failed = False
        self._subscribe_attempt = None
        self.state = ChannelStates.CLOSED
        self._enqueue(_ChannelFailed(error))

    def _postgres_changes_match(
        self, server_bindings: Sequence[PostgresRowChange] | None
    ) -> bool:
        if server_bindings is None:
            return True
        client_bindings = self.options.postgres_changes_bindings
        if len(server_bindings) < len(client_bindings):
            return False
        return all(
            (server.event, server.schema_, server.table, server.filter)
            == (client.event, client.schema, client.table, client.filter)
            for client, server in zip(client_bindings, server_bindings, strict=False)
        )

    def _raise_if_join_was_stopped(self, attempt: object) -> None:
        if self._subscribe_attempt is not attempt:
            raise RealtimeError(
                f"the join of channel {self.topic!r} was stopped by unsubscribe() "
                "or a closed connection before it completed"
            )

    async def _stop_cancelled_join(
        self,
        attempt: object,
        join_ref: str,
        failure: asyncio.Future[Message] | None,
    ) -> None:
        if self._subscribe_attempt is not attempt:
            return
        self.state = ChannelStates.CLOSED
        self._subscribe_attempt = None
        await self._leave_cancelled_join(join_ref, failure)

    async def _leave_cancelled_join(
        self, join_ref: str, failure: asyncio.Future[Message] | None
    ) -> None:
        if self.socket._connection_failure is not failure:
            return
        leave = Message(
            topic=self.topic,
            event=ChannelEvents.leave,
            ref=self.socket._make_ref(),
            join_ref=join_ref,
            payload={},
        )
        with contextlib.suppress(Exception):
            await self.socket._send_no_wait(leave)

    def _raise_if_topic_is_taken(self) -> None:
        if self.socket.channels.get(self.topic, self) is not self:
            raise ValueError(
                f"another channel is already registered for {self.topic!r}"
            )

    @property
    async def messages(self) -> AsyncIterator[ChannelMessage]:
        """
        The messages of the channel, in the order they arrived.

        It also yields a `ChannelStateChange` when the connection of the
        joined channel drops and when the client joined it again. At most
        ``max_queued_messages`` of the client are kept until they are read;
        when the queue is full, the oldest message is dropped and a warning is
        logged.

        :raises NotConnectedError: If the client is not connected, or is closed
            while waiting for a message.
        :raises Exception: The error that ended the channel, such as an
            `AuthorizationError` when the client could not join it again after
            a reconnect, or the error that dropped the connection of a channel
            that was not joined.
        """
        while True:
            if self.message_stream.empty():
                message = await self.socket._next_message(self.message_stream)
            else:
                message = self.message_stream.get_nowait()
            if isinstance(message, ChannelStateChange):
                yield message
                continue
            if isinstance(message, _ChannelFailed):
                raise message.error
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
        self._rejoin_pending = False
        needs_leave = self.state in (ChannelStates.JOINED, ChannelStates.JOINING)
        self.state = ChannelStates.LEAVING
        self.socket._remove_channel(self)
        try:
            if needs_leave:
                await self._send_event(ChannelEvents.leave, payload={})
        finally:
            self.state = ChannelStates.CLOSED
            self._enqueue(
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

        The client tracks it again when it joins the channel again after a
        reconnect.

        :param user_status: Dictionary containing the user's presence information
        """
        reply = await self.send_presence("track", user_status)
        if isinstance(reply.payload, SuccessReplyMessage):
            self._tracked = user_status
        return reply

    async def untrack(self) -> ReplyMessage:
        """
        Stop tracking presence for the current user.
        """
        self._tracked = None
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
