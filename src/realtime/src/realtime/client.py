import asyncio
import logging
from collections.abc import Awaitable, Callable, Generator
from types import TracebackType
from warnings import warn

import websockets
from supabase_utils.http.errors import SupabaseTransportError
from websockets.asyncio.client import ClientConnection
from yarl import URL

from ._redact import RedactingLoggerAdapter
from ._serializer import decode, encode
from .channel import RealtimeChannel, RealtimeChannelOptions
from .exceptions import MaxRetriesExceeded, NotConnectedError
from .message import Message, ReplyMessage
from .types import (
    DEFAULT_HEARTBEAT_INTERVAL,
    DEFAULT_HEARTBEAT_TIMEOUT,
    PHOENIX_CHANNEL,
    PROTOCOL_VERSION,
    ChannelEvents,
    ChannelStates,
    validate_heartbeat,
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
    """

    def __init__(
        self,
        url: str,
        token_callback: Callable[[], Awaitable[str | None]] | None = None,
        heartbeat_interval: float = DEFAULT_HEARTBEAT_INTERVAL,
        heartbeat_timeout: float = DEFAULT_HEARTBEAT_TIMEOUT,
    ) -> None:
        self.client = RealtimeClient(
            url,
            token_callback,
            heartbeat_interval=heartbeat_interval,
            heartbeat_timeout=heartbeat_timeout,
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


MAX_RECONNECT_DELAY = 60


def exponential_delay(max_retries: int, retry_count: int) -> float | None:
    if retry_count >= max_retries:
        return None
    return float(min(2**retry_count, MAX_RECONNECT_DELAY))


async def automatically_reconnect(
    url: str,
    token_callback: Callable[[], Awaitable[str]],
    client_handler: Callable[["RealtimeClient"], Awaitable[None]],
    max_retries: int = 3,
) -> None:
    loop = asyncio.get_running_loop()
    retries = 0
    while True:
        connected_at: float | None = None
        try:
            async with connect_once(url, token_callback) as client:
                connected_at = loop.time()
                await client_handler(client)
                break
        except (
            websockets.ConnectionClosed,
            TimeoutError,
            OSError,
            SupabaseTransportError,
        ) as e:
            if (
                connected_at is not None
                and loop.time() - connected_at >= MAX_RECONNECT_DELAY
            ):
                retries = 0
            retries += 1
            delay = exponential_delay(max_retries, retries)
            if delay is None:
                raise MaxRetriesExceeded(retries) from e
            await asyncio.sleep(delay)


class RealtimeClient:
    """
    A realtime client that connects when the first channel subscribes and
    disconnects when the last channel is removed.

    :param url: The realtime URL of the project
    :param token_callback: Returns the access token, awaited on connect, on every channel join and on every heartbeat
    :param heartbeat_interval: Seconds between heartbeats, must be positive
    :param heartbeat_timeout: Seconds to wait for a heartbeat reply before the connection is considered lost, must be positive
    """

    def __init__(
        self,
        url: str | URL,
        token_callback: Callable[[], Awaitable[str | None]] | None = None,
        heartbeat_interval: float = DEFAULT_HEARTBEAT_INTERVAL,
        heartbeat_timeout: float = DEFAULT_HEARTBEAT_TIMEOUT,
    ) -> None:
        validate_heartbeat(heartbeat_interval, heartbeat_timeout)
        self.url = URL(url)
        self.last_token: str | None = None
        self.get_access_token = token_callback
        self.http_endpoint = self.url.with_scheme("https").with_path("")

        self._ws_connection: ClientConnection | None = None
        self._connection_failure: asyncio.Future[Message] | None = None
        self._listen_task: asyncio.Task[None] | None = None
        self._heartbeat_task: asyncio.Task[None] | None = None
        self._connect_lock = asyncio.Lock()
        self._auth_lock = asyncio.Lock()

        self.ref = 0
        self.channels: dict[str, RealtimeChannel] = {}
        self.message_refs: dict[str, asyncio.Future[Message]] = {}

        self.heartbeat_interval = heartbeat_interval
        self.heartbeat_timeout = heartbeat_timeout

    async def connect(self) -> None:
        """
        Open the WebSocket connection, unless one is already open.

        Subscribing to a channel calls this, so it is only needed to connect
        before the first subscribe. A connection that failed is replaced by a
        new one, and the channels of the failed one have to subscribe again.
        """
        async with self._connect_lock:
            if self._is_connected():
                return
            await self._disconnect()
            token = (
                await self.get_access_token()
                if self.get_access_token is not None
                else None
            )
            websocket = await websockets.connect(
                str(normalize_url(self.url, token)), logger=websockets_logger
            )
            if token and self.last_token is not None:
                self.last_token = token
            failure: asyncio.Future[Message] = (
                asyncio.get_running_loop().create_future()
            )
            self._ws_connection = websocket
            self._connection_failure = failure
            self._listen_task = asyncio.create_task(self._listen(websocket, failure))
            self._heartbeat_task = asyncio.create_task(self._heartbeat(failure))

    async def aclose(self) -> None:
        """
        Close the WebSocket connection, if one is open.

        The channels are left unsubscribed. Subscribing to a channel afterwards
        opens a new connection.
        """
        async with self._connect_lock:
            await self._disconnect()

    async def _close_if_unused(self) -> None:
        async with self._connect_lock:
            if not self.channels:
                await self._disconnect()

    def _is_connected(self) -> bool:
        return (
            self._ws_connection is not None
            and self._connection_failure is not None
            and not self._connection_failure.done()
        )

    async def _disconnect(self) -> None:
        websocket = self._ws_connection
        failure = self._connection_failure
        listen_task = self._listen_task
        if self._heartbeat_task is not None:
            self._heartbeat_task.cancel()
        self._ws_connection = None
        self._connection_failure = None
        self._listen_task = None
        self._heartbeat_task = None
        for channel in self.channels.values():
            if channel.state == ChannelStates.JOINING:
                channel._subscribe_attempt = None
            channel.state = ChannelStates.CLOSED
        if websocket is not None:
            await websocket.close()
        if listen_task is not None:
            await listen_task
        if failure is not None and failure.done() and not failure.cancelled():
            failure.exception()

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
                try:
                    message = decode(frame)
                except ValueError as e:
                    logger.error(
                        "Unrecognized message format %s\n%s", _loggable(frame), e
                    )
                    continue
                if message.ref is not None and (
                    fut := self.message_refs.get(message.ref)
                ):
                    fut.set_result(message)
                elif message.event == ChannelEvents.reply:
                    logger.info("Ignoring reply nobody is waiting on: %r", message)
                elif channel := self.channels.get(message.topic):
                    await channel.message_stream.put(message)
                else:
                    logger.info("Ignoring message: %r", message)
        except Exception as exc:
            if not failure.done():
                failure.set_exception(exc)

    async def _get_message_or_raise(self, fut: asyncio.Future[Message]) -> Message:
        try:
            _, failure = self._connection("RealtimeChannel.messages")
            return await _wait_or_raise(fut, failure)
        finally:
            fut.cancel()

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
                res = await asyncio.wait_for(
                    self._send(data), timeout=self.heartbeat_timeout
                )
                logger.info("heartbeat response: %r", res)
                await self.set_auth()
                await asyncio.sleep(self.heartbeat_interval)
        except asyncio.CancelledError:
            return
        except (TimeoutError, websockets.ConnectionClosed) as exc:
            if not failure.done():
                failure.set_exception(exc)

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
            token (Optional[str]): The new access token. When None, the token
                callback is awaited for it, and nothing changes if there is no
                callback or it returns no token.

        Raises:
            websockets.ConnectionClosed: If the connection is closed. The token is
                not stored, so calling this method again with the same token sends
                it again.
            Exception: If the connection already failed, the exception that failed
                it, such as a TimeoutError when a heartbeat timed out.
        """
        async with self._auth_lock:
            if token is None:
                if self.get_access_token is None:
                    logger.warning(
                        "tried setting auth but no token callback was registered"
                    )
                    return
                token = await self.get_access_token()
                if not token:
                    return
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

    async def _send(self, message: Message) -> ReplyMessage:
        assert message.ref, "Cannot wait for reponse on a message without ref"

        websocket, failure = self._connection("RealtimeClient._send")
        _raise_connection_failure(failure)
        frame = encode(message)
        logger.debug("sending: %s", _loggable(frame))

        receive: asyncio.Future[Message] = asyncio.get_running_loop().create_future()
        self.message_refs[message.ref] = receive
        try:
            await websocket.send(frame)
            logger.debug("waiting for ref=%r", message.ref)
            response = await _wait_or_raise(receive, failure)
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
