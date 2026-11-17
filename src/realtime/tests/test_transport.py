import asyncio

import pytest

from realtime import (
    ChannelNotJoinedError,
    ConnectionState,
    NotConnectedError,
    RealtimeChannel,
    RealtimeClient,
    WebSocketConnection,
    connect_once,
)
from realtime._serializer import decode, encode
from realtime.message import BroadcastMessage, Message
from realtime.types import ChannelEvents

URL = "wss://example.supabase.co/realtime/v1"


class InMemoryConnection:
    def __init__(self) -> None:
        self.sent: list[Message] = []
        self.closed = False
        self._frames: asyncio.Queue[str | bytes | None] = asyncio.Queue()

    async def send(self, message: str | bytes, /) -> None:
        if self.closed:
            raise ConnectionError("the connection is closed")
        sent = decode(message)
        self.sent.append(sent)
        if sent.ref is not None and sent.event != ChannelEvents.access_token:
            reply = Message(
                event=ChannelEvents.reply,
                topic=sent.topic,
                ref=sent.ref,
                payload={"status": "ok", "response": {"postgres_changes": []}},
            )
            self._frames.put_nowait(encode(reply))

    async def recv(self) -> str | bytes:
        frame = await self._frames.get()
        if frame is None:
            raise ConnectionError("the connection is closed")
        return frame

    async def close(self) -> None:
        self.closed = True
        self._frames.put_nowait(None)

    def push(self, message: Message) -> None:
        self._frames.put_nowait(encode(message))


class InMemoryTransport:
    def __init__(self) -> None:
        self.urls: list[str] = []
        self.connections: list[InMemoryConnection] = []

    async def __call__(self, url: str) -> WebSocketConnection:
        self.urls.append(url)
        connection = InMemoryConnection()
        self.connections.append(connection)
        return connection


async def test_the_client_connects_with_the_transport() -> None:
    transport = InMemoryTransport()

    async with connect_once(URL, transport=transport) as client:
        channel = client.channel("room")
        await channel.subscribe()
        transport.connections[0].push(
            Message(
                event=ChannelEvents.broadcast,
                topic=channel.topic,
                payload={"type": "broadcast", "event": "ping", "payload": {}},
            )
        )
        message = await anext(channel.messages)

    assert isinstance(message, BroadcastMessage)
    assert transport.urls == [f"{URL}/websocket?vsn=2.0.0"]
    assert transport.connections[0].sent[0].event == ChannelEvents.join
    assert transport.connections[0].closed


async def test_an_error_from_the_transport_fails_the_connect() -> None:
    async def refuse(url: str) -> WebSocketConnection:
        raise ConnectionRefusedError(url)

    client = RealtimeClient(URL, transport=refuse)

    with pytest.raises(ConnectionRefusedError):
        await client.connect()
    assert client.connection_state == ConnectionState.CLOSED


async def test_a_connection_error_from_the_transport_drops_the_connection() -> None:
    transport = InMemoryTransport()
    client = RealtimeClient(URL, transport=transport)
    channel = client.channel("room")
    await channel.subscribe()

    await transport.connections[0].close()
    await asyncio.sleep(0)

    assert client.connection_state == ConnectionState.CLOSED
    with pytest.raises(ChannelNotJoinedError):
        await channel.send_broadcast("ping", {})
    await client.aclose()


async def wait_until_closed(client: RealtimeClient) -> None:
    async def closed() -> None:
        async for state in client.connection_states():
            if state == ConnectionState.CLOSED:
                return

    await asyncio.wait_for(closed(), timeout=5)


async def test_the_connection_closes_once_the_delay_after_the_last_channel_passes() -> (
    None
):
    transport = InMemoryTransport()
    client = RealtimeClient(
        URL, transport=transport, disconnect_on_empty_channels_after=0.05
    )
    channel = client.channel("room")
    await channel.subscribe()

    await channel.unsubscribe()
    assert client.connection_state == ConnectionState.CONNECTED

    await wait_until_closed(client)
    assert transport.connections[0].closed


async def test_a_channel_joined_within_the_delay_reuses_the_connection() -> None:
    transport = InMemoryTransport()
    client = RealtimeClient(
        URL, transport=transport, disconnect_on_empty_channels_after=60
    )
    await client.channel("first").subscribe()
    await client.remove_all_channels()
    pending = client._disconnect_task
    assert pending is not None

    await client.channel("second").subscribe()
    await asyncio.sleep(0)

    assert pending.cancelled()
    assert client.connection_state == ConnectionState.CONNECTED
    assert len(transport.connections) == 1
    await client.aclose()


async def test_removing_the_last_channel_again_restarts_the_delay() -> None:
    transport = InMemoryTransport()
    client = RealtimeClient(
        URL, transport=transport, disconnect_on_empty_channels_after=60
    )
    await client.channel("first").subscribe()
    await client.remove_all_channels()
    first = client._disconnect_task
    await client.channel("second").subscribe()
    await client.remove_all_channels()
    await asyncio.sleep(0)

    assert first is not None
    assert first.cancelled()
    assert client._disconnect_task is not None
    assert not client._disconnect_task.done()
    await client.aclose()


async def test_unsubscribing_without_a_connection_schedules_no_disconnect() -> None:
    client = RealtimeClient(
        URL, transport=InMemoryTransport(), disconnect_on_empty_channels_after=60
    )
    channel = client.channel("room")

    await channel.unsubscribe()

    assert client._disconnect_task is None


async def read_all(channel: RealtimeChannel) -> None:
    async for _ in channel.messages:
        pass


async def test_reading_past_the_close_of_an_unsubscribed_channel_raises() -> None:
    client = RealtimeClient(
        URL, transport=InMemoryTransport(), disconnect_on_empty_channels_after=60
    )
    channel = client.channel("room")
    await channel.subscribe()
    await channel.unsubscribe()

    with pytest.raises(NotConnectedError, match="unsubscribed"):
        await asyncio.wait_for(read_all(channel), timeout=5)
    await client.aclose()


async def test_aclose_cancels_a_pending_disconnect() -> None:
    transport = InMemoryTransport()
    client = RealtimeClient(
        URL, transport=transport, disconnect_on_empty_channels_after=60
    )
    await client.channel("room").subscribe()
    await client.remove_all_channels()
    pending = client._disconnect_task
    assert pending is not None

    await client.aclose()
    await asyncio.sleep(0)

    assert pending.cancelled()
    assert client.connection_state == ConnectionState.CLOSED


def test_the_disconnect_delay_defaults_to_twice_the_heartbeat_interval() -> None:
    client = RealtimeClient(URL, heartbeat_interval=10)

    assert client.disconnect_on_empty_channels_after == 20


def test_a_negative_disconnect_delay_is_rejected() -> None:
    with pytest.raises(ValueError, match="disconnect_on_empty_channels_after"):
        RealtimeClient(URL, disconnect_on_empty_channels_after=-1)
