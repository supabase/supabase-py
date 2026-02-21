from __future__ import annotations

import asyncio
import json
import logging
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Mapping, Optional

from typing_extensions import assert_never

from realtime.types import (
    BroadcastCallback,
    BroadcastPayload,
    Callback,
    ChannelEvents,
    ChannelStates,
    PostgresChangesCallback,
    PostgresChangesData,
    PresenceOnJoinCallback,
    PresenceOnLeaveCallback,
    RealtimeAcknowledgementStatus,
    RealtimeChannelBroadcastConfig,
    RealtimeChannelConfig,
    RealtimeChannelOptions,
    RealtimeChannelPresenceConfig,
    RealtimePostgresChangesListenEvent,
    RealtimePresenceState,
    RealtimeSubscribeStates,
)

from ..message import (
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
    SuccessReplyMessage,
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
        params: Optional[RealtimeChannelOptions] = None,
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
        self.presence: AsyncRealtimePresence = AsyncRealtimePresence()
        self.state = ChannelStates.CLOSED
        self._push_buffer: list[AsyncPush] = []
        self.timeout = self.socket.timeout

        self.join_push: AsyncPush = AsyncPush(self, ChannelEvents.join, self.params)
        self.messages_waiting_for_ack: dict[str, AsyncPush] = {}
        self.broadcast_callbacks: list[BroadcastCallback] = []
        self.system_callbacks: list[Callable[[SuccessSystemPayload], None]] = []
        self.postgres_changes_callbacks: list[PostgresChangesCallback] = []
        self.subscribe_callback: Optional[
            Callable[[RealtimeSubscribeStates, Optional[Exception]], None]
        ] = None

        self.rejoin_timer = AsyncTimer(
            self._rejoin_until_connected, lambda tries: 2**tries
        )

        self.broadcast_endpoint_url = self._broadcast_endpoint_url()

        def on_join_push_ok(payload: ReplyPostgresChanges):
            self.state = ChannelStates.JOINED
            self.rejoin_timer.reset()
            for push in self._push_buffer:
                asyncio.create_task(push.send())
            self._push_buffer = []

        def on_join_push_timeout():
            if not self.is_joining:
                return

            logger.error(f"join push timeout for channel {self.topic}")
            self.state = ChannelStates.ERRORED
            self.rejoin_timer.schedule_timeout()

        self.join_push.receive(
            RealtimeAcknowledgementStatus.Ok, on_join_push_ok
        ).receive(RealtimeAcknowledgementStatus.Timeout, on_join_push_timeout)

    def on_close(self):
        logger.info(f"channel {self.topic} closed")
        self.rejoin_timer.reset()
        self.state = ChannelStates.CLOSED
        self.socket._remove_channel(self)

    def on_error(self, payload: dict[str, Any]):
        if self.is_leaving or self.is_closed:
            return

        logger.info(f"channel {self.topic} error: {payload}")
        self.state = ChannelStates.ERRORED
        self.rejoin_timer.schedule_timeout()

    # Properties
    @property
    def is_closed(self):
        return self.state == ChannelStates.CLOSED

    @property
    def is_joining(self):
        return self.state == ChannelStates.JOINING

    @property
    def is_leaving(self):
        return self.state == ChannelStates.LEAVING

    @property
    def is_errored(self):
        return self.state == ChannelStates.ERRORED

    @property
    def is_joined(self):
        return self.state == ChannelStates.JOINED

    # Core channel methods
    async def subscribe(
        self,
        callback: Optional[
            Callable[[RealtimeSubscribeStates, Optional[Exception]], None]
        ] = None,
    ) -> AsyncRealtimeChannel:
        """
        Subscribe to the channel. Can only be called once per channel instance.

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
        else:
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

            config_payload: Dict[str, Any] = {
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
            self._joined_once = True

            def on_join_push_ok(payload: ReplyPostgresChanges):
                server_postgres_changes = payload.postgres_changes

                new_postgres_bindings = []

                if server_postgres_changes:
                    for i, postgres_callback in enumerate(
                        self.postgres_changes_callbacks
                    ):
                        server_binding: Optional[PostgresRowChange] = (
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
                            postgres_callback.id = server_binding.id
                            new_postgres_bindings.append(postgres_callback)
                        else:
                            asyncio.create_task(self.unsubscribe())
                            callback and callback(
                                RealtimeSubscribeStates.CHANNEL_ERROR,
                                Exception(
                                    "mismatch between server and client bindings for postgres changes"
                                ),
                            )
                            return

                self.postgres_changes_callbacks = new_postgres_bindings
                callback and callback(RealtimeSubscribeStates.SUBSCRIBED, None)

            def on_join_push_error(payload: Dict[str, Any]):
                callback and callback(
                    RealtimeSubscribeStates.CHANNEL_ERROR,
                    Exception(json.dumps(payload)),
                )

            def on_join_push_timeout(*args):
                callback and callback(RealtimeSubscribeStates.TIMED_OUT, None)

            self.join_push.receive(
                RealtimeAcknowledgementStatus.Ok, on_join_push_ok
            ).receive(RealtimeAcknowledgementStatus.Error, on_join_push_error).receive(
                RealtimeAcknowledgementStatus.Timeout, on_join_push_timeout
            )

            await self._rejoin()

        return self

    async def unsubscribe(self) -> None:
        """
        Unsubscribe from the channel and leave the topic.
        Sets channel state to LEAVING and cleans up timers and pushes.
        """
        self.state = ChannelStates.LEAVING

        self.rejoin_timer.reset()
        self.join_push.destroy()

        def _close(*args) -> None:
            logger.info(f"channel {self.topic} leave")
            self.on_close()

        leave_push = AsyncPush(self, ChannelEvents.leave, {})
        leave_push.receive(RealtimeAcknowledgementStatus.Ok, _close).receive(
            RealtimeAcknowledgementStatus.Error, _close
        )
        await leave_push.send()

    async def push(
        self, event: str, payload: Dict[str, Any], timeout: Optional[int] = None
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
        Coroutine that attempts to join Phoenix Realtime server via a certain topic.

        :return: Channel
        """
        config = self.params["config"]
        broadcast = config.get("broadcast")
        presence = config.get("presence")
        private = config.get("private", False)

        config_payload: Dict[str, Any] = {
            "config": {
                "broadcast": broadcast,
                "presence": presence,
                "private": private,
                "postgres_changes": [
                    c.binding_filter for c in self.postgres_changes_callbacks
                ],
            }
        }
        message = Message(
            topic=self.topic,
            event=ChannelEvents.join,
            payload={"config": config_payload},
            ref=self.socket._make_ref(),
        )
        await self.socket.send(message)
        return self

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
        table: Optional[str] = None,
        schema: Optional[str] = None,
        filter: Optional[str] = None,
    ) -> AsyncRealtimeChannel:
        """
        Set up a listener for Postgres database changes.

        :param event: The type of database event to listen for (INSERT, UPDATE, DELETE, or *)
        :param callback: Function called with the payload when a matching change is detected
        :param table: The table name to monitor. Defaults to "*" for all tables
        :param schema: The database schema to monitor. Defaults to "public"
        :param filter: Optional filter string to apply
        :return: The Channel instance for method chaining
        """
        callback = PostgresChangesCallback(
            callback=callback, event=event, table=table, schema=schema, filter=filter
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
    async def track(self, user_status: Dict[str, Any]) -> None:
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

        if self.is_joined:
            logger.info(
                f"channel {self.topic} resubscribe due to change in presence callbacks on joined channel"
            )
            asyncio.create_task(self._resubscribe())

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
        if self.is_joined:
            logger.info(
                f"channel {self.topic} resubscribe due to change in presence callbacks on joined channel"
            )
            asyncio.create_task(self._resubscribe())

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
        if self.is_joined:
            logger.info(
                f"channel {self.topic} resubscribe due to change in presence callbacks on joined channel"
            )
            asyncio.create_task(self._resubscribe())
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

    # Internal methods

    async def _resubscribe(self) -> None:
        await self.unsubscribe()
        await self.subscribe()

    def _broadcast_endpoint_url(self):
        return f"{http_endpoint_url(self.socket.http_endpoint)}/api/broadcast"

    async def _rejoin(self) -> None:
        if self.is_leaving:
            return
        logger.debug(f"Rejoining channel after reconnection: {self.topic}")
        self.state = ChannelStates.JOINING
        await self.join_push.resend()

    def _can_push(self):
        return self.socket.is_connected and self._joined_once

    async def send_presence(self, event: str, data: Any) -> None:
        await self.push(ChannelEvents.presence, {"event": event, "payload": data})

    def _handle_message(self, message: ServerMessage):
        logger.debug(f"{self.topic} : {message!r}")
        if isinstance(message, SystemMessage):
            if isinstance(message.payload, SuccessSystemPayload):
                for callback in self.system_callbacks:
                    callback(message.payload)
            else:
                self.on_error(dict(message.payload))
        elif isinstance(message, ReplyMessage):
            reply_payload = message.payload
            if message.ref and (push := self.messages_waiting_for_ack.pop(message.ref, None)):
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
            self.on_close()
        elif isinstance(message, HeartbeatMessage):  # do nothing
            return
        else:
            assert_never(message)

    async def _rejoin_until_connected(self):
        self.rejoin_timer.schedule_timeout()
        if self.socket.is_connected:
            await self._rejoin()
