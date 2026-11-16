import asyncio
import logging
from collections.abc import AsyncGenerator, Awaitable, Callable, Generator
from types import TracebackType
from warnings import warn

import websockets
from supabase_utils.http.retry import RetryPolicy
from websockets.asyncio.client import ClientConnection
from websockets.exceptions import InvalidStatus
from yarl import URL

from ._redact import RedactingLoggerAdapter
from ._serializer import decode, encode
from .channel import QueuedMessage, RealtimeChannel, RealtimeChannelOptions
from .exceptions import (
    AuthorizationError,
    NotConnectedError,
    RealtimeError,
    RealtimeTimeoutError,
)
from .message import ErrorReplyMessage, Message, ReplyMessage
from .types import (
    DEFAULT_HEARTBEAT_INTERVAL,
    DEFAULT_HEARTBEAT_TIMEOUT,
    DEFAULT_MAX_QUEUED_MESSAGES,
    DEFAULT_TIMEOUT,
    PHOENIX_CHANNEL,
    PROTOCOL_VERSION,
    ChannelEvents,
    ConnectionState,
    HeartbeatStatus,
    validate_heartbeat,
    validate_push_options,
)

logger = RedactingLoggerAdapter(logging.getLogger(__name__))
websockets_logger = RedactingLoggerAdapter(logging.getLogger("websockets.client"))


def _loggable(frame: str | bytes) -> str:
    if isinstance(frame, str):
        return frame
    return f"<binary frame of {len(frame)} bytes>"


def _raise_connection_failure(failure: asyncio.Future[Message]) -> None:
    if failure.done() and not failure.cancelled():
        failure.result()


async def _wait_or_raise(
    fut: asyncio.Future[Message], failure: asyncio.Future[Message]
) -> Message:
    done, _pending = await asyncio.wait(
        (fut, failure), return_when=asyncio.FIRST_COMPLETED
    )
    if fut not in done:
        fut.cancel()
        await failure
    return fut.result()


def _publish[T](listeners: set[asyncio.Queue[T]], value: T) -> None:
    for queue in listeners:
        queue.put_nowait(value)


def normalize_url(url: URL, token: str | None) -> URL:
    if url.scheme not in {"ws", "wss", "http", "https"}:
        raise ValueError("url must be a valid WebSocket URL or HTTP URL string")
    url = (
        url.joinpath("websocket")
        .with_query(url.query)
        .update_query(vsn=PROTOCOL_VERSION)
    )
    if token:
        url = url.update_query(apikey=token)
    if url.scheme in {"ws", "wss"}:
        return url
    if url.scheme == "https":
        return url.with_scheme("wss")
    return url.with_scheme("ws")


class connect_once:
    """
    Open a realtime connection when awaited or entered as an async context manager.

    :param url: The realtime URL of the project
    :param token_callback: Returns the access token, awaited on connect and on every heartbeat
    :param heartbeat_interval: Seconds between heartbeats, must be positive
    :param heartbeat_timeout: Seconds to wait for a heartbeat reply before the connection is considered lost, must be positive
    :param timeout: Seconds to wait for the server to reply to a join, a leave, a presence update or an acknowledged broadcast, must be positive
    :param max_queued_messages: Messages each channel keeps until they are read from `RealtimeChannel.messages`, must be positive
    """

    def __init__(
        self,
        url: str,
        token_callback: Callable[[], Awaitable[str | None]] | None = None,
        heartbeat_interval: float = DEFAULT_HEARTBEAT_INTERVAL,
        heartbeat_timeout: float = DEFAULT_HEARTBEAT_TIMEOUT,
        timeout: float = DEFAULT_TIMEOUT,
        max_queued_messages: int = DEFAULT_MAX_QUEUED_MESSAGES,
    ) -> None:
        self.client = RealtimeClient(
            url,
            token_callback,
            heartbeat_interval=heartbeat_interval,
            heartbeat_timeout=heartbeat_timeout,
            timeout=timeout,
            max_queued_messages=max_queued_messages,
        )

    def __await__(self) -> Generator[None, None, "RealtimeClient"]:
        return self.__await_impl__().__await__()

    async def __await_impl__(self) -> "RealtimeClient":
        await self.client.connect()
        return self.client

    async def __aenter__(self) -> "RealtimeClient":
        return await self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        await self.client.aclose()


RECONNECT_BASE_DELAY = 1.0
MAX_RECONNECT_DELAY = 30.0
_RECONNECT_BACKOFF = RetryPolicy(
    base_delay=RECONNECT_BASE_DELAY, max_delay=MAX_RECONNECT_DELAY, jitter=1.0
)


