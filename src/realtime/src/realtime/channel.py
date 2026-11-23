from __future__ import annotations

import asyncio
import contextlib
import weakref
from collections.abc import Buffer, Sequence
from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Any, Self, overload
from urllib.parse import quote

import websockets
from postgrest import Column, Filter, NullableColumn, Table
from pydantic import ValidationError
from supabase_utils._logging import get_logger
from supabase_utils.http.request import Request, validate_request_timeout
from supabase_utils.types import JSONParser

from ._redact import RedactingLoggerAdapter, describe
from .exceptions import (
    AuthorizationError,
    ChannelClosedError,
    ChannelNotJoinedError,
    NotConnectedError,
    PushRejectedError,
    RealtimeAPIError,
    RealtimeError,
    RealtimeTimeoutError,
    _is_fatal,
    _join_error,
)
from .message import (
    BroadcastMessage,
    ChannelCloseMessage,
    ChannelErrorMessage,
    ErrorReplyMessage,
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
    BroadcastPersistence,
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
    from collections.abc import AsyncGenerator, AsyncIterator, Mapping

    from supabase_utils.http.request import Response
    from supabase_utils.types import JSON
    from yarl import URL

    from .client import RealtimeClient
    from .message import PostgresRowChange

logger = RedactingLoggerAdapter(get_logger("realtime.channel"))


@dataclass(frozen=True)
class RealtimeChannelOptions:
    broadcast_ack: bool = False
    broadcast_self: bool = False
    broadcast_replay_since: int | None = None
    broadcast_replay_limit: int | None = None
    broadcast_replication_ready: bool = False
    presence_key: str = ""
    presence_enabled: bool = False
    """Turn presence on even when the channel has no presence listener."""
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
        """
        Configure presence for the channel.

        :param key: The key this connection's presence goes under. The server
            picks a new one on each join when it is empty.
        :param enabled: Turn presence on even when the channel has no
            listener from `RealtimeChannel.presence_events()` at subscribe,
            for an app that only reads `RealtimeChannel.presence_state()`.
        """
        return replace(self, presence_key=key, presence_enabled=enabled)

    def private(self, private: bool = False) -> RealtimeChannelOptions:
        return replace(self, is_private=private)

    @overload
    def postgres_changes(
        self,
        event: RealtimePostgresChangesListenEvent,
        table: str | None = None,
        schema: str = "public",
        filter: str | None = None,
        id: int | None = None,
        select: Sequence[str] | None = None,
    ) -> RealtimeChannelOptions: ...

    @overload
    def postgres_changes[Row](
        self,
        event: RealtimePostgresChangesListenEvent,
        table: Table[Row, Any, Any],
        schema: str | None = None,
        filter: Filter[Row] | str | None = None,
        id: int | None = None,
        select: Sequence[Column[Row, Any] | NullableColumn[Row, Any]]
        | Sequence[str]
        | None = None,
    ) -> RealtimeChannelOptions: ...

    def postgres_changes(
        self,
        event: RealtimePostgresChangesListenEvent,
        table: Table[Any, Any, Any] | str | None = None,
        schema: str | None = None,
        filter: Filter[Any] | str | None = None,
        id: int | None = None,
        select: Sequence[Column[Any, Any] | NullableColumn[Any, Any]]
        | Sequence[str]
        | None = None,
    ) -> RealtimeChannelOptions:
        """
        Listen for Postgres database changes.

        :param event: The change event to listen for (``INSERT``, ``UPDATE``, ``DELETE`` or ``*``)
        :param table: The table to monitor, by name or as a typed ``Table``.
            Defaults to all tables
        :param schema: The database schema to monitor. Defaults to the schema of
            a typed ``Table``, and to ``public``
        :param filter: Optional filter, evaluated server-side, as a typed
            ``Filter`` of the table or as a string in the form
            ``column=operator.value`` (e.g. ``"id=eq.1"`` or ``"title=like.%foo%"``).
            Supported operators: ``eq``, ``neq``, ``lt``, ``lte``, ``gt``, ``gte``,
            ``in`` (``"status=in.(active,pending)"``), ``like``, ``ilike``, ``is``
            (``"deleted_at=is.null"``), ``match``, ``imatch`` (POSIX regex),
            ``isdistinct`` (NULL-safe inequality). Any operator can be negated with
            the ``not.`` prefix (e.g. ``"status=not.in.(draft,archived)"``). Combine
            multiple conditions with commas to apply them as an ``AND``
            (e.g. ``"amount=gt.100,status=in.(open,pending)"``).
            A typed filter joins its ``&`` conditions with commas and sends ``~``
            on one condition as ``not.``; it raises ``ValueError`` for a ``|`` and
            for a ``~`` on a group, which the filter string cannot express:

                Messages.room_id.eq(200) & ~Messages.status.in_(["draft"])

        :param select: Optional list of columns to receive instead of the full row.
            Reduces payload size (helpful for large ``bytea``/``jsonb`` columns). The
            listed columns must be selectable by the subscribing role. With a typed
            ``Table`` the primary key is always included, so a change can be told
            apart from the others; read the record with ``Table.decode_partial()``.
        """
        names = None if select is None else _column_names(select)
        if isinstance(table, Table):
            if schema is None:
                schema = table.schema
            if names is not None:
                names += [
                    column.name
                    for column in table.primary_key
                    if column.name not in names
                ]
            table = table.name
        if isinstance(filter, Filter):
            filter = filter._realtime_filter()
        binding = PostgresChangesBinding(
            event=event,
            table=table,
            schema="public" if schema is None else schema,
            filter=filter,
            select=names,
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


def _column_names(
    select: Sequence[Column[Any, Any] | NullableColumn[Any, Any]] | Sequence[str],
) -> list[str]:
    return [column if isinstance(column, str) else column.name for column in select]


@dataclass(frozen=True)
class ChannelStateChange:
    """
    Yielded by `RealtimeChannel.messages` when the connection of a joined
    channel drops, with the state `ERRORED` and the error that dropped it, or
    when `RealtimeClient.aclose()` closes it, with the state `ERRORED` and no
    error, and when the client joined the channel again, with the state
    `JOINED`.
    """

    state: ChannelStates
    error: Exception | None = None


@dataclass(frozen=True)
class _ChannelFailed:
    error: Exception


QueuedMessage = Message | ChannelStateChange | _ChannelFailed

QueuedPresenceEvent = PresenceEvent | _ChannelFailed

ChannelMessage = (
    SystemMessage
    | BroadcastMessage
    | PostgresChangesMessage
    | ChannelErrorMessage
    | ChannelCloseMessage
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
        self._presence_enabled = False
        self._presence_on = False
        self._presence_listeners: dict[asyncio.Queue[QueuedPresenceEvent], bool] = {}
        self._closed: asyncio.Future[Message] | None = None
        self._system_error: str | None = None
        self._dropping_messages = False
        self.message_stream: asyncio.Queue[QueuedMessage] = asyncio.Queue(
            maxsize=socket.max_queued_messages
        )
        self.broadcast_endpoint_url = self._broadcast_endpoint_url()

    @property
    def joined(self) -> bool:
        return self.state == ChannelStates.JOINED

    def _receive(self, message: Message) -> None:
        if message.event == ChannelEvents.system:
            self._remember_system_error(message)
        elif message.event not in (ChannelEvents.error, ChannelEvents.close):
            self._system_error = None
        if message.event in (ChannelEvents.error, ChannelEvents.close):
            if message.join_ref is not None and message.join_ref != self.join_ref:
                logger.debug("Ignoring %s of an earlier join", describe(message))
                return
            self._fail_pending_pushes()
            if message.event == ChannelEvents.error:
                self._on_error()
            else:
                self._on_close()
        if message.event in (ChannelEvents.presence_state, ChannelEvents.presence_diff):
            self._apply_presence(message)
            return
        self._enqueue(message)

    def _remember_system_error(self, message: Message) -> None:
        reason = message.payload.get("message")
        error = message.payload.get("status") == "error" and isinstance(reason, str)
        self._system_error = reason if error else None

    def _fail_pending_pushes(self) -> None:
        closed = self._closed
        self._closed = None
        if closed is None or closed.done():
            return
        closed.set_exception(ChannelClosedError(self.topic, self._system_error))
        closed.exception()

    def _apply_presence(self, message: Message) -> None:
        try:
            server_message = ServerMessageAdapter.validate_python(message)
        except ValueError:
            logger.warning(
                "Ignoring an invalid presence message: %s", describe(message)
            )
            return
        if isinstance(server_message, PresenceStateMessage):
            events = self.presence._on_state_event(
                server_message.payload, message.join_ref
            )
        elif isinstance(server_message, PresenceDiffMessage):
            events = self.presence._on_diff_event(
                server_message.payload, message.join_ref
            )
        else:
            return
        self._emit_presence(events)

    def _emit_presence(self, events: Sequence[QueuedPresenceEvent]) -> None:
        for event in events:
            for queue, dropping in list(self._presence_listeners.items()):
                self._presence_listeners[queue] = self._put(queue, event, dropping)

    def _enqueue(self, message: QueuedMessage) -> None:
        self._dropping_messages = self._put(
            self.message_stream, message, self._dropping_messages
        )

    def _put[T](self, queue: asyncio.Queue[T], message: T, dropping: bool) -> bool:
        if queue.empty():
            dropping = False
        elif queue.full():
            queue.get_nowait()
            if not dropping:
                logger.warning(
                    "a message queue of channel %s is full, dropping its oldest "
                    "messages until it is read",
                    self.topic,
                )
            dropping = True
        queue.put_nowait(message)
        return dropping

    def _fail(self, error: Exception) -> None:
        self._enqueue(_ChannelFailed(error))
        self._emit_presence([_ChannelFailed(error)])

    def _wait_for_rejoin(self, error: Exception | None) -> bool:
        if self._rejoin_pending:
            self.state = ChannelStates.ERRORED
            return True
        if self.state != ChannelStates.JOINED:
            return False
        logger.info("channel %s lost its connection", self.topic)
        self.state = ChannelStates.ERRORED
        self._rejoin_pending = True
        self._enqueue(ChannelStateChange(ChannelStates.ERRORED, error))
        return True

    def _on_connection_lost(self, error: Exception) -> bool:
        if self._wait_for_rejoin(error):
            return True
        self._on_error()
        self._fail(error)
        return False

    def _on_client_stopped(self) -> None:
        if self.state == ChannelStates.JOINING:
            self._subscribe_attempt = None
        self._fail_pending_pushes()
        if self._wait_for_rejoin(None):
            return
        self.state = ChannelStates.CLOSED
        self._emit_presence(self.presence._on_unsubscribe())

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
        try:
            await self.unsubscribe()
        except (websockets.ConnectionClosed, OSError, NotConnectedError) as error:
            logger.warning("could not leave channel %s: %r", self.topic, error)

    async def subscribe(self) -> ReplyMessage:
        """
        Join the channel, connecting the client first if it is not connected.

        When the connection of the joined channel drops, the client joins it
        again on its own once it reconnected. After `RealtimeClient.aclose()`,
        it joins it again on the next connect.

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
        self._presence_enabled = self.options.presence_enabled or bool(
            self._presence_listeners
        )
        await self.socket.connect()
        await self.socket._refresh_token()
        return await self._join(attempt, clear_messages=True)

    async def _join(self, attempt: object, *, clear_messages: bool) -> ReplyMessage:
        self._raise_if_join_was_stopped(attempt)
        self._raise_if_topic_is_taken()
        self.socket.channels[self.topic] = self
        if clear_messages:
            while not self.message_stream.empty():
                self.message_stream.get_nowait()
            for queue in self._presence_listeners:
                events = [queue.get_nowait() for _ in range(queue.qsize())]
                for event in events:
                    if not isinstance(event, _ChannelFailed):
                        queue.put_nowait(event)
        options = replace(self.options, presence_enabled=self._presence_enabled)
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
        self._fail_pending_pushes()
        self.join_ref = join_ref
        self._system_error = None
        self._closed = asyncio.get_running_loop().create_future()
        self.presence._on_join(join_ref)
        self._presence_on = self._presence_enabled
        self.state = ChannelStates.JOINING
        failure = self.socket._connection_failure
        try:
            msg = await self.socket._send(message)
        except asyncio.CancelledError:
            await self._stop_cancelled_join(attempt, join_ref, failure)
            raise
        except Exception as exc:
            self._raise_if_join_was_stopped(attempt)
            self.state = ChannelStates.CLOSED
            connection_failed = failure is not None and failure.done()
            if isinstance(exc, RealtimeTimeoutError) and not connection_failed:
                await self._leave_cancelled_join(join_ref, failure)
                raise
            if connection_failed or isinstance(
                exc, (websockets.ConnectionClosed, OSError)
            ):
                raise NotConnectedError(
                    "RealtimeChannel.subscribe",
                    f"the connection dropped before the join of {self.topic!r} completed",
                ) from exc
            raise
        logger.debug("join reply on %s: %s", self.topic, msg.payload.status)
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

    def _fail_rejoin(self, error: Exception) -> None:
        logger.error("gave up joining channel %s again: %r", self.topic, error)
        self._rejoin_pending = False
        self._rejoin_authorization_failed = False
        self._subscribe_attempt = None
        self.state = ChannelStates.CLOSED
        self._fail_pending_pushes()
        self._emit_presence(self.presence._on_unsubscribe())
        self._fail(error)

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
            async with asyncio.timeout(self.socket.timeout):
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
        joined channel drops or the client is closed, and when the client
        joined it again. At most
        ``max_queued_messages`` of the client are kept until they are read;
        when the queue is full, the oldest message is dropped and a warning is
        logged. Presence events are not yielded here: read them from
        `presence_events()`.

        :raises NotConnectedError: If the client is not connected, is closed
            while waiting for a message, or the channel was unsubscribed and
            its queued messages were read.
        :raises Exception: The error that ended the channel, such as an
            `AuthorizationError` when the client could not join it again after
            a reconnect, or the error that dropped the connection of a channel
            that was not joined, like a channel the server closed.
        """
        while True:
            if self.message_stream.empty():
                if self.socket.channels.get(self.topic) is not self:
                    raise NotConnectedError(
                        "RealtimeChannel.messages", "the channel was unsubscribed"
                    )
                message = await self.socket._next_message(self.message_stream)
            else:
                message = self.message_stream.get_nowait()
            if isinstance(message, ChannelStateChange):
                yield message
                continue
            if isinstance(message, _ChannelFailed):
                raise message.error
            server_message = ServerMessageAdapter.validate_python(message)
            if not isinstance(
                server_message, (PresenceStateMessage, PresenceDiffMessage)
            ):
                yield server_message

    def presence_events(self) -> AsyncIterator[PresenceEvent]:
        """
        Listen for the presence events of the channel.

        The listener is registered when this is called, so call it before
        `subscribe()`: a channel with a presence listener at subscribe turns
        presence on. For each change of the presence state, it yields a
        `PresenceJoin` per key with joined presences, then a `PresenceLeave`
        per key with left presences, then a `PresenceSync`. Unsubscribing
        yields a `PresenceLeave` for every key, then a `PresenceSync`. At most
        ``max_queued_messages`` of the client are kept until they are read.
        The listener is removed when the iterator is closed or garbage
        collected.

        :raises RealtimeError: If the channel is joining or joined with
            presence off, since the listener would never receive an event.
            Add the listener before `subscribe()`, or turn presence on with
            `RealtimeChannelOptions.presence(enabled=True)`.
        """
        joining_or_joined = self.state in (
            ChannelStates.JOINING,
            ChannelStates.JOINED,
            ChannelStates.ERRORED,
        )
        if joining_or_joined and not self._presence_on:
            raise RealtimeError(
                f"channel {self.topic!r} joined with presence off, so a presence "
                "listener would never receive an event; call presence_events() "
                "before subscribe() or set RealtimeChannelOptions.presence(enabled=True)"
            )
        queue: asyncio.Queue[QueuedPresenceEvent] = asyncio.Queue(
            maxsize=self.socket.max_queued_messages
        )
        self._presence_listeners[queue] = False
        events = self._listen_presence(queue)
        weakref.finalize(events, self._presence_listeners.pop, queue, None)
        return events

    async def _listen_presence(
        self, queue: asyncio.Queue[QueuedPresenceEvent]
    ) -> AsyncGenerator[PresenceEvent]:
        try:
            while True:
                if queue.empty():
                    event = await self.socket._next_message(
                        queue, "RealtimeChannel.presence_events"
                    )
                else:
                    event = queue.get_nowait()
                if isinstance(event, _ChannelFailed):
                    raise event.error
                yield event
        finally:
            self._presence_listeners.pop(queue, None)

    async def unsubscribe(self) -> None:
        self._subscribe_attempt = None
        self._rejoin_pending = False
        needs_leave = self.state in (ChannelStates.JOINED, ChannelStates.JOINING)
        self.state = ChannelStates.LEAVING
        self.socket._remove_channel(self)
        self._emit_presence(self.presence._on_unsubscribe())
        self._fail_pending_pushes()
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
    async def track(self, user_status: Mapping[str, JSON]) -> None:
        """
        Publish the presence of this connection, or replace it.

        The server removes it when the channel ends, so after the channel is
        joined again (`messages` yields a `ChannelStateChange` with the state
        `JOINED`), call `track()` again to be present.

        Wait at most ``timeout`` seconds of the client for the reply, or
        wrap the call in ``asyncio.timeout()`` for a shorter wait.

        :param user_status: The presence payload, a JSON object.
        :raises ChannelNotJoinedError: If the channel is not joined.
        :raises PushRejectedError: If the server replies with an error.
        :raises RealtimeTimeoutError: If the server does not reply in time.
        :raises ChannelClosedError: If the channel closes or errors before the
            server replies, for example when the server closes it for going
            over the presence rate limit.
        """
        join_ref = self.join_ref
        await self.send_presence("track", dict(user_status))
        if self.join_ref == join_ref:
            self._presence_on = True

    async def untrack(self) -> None:
        """
        Remove the presence of this connection.

        Wait at most ``timeout`` seconds of the client for the reply, or
        wrap the call in ``asyncio.timeout()`` for a shorter wait.

        :raises ChannelNotJoinedError: If the channel is not joined.
        :raises PushRejectedError: If the server replies with an error.
        :raises RealtimeTimeoutError: If the server does not reply in time.
        :raises ChannelClosedError: If the channel closes or errors before the
            server replies.
        """
        await self.send_presence("untrack", {})

    def presence_state(self) -> RealtimePresenceState:
        """
        Get a snapshot of the presence state of this channel.

        Later presence messages do not change the returned value.

        :return: Dictionary mapping presence keys to lists of presence payloads
        """
        return {key: list(presences) for key, presences in self.presence.state.items()}

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
        self,
        event: str,
        data: JSON | Buffer,
        *,
        persist: BroadcastPersistence | None = None,
    ) -> ReplyMessage | None:
        """
        Send a broadcast message through this channel.

        The channel must be joined. To broadcast without subscribing, use
        `http_send()`. Without ``broadcast_ack``, returning means the message
        was written to the connection, not that the server received it. With
        it, the call waits at most ``timeout`` seconds of the client for the
        server's reply and returns it.

        :param event: The name of the broadcast event
        :param data: The payload to broadcast. A bytes-like object, such as
            ``bytes``, ``bytearray`` or ``memoryview``, is sent as a binary frame,
            and receivers get it as ``bytes`` in ``BroadcastPayload.payload``.
            Anything else is sent as JSON.
        :param persist: Stores the message on the server so that it can be
            replayed. Only ``broadcast_ack`` tells whether it was stored.
        :raises ValueError: If ``persist`` is set on a channel that is not
            private, or if the message is sent as a binary frame and the
            topic or the event is longer than 255 bytes in UTF-8.
        :raises ChannelNotJoinedError: If the channel is not joined.
        :raises PushRejectedError: With ``broadcast_ack``, if the server replies
            with an error. Its ``code`` is ``persistence_unauthorized`` or
            ``persistence_failed`` when the message was delivered but not
            stored, and ``persistence_invalid_ttl`` when the server refused
            the ``ttl`` and neither delivered nor stored it.
        :raises RealtimeTimeoutError: With ``broadcast_ack``, if the server does
            not reply in time.
        :raises ChannelClosedError: With ``broadcast_ack``, if the channel closes
            or errors before the server replies.
        :raises websockets.ConnectionClosed: If the connection is closed, or the
            error the `WebSocketConnection` of a custom transport raises.
        :raises Exception: If the connection already failed, the exception that
            failed it, such as a TimeoutError when a heartbeat timed out.
        """
        self._check_persist("send_broadcast", persist)
        if not self.joined:
            raise ChannelNotJoinedError("RealtimeChannel.send_broadcast", self.topic)
        if isinstance(data, Buffer):
            data = bytes(data)
        payload: dict[str, JSON | bytes] = {
            "type": "broadcast",
            "event": event,
            "payload": data,
        }
        if persist is not None:
            payload["meta"] = {"persist": persist._metadata()}
        if not self.options.broadcast_ack:
            await self._send_event_no_wait(ChannelEvents.broadcast, payload)
            return None
        return await self._push("broadcast", ChannelEvents.broadcast, payload)

    async def http_send(
        self,
        event: str,
        data: Mapping[str, JSON] | Buffer,
        *,
        persist: BroadcastPersistence | None = None,
        request_timeout: float | None = None,
    ) -> None:
        """
        Send a broadcast message through the Realtime REST API.

        The channel does not need to be subscribed, and the WebSocket
        connection is not used, so this suits fire and forget broadcasts from
        server code. The request is never retried, since a retry could
        deliver the broadcast twice. Returning means the server accepted the
        broadcast.

        :param event: The name of the broadcast event
        :param data: The payload to broadcast, a JSON object. A bytes-like
            object is sent unchanged as ``application/octet-stream``.
        :param persist: Asks the server to store the message so that it can be
            replayed. The server stores it after it answers, so returning does
            not mean the message was stored.
        :param request_timeout: Seconds the whole call may take. None uses the
            ``timeout`` of the client.
        :raises ValueError: If ``persist`` is set on a channel that is not
            private.
        :raises RealtimeError: If the client has no ``http_session``.
        :raises RealtimeAPIError: If the server answers with a status other
            than 202.
        :raises RealtimeTimeoutError: If the call takes longer than the timeout.
        :raises SupabaseTransportError: If the request fails before a response
            is read.
        """
        validate_request_timeout(request_timeout)
        self._check_persist("http_send", persist)
        session = self.socket.http_session
        if session is None:
            raise RealtimeError(
                "RealtimeChannel.http_send() needs the http_session of the RealtimeClient"
            )
        seconds = self.socket.timeout if request_timeout is None else request_timeout
        deadline = asyncio.timeout(seconds)
        try:
            async with deadline:
                response = await session.send(
                    await self._http_send_request(event, data, persist)
                )
        except TimeoutError:
            if deadline.expired():
                raise RealtimeTimeoutError("broadcast", self.topic, seconds) from None
            raise
        if response.status != 202:
            raise RealtimeAPIError(
                _error_message(response),
                status_code=response.status,
                response=response,
            )

    async def _http_send_request(
        self,
        event: str,
        data: Mapping[str, JSON] | Buffer,
        persist: BroadcastPersistence | None,
    ) -> Request:
        if isinstance(data, Buffer):
            content, content_type = bytes(data), "application/octet-stream"
        else:
            content, content_type = JSONParser.dump_json(dict(data)), "application/json"
        headers = self.socket.headers.override("Content-Type", content_type)
        if token := await self.socket._access_token():
            headers = headers.override("Authorization", f"Bearer {token}")
        url = self.broadcast_endpoint_url.joinpath(
            quote(self.topic.removeprefix("realtime:"), safe=""),
            "events",
            quote(event, safe=""),
            encoded=True,
        )
        if self.options.is_private:
            url = url.update_query(private="true")
        if persist is not None:
            url = url.update_query(persist._query())
        return Request(
            url=url,
            method="POST",
            headers=headers,
            content=content,
            delay=None,
            retry=False,
        )

    # Internal methods

    def _check_persist(
        self, func_name: str, persist: BroadcastPersistence | None
    ) -> None:
        if persist is not None and not self.options.is_private:
            raise ValueError(
                f"RealtimeChannel.{func_name}() can only persist a message on a "
                f"private channel, and {self.topic!r} is public; nothing was sent"
            )

    def _broadcast_endpoint_url(self) -> URL:
        return self.socket.http_endpoint.joinpath("api", "broadcast")

    async def send_presence(self, event: str, data: JSON) -> None:
        """
        Send a ``presence`` message and wait for the server's reply.

        :raises ChannelNotJoinedError: If the channel is not joined.
        :raises PushRejectedError: If the server replies with an error.
        :raises RealtimeTimeoutError: If the server does not reply in time.
        :raises ChannelClosedError: If the channel closes or errors before the
            server replies.
        """
        if not self.joined:
            raise ChannelNotJoinedError(f"RealtimeChannel.{event}", self.topic)
        await self._push(
            f"presence {event}",
            ChannelEvents.presence,
            {"event": event, "payload": data},
        )

    async def _push(
        self, label: str, event: ChannelEvents, payload: Mapping[str, JSON | bytes]
    ) -> ReplyMessage:
        message = Message(
            topic=self.topic,
            event=event,
            ref=self.socket._make_ref(),
            join_ref=self.join_ref,
            payload=payload,
        )
        reply = await self.socket._send(message, channel_closed=self._closed)
        if isinstance(reply.payload, ErrorReplyMessage):
            reason = reply.payload.response.get("reason")
            code = reply.payload.response.get("error")
            raise PushRejectedError(
                label,
                self.topic,
                reason if isinstance(reason, str) else None,
                code=code if isinstance(code, str) else None,
            )
        return reply


def _error_message(response: Response) -> str:
    try:
        body = JSONParser.validate_json(response.content)
    except ValidationError:
        body = None
    if isinstance(body, dict):
        for key in ("error", "message"):
            if isinstance(message := body.get(key), str) and message:
                return message
    return f"the server answered the broadcast with status {response.status}"
