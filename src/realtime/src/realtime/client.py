import asyncio
import json
import logging
import re
import sys
from functools import wraps
from types import TracebackType
from typing import (
    Any,
    AsyncIterator,
    Awaitable,
    Callable,
    Dict,
    Generator,
    List,
    Optional,
    Union,
)
from urllib.parse import urlencode, urlparse, urlunparse
from warnings import warn

import websockets
from pydantic import ValidationError
from websockets.asyncio.client import ClientConnection
from yarl import URL
from yarl._query import get_str_query

from .channel import RealtimeChannel, RealtimeChannelOptions
from .exceptions import NotConnectedError
from .message import Message, ReplyMessage, ServerMessage
from .types import (
    DEFAULT_HEARTBEAT_INTERVAL,
    DEFAULT_TIMEOUT,
    PHOENIX_CHANNEL,
    VSN,
    ChannelEvents,
    ChannelStates,
)

logger = logging.getLogger(__name__)


def normalize_url(url: URL, token: str | None) -> URL:
    if url.scheme not in {"ws", "wss", "http", "https"}:
        raise ValueError("url must be a valid WebSocket URL or HTTP URL string")
    url = url.joinpath("websocket")
    if token:
        url = url.with_query(**url.query, apikey=token)
    if url.scheme in {"ws", "wss"}:
        return url
    if url.scheme == "https":
        return url.with_scheme("wss")
    return url.with_scheme("ws")


class connect_once:
    def __init__(
        self,
        url: str,
        token_callback: Callable[[], Awaitable[str | None]] | None = None,
        hb_interval: int = DEFAULT_HEARTBEAT_INTERVAL,
        hb_timeout: int = 5,
    ) -> None:
        self.url = URL(url)
        self.get_access_token = token_callback
        self.listen_task: asyncio.Task | None = None
        self.heartbeat_task: asyncio.Task | None = None
        self.hb_interval = hb_interval
        self.hb_timeout = hb_timeout

    def __await__(self) -> Generator[None, None, "RealtimeClient"]:
        return self.__await_impl__().__await__()

    async def __await_impl__(self) -> "RealtimeClient":
        if self.get_access_token:
            token = await self.get_access_token()
            url = normalize_url(self.url, token)
        else:
            url = normalize_url(self.url, None)
        self.ws = await websockets.connect(str(url))
        self.client = RealtimeClient(
            self.url,
            self.ws,
            self.get_access_token,
            hb_interval=self.hb_interval,
            hb_timeout=self.hb_timeout,
        )
        self.listen_task = asyncio.create_task(self.client.listen())
        self.heartbeat_task = asyncio.create_task(self.client.heartbeat())
        return self.client

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
        await self.client.close()


class MaxRetriesExceeded(Exception):
    pass


def exponential_delay(max_retries: int, retry_count: int) -> float | None:
    if retry_count == max_retries:
        return None
    else:
        return float(2**retry_count)


async def automatically_reconnect(
    url: str,
    token_callback: Callable[[], Awaitable[str]],
    client_handler: Callable[["RealtimeClient"], Awaitable[None]],
    max_retries: int = 3,
) -> None:
    retries = 0
    while True:
        try:
            async with connect_once(url, token_callback) as client:
                retries = 0
                await client_handler(client)
                break
        except websockets.ConnectionClosed:
            continue
        except (TimeoutError, OSError):
            retries += 1
            delay = exponential_delay(max_retries, retries)
            if delay is not None:
                await asyncio.sleep(delay)
            else:
                raise MaxRetriesExceeded(retries)