def reconnect_delay(attempt: int) -> float:
    """
    Seconds to wait before reconnect attempt `attempt`, counted from 1.

    Full jitter: a random wait between 0 and the exponential backoff, which
    doubles from `RECONNECT_BASE_DELAY` and is capped at `MAX_RECONNECT_DELAY`.
    """
    return _RECONNECT_BACKOFF.backoff(attempt)


def _refused_with(error: Exception) -> int | None:
    if isinstance(error, InvalidStatus):
        return error.response.status_code
    return None


class RealtimeClient:
    """
    A realtime client that connects when the first channel subscribes and
    disconnects when the last channel is removed.

    When the connection drops, it reconnects with full-jitter backoff until it
    is closed, and joins its joined channels again.

    :param url: The realtime URL of the project
    :param token_callback: Returns the access token, awaited on connect, on every channel join and on every heartbeat.
        An error it raises fails the connect or the join. After a heartbeat it is logged and the channels keep their token.
    :param heartbeat_interval: Seconds between heartbeats, must be positive
    :param heartbeat_timeout: Seconds to wait for a heartbeat reply before the connection is considered lost, must be positive
    :param timeout: Seconds to wait for the server to reply to a join, a leave, a presence update or an acknowledged broadcast, must be positive
    :param max_queued_messages: Messages each channel keeps until they are read from `RealtimeChannel.messages`, must be positive.
        When a channel's queue is full, its oldest message is dropped and a warning is logged.
    """

    def __init__(
        self,
        url: str | URL,
        token_callback: Callable[[], Awaitable[str | None]] | None = None,
        heartbeat_interval: float = DEFAULT_HEARTBEAT_INTERVAL,
        heartbeat_timeout: float = DEFAULT_HEARTBEAT_TIMEOUT,
        timeout: float = DEFAULT_TIMEOUT,
        max_queued_messages: int = DEFAULT_MAX_QUEUED_MESSAGES,
    ) -> None:
        validate_heartbeat(heartbeat_interval, heartbeat_timeout)
        validate_push_options(timeout, max_queued_messages)
        self.url = URL(url)
        self.last_token: str | None = None
        self.get_access_token = token_callback
        self.http_endpoint = self.url.with_scheme("https").with_path("")

        self._ws_connection: ClientConnection | None = None
        self._connection_failure: asyncio.Future[Message] | None = None
        self._connected_at = 0.0
        self._session: asyncio.Future[None] | None = None
        self._listen_task: asyncio.Task[None] | None = None
        self._heartbeat_task: asyncio.Task[None] | None = None
        self._reconnect_task: asyncio.Task[None] | None = None
        self._reconnect_attempt = 0
        self._connect_lock = asyncio.Lock()
        self._auth_lock = asyncio.Lock()
        self._token_is_manual = False
        self._connection_state = ConnectionState.CLOSED
        self._connection_state_listeners: set[asyncio.Queue[ConnectionState]] = set()
        self._heartbeat_listeners: set[asyncio.Queue[HeartbeatStatus]] = set()

        self.ref = 0
        self.channels: dict[str, RealtimeChannel] = {}
        self.message_refs: dict[str, asyncio.Future[Message]] = {}

        self.heartbeat_interval = heartbeat_interval
        self.heartbeat_timeout = heartbeat_timeout
        self.timeout = timeout
        self.max_queued_messages = max_queued_messages

    async def connect(self) -> None:
        """
        Open the WebSocket connection, unless one is already open.

        Subscribing to a channel calls this, so it is only needed to connect
        before the first subscribe. When an open connection drops, the client
        reconnects on its own and joins its joined channels again.
        """
        async with self._connect_lock:
            if self._is_connected():
                return
            await self._drop_connection()
            self._set_connection_state(ConnectionState.CONNECTING)
            try:
                token = (
                    await self.get_access_token()
                    if self.get_access_token is not None
                    else None
                )
                websocket = await websockets.connect(
                    str(normalize_url(self.url, token)), logger=websockets_logger
                )
            except BaseException:
                self._set_connection_state(ConnectionState.CLOSED)
                raise
            if token and self.last_token is not None and not self._token_is_manual:
                self.last_token = token
            loop = asyncio.get_running_loop()
            failure: asyncio.Future[Message] = loop.create_future()
            self._ws_connection = websocket
            self._connection_failure = failure
            self._connected_at = loop.time()
            if self._session is None:
                self._session = loop.create_future()
            self._listen_task = asyncio.create_task(self._listen(websocket, failure))
            self._heartbeat_task = asyncio.create_task(self._heartbeat(failure))
            self._set_connection_state(ConnectionState.CONNECTED)

    @property
    def connection_state(self) -> ConnectionState:
        """The current state of the WebSocket connection."""
        return self._connection_state

    async def connection_states(self) -> AsyncGenerator[ConnectionState, None]:
        """
        Yield the current connection state, then every state the connection
        moves to, until the caller stops iterating.

        A dropped connection moves to `ConnectionState.CLOSED`, and to
        `ConnectionState.CONNECTING` again when the client reconnects.
        """
        queue: asyncio.Queue[ConnectionState] = asyncio.Queue()
        self._connection_state_listeners.add(queue)
        try:
            yield self._connection_state
            while True:
                yield await queue.get()
        finally:
            self._connection_state_listeners.discard(queue)

    async def heartbeats(self) -> AsyncGenerator[HeartbeatStatus, None]:
        """
        Yield the status of every heartbeat sent from the first iteration on,
        until the caller stops iterating.

        Each heartbeat yields `HeartbeatStatus.SENT`, then `HeartbeatStatus.OK`
        when the server acknowledges it. An error reply yields
        `HeartbeatStatus.ERROR`, and no reply within ``heartbeat_timeout``
        yields `HeartbeatStatus.TIMEOUT`. Both drop the connection, which the
        client then reopens.
        """
        queue: asyncio.Queue[HeartbeatStatus] = asyncio.Queue()
        self._heartbeat_listeners.add(queue)
        try:
            while True:
                yield await queue.get()
        finally:
            self._heartbeat_listeners.discard(queue)

    def _set_connection_state(self, state: ConnectionState) -> None:
        if state != self._connection_state:
            self._connection_state = state
            _publish(self._connection_state_listeners, state)

    async def aclose(self) -> None:
        """
        Close the WebSocket connection, if one is open, and stop reconnecting.

        The channels are left unsubscribed. Subscribing to a channel afterwards
        opens a new connection.
        """
        async with self._connect_lock:
            await self._stop()

    async def _close_if_unused(self) -> None:
        async with self._connect_lock:
            if not self.channels:
                await self._stop()

    def _is_connected(self) -> bool:
        return (
            self._ws_connection is not None
            and self._connection_failure is not None
            and not self._connection_failure.done()
        )

    async def _stop(self) -> None:
        if (
            self._reconnect_task is not None
            and self._reconnect_task is not asyncio.current_task()
        ):
            self._reconnect_task.cancel()
        self._reconnect_task = None
        self._reconnect_attempt = 0
        for channel in self.channels.values():
            channel._on_client_stopped()
        await self._drop_connection()
        if self._session is not None:
            self._session.set_result(None)
            self._session = None

    async def _drop_connection(self) -> None:
        websocket = self._ws_connection
        failure = self._connection_failure
        listen_task = self._listen_task
        if self._heartbeat_task is not None:
            self._heartbeat_task.cancel()
        self._ws_connection = None
        self._connection_failure = None
        self._listen_task = None
        self._heartbeat_task = None
        if websocket is not None:
            await websocket.close()
        if listen_task is not None:
            await listen_task
        if failure is not None and failure.done() and not failure.cancelled():
            failure.exception()
        self._set_connection_state(ConnectionState.CLOSED)

    def _connection(
        self, func_name: str
    ) -> tuple[ClientConnection, asyncio.Future[Message]]:
        if self._ws_connection is None or self._connection_failure is None:
            raise NotConnectedError(func_name)
        return self._ws_connection, self._connection_failure

    async def _listen(
        self, websocket: ClientConnection, failure: asyncio.Future[Message]
    ) -> None:
        try:
            while True:
                frame = await websocket.recv()
                if failure.done():
                    logger.debug("Ignoring %s on a failed connection", _loggable(frame))
                    return
                try:
                    message = decode(frame)
                except ValueError as e:
                    logger.error(
                        "Unrecognized message format %s\n%s", _loggable(frame), e
                    )
                    continue
                fut = (
                    self.message_refs.get(message.ref)
                    if message.ref is not None
                    else None
                )
                if fut is not None and not fut.done():
                    fut.set_result(message)
                elif message.event == ChannelEvents.reply:
                    logger.info("Ignoring reply nobody is waiting on: %r", message)
                elif channel := self.channels.get(message.topic):
                    channel._receive(message)
                else:
                    logger.info("Ignoring message: %r", message)
        except Exception as exc:
            self._fail_connection(failure, exc)

    def _fail_connection(
        self, failure: asyncio.Future[Message], exc: Exception
    ) -> None:
        if failure.done():
            return
        failure.set_exception(exc)
        if failure is not self._connection_failure:
            return
        self._set_connection_state(ConnectionState.CLOSED)
        loop = asyncio.get_running_loop()
        if loop.time() - self._connected_at >= MAX_RECONNECT_DELAY:
            self._reconnect_attempt = 0
        rejoin = False
        for channel in list(self.channels.values()):
            rejoin = channel._on_connection_lost(exc) or rejoin
        if rejoin and (self._reconnect_task is None or self._reconnect_task.done()):
            self._reconnect_task = asyncio.create_task(self._reconnect())

    def _channels_to_rejoin(self) -> list[RealtimeChannel]:
        return [
            channel for channel in self.channels.values() if channel._rejoin_pending
        ]

    async def _reconnect(self) -> None:
        refused = False
        while self._channels_to_rejoin():
            self._reconnect_attempt += 1
            delay = reconnect_delay(self._reconnect_attempt)
            logger.info(
                "reconnecting in %.1f seconds (attempt %d)",
                delay,
                self._reconnect_attempt,
            )
            await asyncio.sleep(delay)
            try:
                await self.connect()
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                status = _refused_with(exc)
                if status in (401, 403) and refused:
                    reason = f"the server refused the connection with HTTP {status}"
                    for channel in self._channels_to_rejoin():
                        channel._fail_rejoin(AuthorizationError(channel.topic, reason))
                    return
                refused = status in (401, 403)
                logger.warning("could not reconnect: %r", exc)
                continue
            refused = False
            try:
                await self._refresh_token()
            except asyncio.CancelledError:
                raise
            except Exception as exc:
                logger.warning(
                    "could not refresh the access token to rejoin: %s",
                    type(exc).__name__,
                )
                continue
            await asyncio.gather(
                *(channel._rejoin() for channel in self._channels_to_rejoin())
            )

    async def _next_message(self, queue: asyncio.Queue[QueuedMessage]) -> QueuedMessage:
        session = self._session
        if session is None:
            raise NotConnectedError("RealtimeChannel.messages")
        get = asyncio.ensure_future(queue.get())
        try:
            await asyncio.wait((get, session), return_when=asyncio.FIRST_COMPLETED)
            if get.done():
                return get.result()
            raise NotConnectedError(
                "RealtimeChannel.messages",
                "The realtime client was closed while waiting for messages",
            )
        finally:
            get.cancel()

    async def _heartbeat(self, failure: asyncio.Future[Message]) -> None:
        try:
            while True:
                data = Message(
                    topic=PHOENIX_CHANNEL,
                    event=ChannelEvents.heartbeat,
                    payload={},
                    ref=self._make_ref(),
                )
                logger.info("sending heartbeat")
                _publish(self._heartbeat_listeners, HeartbeatStatus.SENT)
                try:
                    res = await self._send(data, reply_timeout=self.heartbeat_timeout)
                except TimeoutError:
                    _publish(self._heartbeat_listeners, HeartbeatStatus.TIMEOUT)
                    raise
                logger.info("heartbeat response: %r", res)
                if isinstance(res.payload, ErrorReplyMessage):
                    _publish(self._heartbeat_listeners, HeartbeatStatus.ERROR)
                    self._fail_connection(
                        failure,
                        RealtimeError(
                            "the server replied to a heartbeat with an error: "
                            f"{res.payload.response!r}"
                        ),
                    )
                    return
                _publish(self._heartbeat_listeners, HeartbeatStatus.OK)
                await self._refresh_token_after_heartbeat()
                await asyncio.sleep(self.heartbeat_interval)
        except asyncio.CancelledError:
            return
        except (TimeoutError, websockets.ConnectionClosed) as exc:
            self._fail_connection(failure, exc)

    async def _refresh_token_after_heartbeat(self) -> None:
        try:
            await self._refresh_token()
        except websockets.ConnectionClosed:
            raise
        except Exception as exception:
            logger.warning(
                "could not refresh the access token after the heartbeat: %s",
                type(exception).__name__,
            )

    def channel(
        self, topic: str, options: RealtimeChannelOptions | None = None
    ) -> RealtimeChannel:
        """
        Initialize a channel and create a two-way association with the socket.

        If a channel for this topic already exists, that channel is returned
        instead of a new one. Messages are routed to one channel per topic, so
        replacing it would silently stop delivering messages to the existing
        channel.

        :param topic: The topic to subscribe to
        :param options: Optional channel options
        :return: RealtimeChannel instance
        """
        topic = f"realtime:{topic}"
        if existing := self.channels.get(topic):
            if options is not None and options != existing.options:
                warn(
                    f"channel {topic!r} already exists, so the given options are ignored",
                    stacklevel=2,
                )
            return existing
        chan = RealtimeChannel(self, topic, options)
        self.channels[topic] = chan
        return chan

    def get_channels(self) -> list[RealtimeChannel]:
        return list(self.channels.values())

    def _remove_channel(self, channel: RealtimeChannel) -> None:
        if self.channels.get(channel.topic) is channel:
            del self.channels[channel.topic]

    async def remove_channel(self, channel: RealtimeChannel) -> None:
        if self.channels.get(channel.topic) is channel:
            await channel.unsubscribe()

    async def remove_all_channels(self) -> None:
        """
        Unsubscribes and removes all channels from the socket
        :return: None
        """
        results = await asyncio.gather(
            *(channel.unsubscribe() for channel in list(self.channels.values())),
            return_exceptions=True,
        )
        for result in results:
            if isinstance(result, Exception):
                logger.warning("failed to unsubscribe a channel: %r", result)

    async def set_auth(self, token: str | None = None) -> None:
        """
        Set the access token of the connection and send it to every joined channel.

        Channels joined later send it in their join message. Tokens are sent
        in the order of the calls.

        Args:
            token (Optional[str]): The new access token. The token callback no
                longer replaces it on joins, heartbeats and reconnects, until
                this method is called without a token. When None, the token
                callback is awaited for the token and replaces it again from
                then on. Nothing changes if there is no callback or it returns
                no token.

        Channels of a connection that dropped or that the server closed or
        errored are not joined, so nothing is sent to them. The token is still
        stored and sent in the join message when they subscribe again.

        Raises:
            websockets.ConnectionClosed: If the connection closes while the
                token is sent to a joined channel. The token is not stored, so
                calling this method again with the same token sends it again.
        """
        if token is None and self.get_access_token is None:
            logger.warning("tried setting auth but no token callback was registered")
            return
        async with self._auth_lock:
            self._token_is_manual = token is not None
            if token is None:
                await self._send_callback_token()
            else:
                await self._send_token(token)

    async def _refresh_token(self) -> None:
        if self.get_access_token is None:
            return
        async with self._auth_lock:
            if not self._token_is_manual:
                await self._send_callback_token()

    async def _send_callback_token(self) -> None:
        assert self.get_access_token is not None
        token = await self.get_access_token()
        if token:
            await self._send_token(token)

    async def _send_token(self, token: str) -> None:
        if token == self.last_token:
            logger.info("generated access token is still the same, skipping")
            return
        for channel in list(self.channels.values()):
            if channel.joined:
                await channel._send_event_no_wait(
                    ChannelEvents.access_token, {"access_token": token}
                )
        self.last_token = token

    async def _send_token_if_changed(
        self, channel: RealtimeChannel, joined_with: str | None
    ) -> None:
        async with self._auth_lock:
            token = self.last_token
            if token is None or token == joined_with or not channel.joined:
                return
            try:
                await channel._send_event_no_wait(
                    ChannelEvents.access_token, {"access_token": token}
                )
            except Exception as exception:
                logger.warning(
                    "could not send the new access token to %s: %r",
                    channel.topic,
                    exception,
                )

    def _make_ref(self) -> str:
        self.ref += 1
        return f"{self.ref}"

    async def _send(
        self, message: Message, reply_timeout: float | None = None
    ) -> ReplyMessage:
        assert message.ref, "Cannot wait for reponse on a message without ref"

        websocket, failure = self._connection("RealtimeClient._send")
        _raise_connection_failure(failure)
        frame = encode(message)
        logger.debug("sending: %s", _loggable(frame))

        seconds = self.timeout if reply_timeout is None else reply_timeout
        deadline = asyncio.timeout(seconds)
        receive: asyncio.Future[Message] = asyncio.get_running_loop().create_future()
        self.message_refs[message.ref] = receive
        try:
            async with deadline:
                await websocket.send(frame)
                logger.debug("waiting for ref=%r", message.ref)
                response = await _wait_or_raise(receive, failure)
        except TimeoutError:
            if deadline.expired():
                raise RealtimeTimeoutError(
                    message.event, message.topic, seconds
                ) from None
            raise
        finally:
            del self.message_refs[message.ref]

        return ReplyMessage.model_validate(response)

    async def _send_no_wait(self, message: Message) -> None:
        websocket, failure = self._connection("RealtimeClient._send_no_wait")
        _raise_connection_failure(failure)
        frame = encode(message)
        logger.debug("sending: %s", _loggable(frame))
        await websocket.send(frame)

    def endpoint_url(self) -> str:
        return str(normalize_url(self.url, self.last_token))
