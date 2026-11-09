import asyncio
import logging
from collections.abc import Awaitable, Callable, Generator
from types import TracebackType
from warnings import warn

import websockets
from pydantic import ValidationError
from supabase_utils.http.errors import SupabaseTransportError
from websockets.asyncio.client import ClientConnection
from yarl import URL

from ._redact import RedactingLoggerAdapter
from .channel import RealtimeChannel, RealtimeChannelOptions
from .exceptions import MaxRetriesExceeded
from .message import Message, ReplyMessage
from .types import (
    DEFAULT_HEARTBEAT_INTERVAL,
    DEFAULT_HEARTBEAT_TIMEOUT,
    PHOENIX_CHANNEL,
    PROTOCOL_VERSION,
    ChannelEvents,
    validate_heartbeat,
)

logger = RedactingLoggerAdapter(logging.getLogger(__name__))
websockets_logger = RedactingLoggerAdapter(logging.getLogger("websockets.client"))


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
        validate_heartbeat(heartbeat_interval, heartbeat_timeout)
        self.url = URL(url)
        self.get_access_token = token_callback
        self.listen_task: asyncio.Task[None] | None = None
        self.heartbeat_task: asyncio.Task[None] | None = None
        self.websocket: ClientConnection | None = None
        self.client: RealtimeClient | None = None
        self.heartbeat_interval = heartbeat_interval
        self.heartbeat_timeout = heartbeat_timeout

    def __await__(self) -> Generator[None, None, "RealtimeClient"]:
        return self.__await_impl__().__await__()

    async def __await_impl__(self) -> "RealtimeClient":
        if self.get_access_token:
            token = await self.get_access_token()
            url = normalize_url(self.url, token)
        else:
            url = normalize_url(self.url, None)
        websocket = await websockets.connect(str(url), logger=websockets_logger)
        self.websocket = websocket
        client = RealtimeClient(
            self.url,
            websocket,
            self.get_access_token,
            heartbeat_interval=self.heartbeat_interval,
            heartbeat_timeout=self.heartbeat_timeout,
        )
        self.client = client
        self.listen_task = asyncio.create_task(client.listen())
        self.heartbeat_task = asyncio.create_task(client.heartbeat())
        return client

    async def __aenter__(self) -> "RealtimeClient":
        return await self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        assert self.listen_task, "Connection should never exit without listen_task"
        self.listen_task.cancel()
        assert self.heartbeat_task, "Connection should never exit without hearbeat_task"
        self.heartbeat_task.cancel()
        assert self.client, "Connection should never exit without client"
        await self.client.close()


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
    def __init__(
        self,
        url: URL,
        websocket_connection: ClientConnection,
        token_callback: Callable[[], Awaitable[str | None]] | None = None,
        heartbeat_interval: float = DEFAULT_HEARTBEAT_INTERVAL,
        heartbeat_timeout: float = DEFAULT_HEARTBEAT_TIMEOUT,
    ) -> None:
        validate_heartbeat(heartbeat_interval, heartbeat_timeout)
        self.url = url
        self.last_token: str | None = None
        self.get_access_token = token_callback
        self.http_endpoint = url.with_scheme("https").with_path("")

        self._ws_connection: ClientConnection = websocket_connection

        self.ref = 0
        self.channels: dict[str, RealtimeChannel] = {}
        self.message_refs: dict[str, asyncio.Future[Message]] = {}
        self._connection_failure: asyncio.Future[Message] = asyncio.Future()

        self.heartbeat_interval = heartbeat_interval
        self.heartbeat_timeout = heartbeat_timeout

    async def listen(self) -> None:
        """
        An infinite loop that keeps listening.
        :return: None
        """
        try:
            while True:
                msg = await self._ws_connection.recv(decode=False)
                try:
                    message = Message.model_validate_json(msg)
                except ValidationError as e:
                    logger.error("Unrecognized message format %r\n%s", msg, e)
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
            if (
                not self._connection_failure.done()
                or self._connection_failure.cancelled()
            ):
                self._connection_failure.set_exception(exc)

    async def close(self) -> None:
        """
        Close the WebSocket connection.

        Returns:
            None

        Raises:
            NotConnectedError: If the connection is not established when this method is called.
        """

        await self._ws_connection.close()

    async def _get_message_or_raise(self, fut: asyncio.Future[Message]) -> Message:
        done, _pending = await asyncio.wait(
            (fut, self._connection_failure), return_when=asyncio.FIRST_COMPLETED
        )
        if self._connection_failure in done:
            fut.cancel()
            # raise the exception
            await self._connection_failure
        return fut.result()

    async def heartbeat(self) -> None:
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
            if (
                not self._connection_failure.done()
                or self._connection_failure.cancelled()
            ):
                self._connection_failure.set_exception(exc)

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
        Set the authentication token for the connection and update all joined channels.

        This method updates the access token for the current connection and sends the new token
        to all joined channels. This is useful for refreshing authentication or changing users.

        Args:
            token (Optional[str]): The new authentication token. Can be None to remove authentication.

        Returns:
            None

        Raises:
            websockets.ConnectionClosed: If the connection is closed. The token is
                not stored, so calling this method again with the same token sends
                it again.
            Exception: If the connection already failed, the exception that failed
                it, such as a TimeoutError when a heartbeat timed out.
        """
        if token is None:
            if self.get_access_token is not None and (
                new_token := await self.get_access_token()
            ):
                token = new_token
            else:
                logger.warning(
                    "tried setting auth but no token callback was registered"
                )
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

    def _make_ref(self) -> str:
        self.ref += 1
        return f"{self.ref}"

    async def _send(self, message: Message) -> ReplyMessage:
        assert message.ref, "Cannot wait for reponse on a message without ref"

        self._raise_connection_failure()
        message_str = message.model_dump_json()
        logger.debug("sending: %s", message_str)

        receive: asyncio.Future[Message] = asyncio.Future()
        self.message_refs[message.ref] = receive
        try:
            await self._ws_connection.send(message_str)
            logger.debug("waiting for ref=%r", message.ref)
            response = await self._get_message_or_raise(receive)
        finally:
            del self.message_refs[message.ref]

        return ReplyMessage.model_validate(response)

    async def _send_no_wait(self, message: Message) -> None:
        self._raise_connection_failure()
        message_str = message.model_dump_json()
        logger.debug("sending: %s", message_str)
        await self._ws_connection.send(message_str)

    def _raise_connection_failure(self) -> None:
        failure = self._connection_failure
        if failure.done() and not failure.cancelled():
            failure.result()

    def endpoint_url(self) -> str:
        return str(normalize_url(self.url, self.last_token))
