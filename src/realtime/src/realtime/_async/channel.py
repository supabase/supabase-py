from __future__ import annotations

import asyncio
import json
import logging
import warnings
from collections.abc import Callable, Coroutine
from typing import TYPE_CHECKING, Any, assert_never
from urllib.parse import quote

import httpx

from realtime.types import (
    BroadcastCallback,
    BroadcastPayload,
    ChannelEvents,
    ChannelStates,
    PostgresChangesCallback,
    PresenceOnJoinCallback,
    PresenceOnLeaveCallback,
    RealtimeAcknowledgementStatus,
    RealtimeChannelConfig,
    RealtimeChannelOptions,
    RealtimeChannelPresenceConfig,
    RealtimePostgresChangesListenEvent,
    RealtimePresenceState,
    RealtimeSubscribeStates,
)

from ..exceptions import RealtimeHTTPError
from ..message import (
    BroadcastMessage,
    ChannelCloseMessage,
    ChannelErrorMessage,
    HeartbeatMessage,
    PostgresChangesMessage,
    PostgresChangesPayload,
    PostgresRowChange,
    PresenceDiffMessage,
    PresenceStateMessage,
    ReplyMessage,
    ReplyPostgresChanges,
    ServerMessage,
    SuccessSystemPayload,
    SystemMessage,
)
from ..transformers import http_endpoint_url
from .presence import (
    AsyncRealtimePresence,
)
from .push import AsyncPush
from .timer import AsyncTimer

if TYPE_CHECKING:
    from .client import AsyncRealtimeClient

logger = logging.getLogger(__name__)

REJOIN_DELAYS_SECONDS = (1, 2, 5, 10)
RATE_LIMITED_REJOIN_DELAY_SECONDS = 30
RATE_LIMIT_ERROR_CODES = (
    "ChannelRateLimitReached",
    "ConnectionRateLimitReached",
    "ClientJoinRateLimitReached",
    "DatabaseConnectionRateLimitReached",
)


def _rejoin_delay(attempt: int) -> float:
    return REJOIN_DELAYS_SECONDS[min(attempt, len(REJOIN_DELAYS_SECONDS)) - 1]


def _is_rate_limit_error(payload: dict[str, Any]) -> bool:
    reason = payload.get("reason")
    return isinstance(reason, str) and reason.startswith(RATE_LIMIT_ERROR_CODES)