class RealtimeClient:
    def __init__(
        self,
        url: URL,
        ws_connection: ClientConnection,
        token_callback: Callable[[], Awaitable[str | None]] | None = None,
        hb_interval: int = DEFAULT_HEARTBEAT_INTERVAL,
        hb_timeout: int = 5,
    ) -> None:
        self.url = url
        self.last_token: str | None = None
        self.get_access_token = token_callback
        self.http_endpoint = url.with_scheme("https").with_path("")

        self._ws_connection: ClientConnection = ws_connection

        self.ref = 0
        self.channels: Dict[str, RealtimeChannel] = {}
        self.message_refs: Dict[str, asyncio.Future[Message]] = {}
        self._connection_failure: asyncio.Future[Message] = asyncio.Future()

        self.hb_interval = hb_interval
        self.heartbeat_timeout = hb_timeout

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
                    logger.error(f"Unrecognized message format {msg!r}\n{e}")
                    continue
                if message.ref is not None:
                    self.message_refs[message.ref].set_result(message)
                elif channel := self.channels.get(message.topic):
                    await channel.message_stream.put(message)
                else:
                    logger.info(f"Ignoring message: {message!r}")
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

    async def get_message_or_raise(self, fut: asyncio.Future[Message]) -> Message:
        done, pending = await asyncio.wait(
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
                    self.send(data), timeout=self.heartbeat_timeout
                )
                logger.info(f"heartbeat response: {res!r}")
                await self.set_auth()
                await asyncio.sleep(max(self.hb_interval, 15))
        except asyncio.CancelledError:
            return
        except (websockets.ConnectionClosed, asyncio.TimeoutError) as exc:
            if (
                not self._connection_failure.done()
                or self._connection_failure.cancelled()
            ):
                self._connection_failure.set_exception(exc)

    def channel(
        self, topic: str, params: RealtimeChannelOptions | None = None
    ) -> RealtimeChannel:
        """
        Initialize a channel and create a two-way association with the socket.

        :param topic: The topic to subscribe to
        :param params: Optional channel parameters
        :return: AsyncRealtimeChannel instance
        """
        topic = f"realtime:{topic}"
        chan = RealtimeChannel(self, topic, params)
        self.channels[topic] = chan
        return chan

    def get_channels(self) -> List[RealtimeChannel]:
        return list(self.channels.values())

    def _remove_channel(self, channel: RealtimeChannel) -> None:
        del self.channels[channel.topic]

    async def remove_channel(self, channel: RealtimeChannel) -> None:
        if chan := self.channels.get(channel.topic):
            await chan.unsubscribe()
            self._remove_channel(channel)

    async def remove_all_channels(self) -> None:
        """
        Unsubscribes and removes all channels from the socket
        :return: None
        """
        tasks = []
        for channel in self.channels.values():
            tasks.append(asyncio.create_task(channel.unsubscribe()))
        await asyncio.wait(tasks)

    async def set_auth(self, token: str | None = None) -> None:
        """
        Set the authentication token for the connection and update all joined channels.

        This method updates the access token for the current connection and sends the new token
        to all joined channels. This is useful for refreshing authentication or changing users.

        Args:
            token (Optional[str]): The new authentication token. Can be None to remove authentication.

        Returns:
            None
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

        tasks = []
        for channel in self.channels.values():
            if channel.joined and channel.state == ChannelStates.JOINED:
                task = asyncio.create_task(
                    channel.send_event(
                        ChannelEvents.access_token, {"access_token": token}
                    )
                )
                tasks.append(task)
        if tasks:
            await asyncio.wait(tasks)
        self.last_token = token

    def _make_ref(self) -> str:
        self.ref += 1
        return f"{self.ref}"

    async def send(self, message: Message) -> ReplyMessage:
        assert message.ref, "Cannot wait for reponse on a message without ref"

        message_str = message.model_dump_json()
        logger.debug(f"sending: {message_str}")

        receive: asyncio.Future[Message] = asyncio.Future()
        self.message_refs[message.ref] = receive
        await self._ws_connection.send(message_str)
        logger.debug(f"waiting for ref='{message.ref}'")

        response = await self.get_message_or_raise(receive)
        del self.message_refs[message.ref]

        return ReplyMessage.model_validate(response)

    async def send_no_wait(self, message: Message) -> None:
        message_str = message.model_dump_json()
        logger.debug(f"sending: {message_str}")
        await self._ws_connection.send(message_str)

    def endpoint_url(self) -> str:
        query = self.url.with_query(**self.url.query, vsn=VSN)
        return str(query)