class AsyncRealtimeChannel:
    """
    Channel is an abstraction for a topic subscription on an existing socket connection.
    Each Channel has its own topic and a list of event-callbacks that respond to messages.
    Should only be instantiated through `AsyncRealtimeClient.channel(topic)`.
    """

    def __init__(
        self,
        socket: AsyncRealtimeClient,
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
        self.params: RealtimeChannelOptions = (
            params
            if params
            else {
                "config": {
                    "broadcast": {"ack": False, "self": False},
                    "presence": {"key": "", "enabled": False},
                    "private": False,
                }
            }
        )
        self.topic = topic
        self._joined_once = False
        self._resubscribing = False
        self._presence_enabled = False
        self.presence: AsyncRealtimePresence = AsyncRealtimePresence()
        self.state = ChannelStates.CLOSED
        self._push_buffer: list[AsyncPush] = []
        self._background_tasks: set[asyncio.Task[None]] = set()
        self.timeout = self.socket.timeout

        self.join_push: AsyncPush = self._create_join_push()
        self.messages_waiting_for_ack: dict[str, AsyncPush] = {}
        self.broadcast_callbacks: list[BroadcastCallback] = []
        self.system_callbacks: list[Callable[[SuccessSystemPayload], None]] = []
        self.postgres_changes_callbacks: list[PostgresChangesCallback] = []
        self.subscribe_callback: (
            Callable[[RealtimeSubscribeStates, Exception | None], None] | None
        ) = None
        self._subscribe_waiter: asyncio.Future[None] | None = None

        self.rejoin_timer = AsyncTimer(self._rejoin_if_connected, _rejoin_delay)

        self.broadcast_endpoint_url = self._broadcast_endpoint_url()

    def _create_join_push(self) -> AsyncPush:
        join_push = AsyncPush(self, ChannelEvents.join, self.params, self.timeout)

        def on_join_push_ok(payload: ReplyPostgresChanges) -> None:
            self.state = ChannelStates.JOINED
            self.rejoin_timer.reset()
            for push in self._push_buffer:
                self._run_in_background(push.send())
            self._push_buffer = []

        def on_join_push_timeout() -> None:
            if not self.is_joining:
                return

            logger.error(f"join push timeout for channel {self.topic}")
            self.state = ChannelStates.ERRORED
            if self.socket.is_connected:
                self.rejoin_timer.schedule_timeout()

        def on_join_push_error(payload: dict[str, Any]) -> None:
            if not self.is_joining:
                return

            logger.error(f"join push error for channel {self.topic}: {payload}")
            self.state = ChannelStates.ERRORED
            if self.socket.is_connected:
                self.rejoin_timer.schedule_timeout(
                    RATE_LIMITED_REJOIN_DELAY_SECONDS
                    if _is_rate_limit_error(payload)
                    else None
                )

        join_push.receive(RealtimeAcknowledgementStatus.Ok, on_join_push_ok).receive(
            RealtimeAcknowledgementStatus.Error, on_join_push_error
        ).receive(RealtimeAcknowledgementStatus.Timeout, on_join_push_timeout)
        return join_push

    def on_close(self) -> None:
        logger.info(f"channel {self.topic} closed")
        self.rejoin_timer.reset()
        self.state = ChannelStates.CLOSED
        self.socket._remove_channel(self)
        self._notify_subscribe_state(RealtimeSubscribeStates.CLOSED, None)

    def on_error(self, payload: dict[str, Any]) -> None:
        if self.is_leaving or self.is_closed:
            return

        logger.info(f"channel {self.topic} error: {payload}")
        self.state = ChannelStates.ERRORED
        self.rejoin_timer.schedule_timeout()
        self._notify_subscribe_state(
            RealtimeSubscribeStates.CHANNEL_ERROR, Exception(json.dumps(payload))
        )

    def _notify_subscribe_state(
        self, status: RealtimeSubscribeStates, error: Exception | None
    ) -> None:
        try:
            if self.subscribe_callback:
                self.subscribe_callback(status, error)
        finally:
            self._release_subscribe_waiter()

    def _release_subscribe_waiter(self) -> None:
        waiter = self._subscribe_waiter
        self._subscribe_waiter = None
        if waiter is not None and not waiter.done():
            waiter.set_result(None)

    # Properties
    @property
    def is_closed(self) -> bool:
        return self.state == ChannelStates.CLOSED

    @property
    def is_joining(self) -> bool:
        return self.state == ChannelStates.JOINING

    @property
    def is_leaving(self) -> bool:
        return self.state == ChannelStates.LEAVING

    @property
    def is_errored(self) -> bool:
        return self.state == ChannelStates.ERRORED

    @property
    def is_joined(self) -> bool:
        return self.state == ChannelStates.JOINED

    # Core channel methods
    async def subscribe(
        self,
        callback: Callable[[RealtimeSubscribeStates, Exception | None], None]
        | None = None,
    ) -> AsyncRealtimeChannel:
        """
        Subscribe to the channel. Can only be called once per channel instance.

        Waits until the server replies to the join, the join times out, or the
        channel errors or is closed by the server, so the callback has been
        called with the resulting state by the time this returns. Unsubscribing
        or closing the client while the join is pending also ends the wait.
        After unsubscribing, the `CLOSED` callback runs later. After closing
        the client, the join timeout reports `TIMED_OUT` later. Cancelling the
        awaiting task stops the wait but not the join, which keeps running in
        the background.

        :param callback: Optional callback function that receives subscription state updates
                        and any errors that occur during subscription
        :return: The Channel instance for method chaining
        :raises: Exception if called multiple times on the same channel instance
        """
        if not self.socket.is_connected:
            await self.socket.connect()

        if self._joined_once:
            raise Exception(
                "Tried to subscribe multiple times. 'subscribe' can only be called a single time per channel instance"
            )

        self._prepare_join(callback)
        waiter: asyncio.Future[None] = asyncio.get_running_loop().create_future()
        self._subscribe_waiter = waiter
        try:
            await self._rejoin()
            if self.is_leaving:
                self._release_subscribe_waiter()
            await asyncio.shield(waiter)
        except Exception:
            self._release_subscribe_waiter()
            raise
        return self

    def _prepare_join(
        self,
        callback: Callable[[RealtimeSubscribeStates, Exception | None], None] | None,
    ) -> None:
        self.subscribe_callback = callback
        config: RealtimeChannelConfig = self.params["config"]
        broadcast = config.get("broadcast")
        presence = config.get("presence") or RealtimeChannelPresenceConfig(
            key="", enabled=False
        )
        private = config.get("private", False)

        presence_enabled = self.presence._has_callback_attached or presence.get(
            "enabled", False
        )
        presence["enabled"] = presence_enabled

        config_payload: dict[str, Any] = {
            "config": {
                "broadcast": broadcast,
                "presence": presence,
                "private": private,
                "postgres_changes": [
                    c.binding_filter for c in self.postgres_changes_callbacks
                ],
            }
        }

        if self.socket.access_token:
            config_payload["access_token"] = self.socket.access_token

        self.join_push.update_payload(config_payload)
        self._presence_enabled = presence_enabled
        self._joined_once = True

        def on_join_push_ok(payload: ReplyPostgresChanges) -> None:
            server_postgres_changes = payload.postgres_changes

            if server_postgres_changes is None:
                self._notify_subscribe_state(RealtimeSubscribeStates.SUBSCRIBED, None)
                return

            server_ids = []

            for i, postgres_callback in enumerate(self.postgres_changes_callbacks):
                server_binding: PostgresRowChange | None = (
                    server_postgres_changes[i]
                    if i < len(server_postgres_changes)
                    else None
                )
                logger.debug(f"{server_binding}, {postgres_callback}")

                if (
                    server_binding
                    and server_binding.event == postgres_callback.event
                    and server_binding.schema_ == postgres_callback.schema
                    and server_binding.table == postgres_callback.table
                    and server_binding.filter == postgres_callback.filter
                ):
                    server_ids.append(server_binding.id)
                else:
                    self._run_in_background(self.unsubscribe())
                    self.state = ChannelStates.ERRORED
                    self._notify_subscribe_state(
                        RealtimeSubscribeStates.CHANNEL_ERROR,
                        Exception(
                            "mismatch between server and client bindings for postgres changes"
                        ),
                    )
                    return

            for postgres_callback, server_id in zip(
                self.postgres_changes_callbacks, server_ids, strict=True
            ):
                postgres_callback.id = server_id
            self._notify_subscribe_state(RealtimeSubscribeStates.SUBSCRIBED, None)

        def on_join_push_error(payload: dict[str, Any]) -> None:
            self._notify_subscribe_state(
                RealtimeSubscribeStates.CHANNEL_ERROR,
                Exception(json.dumps(payload)),
            )

        def on_join_push_timeout(*args) -> None:
            self._notify_subscribe_state(RealtimeSubscribeStates.TIMED_OUT, None)

        self.join_push.receive(
            RealtimeAcknowledgementStatus.Ok, on_join_push_ok
        ).receive(RealtimeAcknowledgementStatus.Error, on_join_push_error).receive(
            RealtimeAcknowledgementStatus.Timeout, on_join_push_timeout
        )

    async def unsubscribe(self) -> None:
        """
        Unsubscribe from the channel and leave the topic.
        Sets channel state to LEAVING and cleans up timers and pushes.
        """
        self._resubscribing = False
        await self._leave()

    async def _leave(self) -> AsyncPush:
        self.state = ChannelStates.LEAVING
        self._release_subscribe_waiter()

        self.rejoin_timer.reset()
        self.join_push.destroy()

        def _close(*args) -> None:
            logger.info(f"channel {self.topic} leave")
            self.on_close()

        leave_push = AsyncPush(self, ChannelEvents.leave, {}, self.timeout)
        leave_push.receive(RealtimeAcknowledgementStatus.Ok, _close).receive(
            RealtimeAcknowledgementStatus.Error, _close
        ).receive(RealtimeAcknowledgementStatus.Timeout, _close)
        await leave_push.send()
        return leave_push

    async def push(
        self, event: str, payload: dict[str, Any], timeout: int | None = None
    ) -> AsyncPush:
        """
        Push a message to the channel.

        :param event: The event name to push
        :param payload: The payload to send
        :param timeout: Optional timeout in milliseconds
        :return: AsyncPush instance representing the push operation
        :raises: Exception if called before subscribing to the channel
        """
        if not self._joined_once:
            raise Exception(
                f"tried to push '{event}' to '{self.topic}' before joining. Use channel.subscribe() before pushing events"
            )

        timeout = timeout or self.timeout

        push = AsyncPush(self, event, payload, timeout)
        if self._can_push():
            await push.send()
            assert push.ref is not None, "Sent AsyncPush should have a ref"
        else:
            push.start_timeout()
            self._push_buffer.append(push)

        return push

    async def join(self) -> AsyncRealtimeChannel:
        """
        Deprecated: use `subscribe()` instead.

        Joins the channel through `subscribe()`. If the channel has already
        been subscribed, waits for a pending join to settle and returns.

        :return: The Channel instance for method chaining
        """
        warnings.warn(
            "AsyncRealtimeChannel.join() is deprecated and will be removed in a "
            "future major version. Use AsyncRealtimeChannel.subscribe() instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        if self._joined_once:
            if self._subscribe_waiter is not None:
                await asyncio.shield(self._subscribe_waiter)
            return self
        return await self.subscribe()

    def on_broadcast(
        self, event: str, callback: Callable[[BroadcastPayload], None]
    ) -> AsyncRealtimeChannel:
        """
        Set up a listener for a specific broadcast event.

        :param event: The name of the broadcast event to listen for
        :param callback: Function called with the payload when a matching broadcast is received
        :return: The Channel instance for method chaining
        """
        self.broadcast_callbacks.append(
            BroadcastCallback(callback=callback, event=event)
        )
        return self

    def on_postgres_changes(
        self,
        event: RealtimePostgresChangesListenEvent,
        callback: Callable[[PostgresChangesPayload], None],
        table: str | None = None,
        schema: str | None = None,
        filter: str | None = None,
        select: list[str] | None = None,
    ) -> AsyncRealtimeChannel:
        """
        Set up a listener for Postgres database changes.

        :param event: The type of database event to listen for (INSERT, UPDATE, DELETE, or *)
        :param callback: Function called with the payload when a matching change is detected
        :param table: The table name to monitor. Defaults to "*" for all tables
        :param schema: The database schema to monitor. Defaults to "public"
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
        :return: The Channel instance for method chaining
        """
        callback = PostgresChangesCallback(
            callback=callback,
            event=event,
            table=table,
            schema=schema,
            filter=filter,
            select=select,
        )
        self.postgres_changes_callbacks.append(callback)
        return self

    def on_system(
        self, callback: Callable[[SuccessSystemPayload], None]
    ) -> AsyncRealtimeChannel:
        """
        Set up a listener for system events.

        :param callback: The callback function to execute when a system event is received.
        :return: The Channel instance for method chaining.
        """
        self.system_callbacks.append(callback)
        return self

    # Presence methods
    async def track(self, user_status: dict[str, Any]) -> None:
        """
        Track presence status for the current user.

        :param user_status: Dictionary containing the user's presence information
        """
        await self.send_presence("track", user_status)

    async def untrack(self) -> None:
        """
        Stop tracking presence for the current user.
        """
        await self.send_presence("untrack", {})

    def presence_state(self) -> RealtimePresenceState:
        """
        Get the current state of presence on this channel.

        :return: Dictionary mapping presence keys to lists of presence payloads
        """
        return self.presence.state

    def on_presence_sync(self, callback: Callable[[], None]) -> AsyncRealtimeChannel:
        """
        Register a callback for presence sync events.

        :param callback: The callback function to execute when a presence sync event occurs.
        :return: The Channel instance for method chaining.
        """
        self.presence.on_sync(callback)

        self._resubscribe_for_presence()

        return self

    def on_presence_join(
        self, callback: PresenceOnJoinCallback
    ) -> AsyncRealtimeChannel:
        """
        Register a callback for presence join events.

        :param callback: The callback function to execute when a presence join event occurs.
        :return: The Channel instance for method chaining.
        """
        self.presence.on_join(callback)
        self._resubscribe_for_presence()

        return self

    def on_presence_leave(
        self, callback: PresenceOnLeaveCallback
    ) -> AsyncRealtimeChannel:
        """
        Register a callback for presence leave events.

        :param callback: The callback function to execute when a presence leave event occurs.
        :return: The Channel instance for method chaining.
        """
        self.presence.on_leave(callback)
        self._resubscribe_for_presence()
        return self

    # Broadcast methods
    async def send_broadcast(self, event: str, data: Any) -> None:
        """
        Send a broadcast message through this channel.

        :param event: The name of the broadcast event
        :param data: The payload to broadcast
        """
        await self.push(
            ChannelEvents.broadcast,
            {"type": "broadcast", "event": event, "payload": data},
        )

    async def http_send(
        self,
        event: str,
        payload: Any,
        *,
        timeout: float | None = None,
    ) -> None:
        """
        Send a broadcast message through the REST API.

        This always uses the HTTP endpoint, whatever the state of the websocket
        connection, and does not require the channel to be subscribed.
        ``bytes`` payloads are sent as ``application/octet-stream``; any other
        payload is JSON-encoded. Requires Realtime server v2.97.0 or newer.

        :param event: The name of the broadcast event
        :param payload: The payload to broadcast (required)
        :param timeout: Optional timeout in seconds, defaults to the client timeout
        :raises ValueError: If the payload is None
        :raises RealtimeHTTPError: If the request times out or the server rejects it
        """
        if payload is None:
            raise ValueError("Payload is required for http_send()")

        is_binary = isinstance(payload, (bytes, bytearray, memoryview))
        headers = {
            "apikey": self.socket.apikey or "",
            "Content-Type": "application/octet-stream"
            if is_binary
            else "application/json",
        }
        if self.socket.access_token:
            headers["Authorization"] = f"Bearer {self.socket.access_token}"

        sub_topic = self.topic
        if sub_topic.startswith("realtime:"):
            sub_topic = sub_topic[len("realtime:") :]
        url = (
            f"{self.broadcast_endpoint_url}/{quote(sub_topic, safe='')}"
            f"/events/{quote(event, safe='')}"
        )
        params = {"private": "true"} if self.params["config"].get("private") else None

        content = bytes(payload) if is_binary else json.dumps(payload)

        timeout_seconds = timeout or self.timeout
        try:
            async with httpx.AsyncClient(timeout=timeout_seconds) as client:
                response = await client.post(
                    url, headers=headers, params=params, content=content
                )
        except httpx.TimeoutException as e:
            raise RealtimeHTTPError(f"Request timeout: {e}") from e

        if response.status_code == 202:
            return

        if response.status_code == 404:
            raise RealtimeHTTPError(
                "http_send() requires Realtime server v2.97.0 or newer; the endpoint "
                "returned 404. Update your Supabase CLI to a recent version, or "
                "upgrade the Realtime server in your self-hosted setup.",
                status=404,
            )

        error_message = response.reason_phrase
        try:
            error_body = response.json()
            error_message = (
                error_body.get("error") or error_body.get("message") or error_message
            )
        except Exception:
            pass
        raise RealtimeHTTPError(error_message, status=response.status_code)

    # Internal methods

    def _run_in_background(self, coroutine: Coroutine[Any, Any, None]) -> None:
        task = asyncio.create_task(coroutine)
        self._background_tasks.add(task)
        task.add_done_callback(self._background_tasks.discard)

    def _resubscribe_for_presence(self) -> None:
        if not self.is_joined or self._presence_enabled:
            return
        logger.info(
            f"channel {self.topic} resubscribe due to change in presence callbacks on joined channel"
        )
        self._run_in_background(self._resubscribe())

    async def _resubscribe(self) -> None:
        if self._resubscribing or not self.is_joined:
            return
        self._resubscribing = True
        try:
            callback = self.subscribe_callback
            closed: asyncio.Future[None] = asyncio.get_running_loop().create_future()

            def _on_left(*args) -> None:
                if not closed.done():
                    closed.set_result(None)

            leave_push = await self._leave()
            leave_push.receive(RealtimeAcknowledgementStatus.Ok, _on_left).receive(
                RealtimeAcknowledgementStatus.Error, _on_left
            ).receive(RealtimeAcknowledgementStatus.Timeout, _on_left)
            await closed

            if (
                not self._resubscribing
                or self.socket.channels.get(self.topic, self) is not self
            ):
                return

            self.socket.channels[self.topic] = self
            self.join_push = self._create_join_push()
            self._prepare_join(callback)
            if self.socket.is_connected:
                await self._rejoin()
            else:
                self.state = ChannelStates.ERRORED
        finally:
            self._resubscribing = False

    def _broadcast_endpoint_url(self) -> str:
        return f"{http_endpoint_url(self.socket.http_endpoint)}/api/broadcast"

    async def _rejoin(self) -> None:
        if self.is_leaving:
            return
        logger.debug(f"Rejoining channel after reconnection: {self.topic}")
        self.state = ChannelStates.JOINING
        await self.join_push.resend()

    def _can_push(self) -> bool:
        return self.socket.is_connected and self._joined_once

    async def send_presence(self, event: str, data: Any) -> None:
        await self.push(ChannelEvents.presence, {"event": event, "payload": data})

    def _handle_message(self, message: ServerMessage) -> None:
        logger.debug(f"{self.topic} : {message!r}")
        if isinstance(message, SystemMessage):
            if isinstance(message.payload, SuccessSystemPayload):
                for callback in self.system_callbacks:
                    callback(message.payload)
            else:
                self.on_error(dict(message.payload))
        elif isinstance(message, ReplyMessage):
            reply_payload = message.payload
            if message.ref and (
                push := self.messages_waiting_for_ack.pop(message.ref, None)
            ):
                if reply_payload.status == "ok":
                    push.trigger(
                        RealtimeAcknowledgementStatus.Ok, reply_payload.response
                    )
                else:
                    push.trigger(
                        RealtimeAcknowledgementStatus.Error, reply_payload.response
                    )
        elif isinstance(message, BroadcastMessage):
            broadcast_payload = message.payload
            for broadcast_callback in self.broadcast_callbacks:
                broadcast_callback(broadcast_payload)
        elif isinstance(message, PresenceStateMessage):
            self.presence._on_state_event(message.payload)
        elif isinstance(message, PresenceDiffMessage):
            self.presence._on_diff_event(message.payload)
        elif isinstance(message, PostgresChangesMessage):
            payload = message.payload
            for postgres_callback in self.postgres_changes_callbacks:
                postgres_callback(payload)
        elif isinstance(message, ChannelErrorMessage):
            self.on_error(message.payload)
        elif isinstance(message, ChannelCloseMessage):
            self._resubscribing = False
            self.on_close()
        elif isinstance(message, HeartbeatMessage):  # do nothing
            return
        else:
            assert_never(message)

    async def _rejoin_if_connected(self) -> None:
        if self.socket.is_connected:
            await self._rejoin()
