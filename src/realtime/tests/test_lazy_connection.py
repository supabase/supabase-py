import asyncio
from collections.abc import AsyncIterator

import pytest
from websockets.asyncio.server import Server, ServerConnection, serve
from websockets.exceptions import ConnectionClosed

from realtime import ChannelStates, NotConnectedError, RealtimeClient, RealtimeError
from realtime._serializer import decode, encode
from realtime.message import ChannelCloseMessage, Message
from realtime.types import ChannelEvents

HOST = "127.0.0.1"


class FakeServer:
    def __init__(self) -> None:
        self.ws_server: Server | None = None
        self.url = ""
        self.connections: list[ServerConnection] = []
        self.received: list[Message] = []
        self.join_reply_delay = 0.0

    async def __aenter__(self) -> "FakeServer":
        self.ws_server = await serve(self.handler, HOST, 0)
        port = next(iter(self.ws_server.sockets)).getsockname()[1]
        self.url = f"http://{HOST}:{port}"
        await self.ws_server.start_serving()
        return self

    async def __aexit__(self, *exc: object) -> None:
        assert self.ws_server is not None
        self.ws_server.close()
        await self.ws_server.wait_closed()

    async def handler(self, connection: ServerConnection) -> None:
        self.connections.append(connection)
        async for raw in connection:
            message = decode(raw)
            self.received.append(message)
            if message.ref is None:
                continue
            if message.event == ChannelEvents.join:
                await asyncio.sleep(self.join_reply_delay)
            reply = Message(
                event=ChannelEvents.reply,
                topic=message.topic,
                ref=message.ref,
                payload={"status": "ok", "response": {"postgres_changes": []}},
            )
            try:
                await connection.send(encode(reply))
            except ConnectionClosed:
                return

    async def drop_connections(self) -> None:
        for connection in self.connections:
            await connection.close()


@pytest.fixture
async def server() -> AsyncIterator[FakeServer]:
    async with FakeServer() as server:
        yield server


async def test_client_does_not_connect_before_a_channel_subscribes(
    server: FakeServer,
) -> None:
    client = RealtimeClient(server.url)
    channel = client.channel("room")
    await asyncio.sleep(0.05)

    assert server.connections == []
    assert client.get_channels() == [channel]

    await channel.subscribe()
    await client.aclose()

    assert len(server.connections) == 1


async def test_channels_of_one_client_share_one_connection(
    server: FakeServer,
) -> None:
    client = RealtimeClient(server.url)

    await asyncio.gather(
        client.channel("first").subscribe(),
        client.channel("second").subscribe(),
    )
    await client.channel("third").subscribe()
    await client.aclose()

    assert len(server.connections) == 1


async def test_close_leaves_channels_unsubscribed(server: FakeServer) -> None:
    client = RealtimeClient(server.url)
    channel = client.channel("room")
    await channel.subscribe()

    await client.aclose()

    assert channel.state == ChannelStates.CLOSED
    await client.remove_all_channels()
    assert client.get_channels() == []


async def test_subscribe_after_close_opens_a_new_connection(
    server: FakeServer,
) -> None:
    client = RealtimeClient(server.url)
    channel = client.channel("room")
    await channel.subscribe()
    await client.aclose()

    await channel.subscribe()

    assert channel.joined
    assert len(server.connections) == 2
    await client.aclose()


async def test_subscribe_after_a_lost_connection_opens_a_new_connection(
    server: FakeServer,
) -> None:
    client = RealtimeClient(server.url)
    channel = client.channel("room")
    await channel.subscribe()
    failure = client._connection_failure
    assert failure is not None

    await server.drop_connections()
    with pytest.raises(ConnectionClosed):
        await asyncio.wait_for(failure, timeout=1)
    await channel.subscribe()

    assert channel.joined
    assert len(server.connections) == 2
    await client.aclose()


async def test_close_without_a_connection_does_nothing() -> None:
    client = RealtimeClient("http://localhost")

    await client.aclose()


async def test_sending_without_a_connection_raises_not_connected() -> None:
    client = RealtimeClient("http://localhost")

    with pytest.raises(NotConnectedError):
        await client.channel("room").track({"user": "a"})


async def test_close_wakes_a_reader_waiting_for_messages(server: FakeServer) -> None:
    client = RealtimeClient(server.url)
    channel = client.channel("room")
    await channel.subscribe()

    async def read() -> None:
        async for _ in channel.messages:
            pass

    reader = asyncio.create_task(read())
    await asyncio.sleep(0.05)
    await client.aclose()

    with pytest.raises(ConnectionClosed):
        await asyncio.wait_for(reader, timeout=1)


async def test_unsubscribe_during_a_pending_join_sends_leave(
    server: FakeServer,
) -> None:
    server.join_reply_delay = 0.2
    client = RealtimeClient(server.url)
    channel = client.channel("room")
    join = asyncio.create_task(channel.subscribe())
    await asyncio.sleep(0.05)

    await channel.unsubscribe()
    with pytest.raises(RealtimeError, match="was stopped"):
        await join
    await client.aclose()

    assert channel.state == ChannelStates.CLOSED

    [join_message] = [m for m in server.received if m.event == ChannelEvents.join]
    [leave_message] = [m for m in server.received if m.event == ChannelEvents.leave]
    assert leave_message.join_ref == join_message.ref


async def test_subscribe_on_a_taken_topic_does_not_connect(
    server: FakeServer,
) -> None:
    client = RealtimeClient(server.url)
    stale = client.channel("room")
    client.channels.clear()
    client.channel("room")

    with pytest.raises(ValueError, match="already registered"):
        await stale.subscribe()

    assert server.connections == []


async def test_reading_messages_without_a_connection_does_not_consume_later_ones() -> (
    None
):
    client = RealtimeClient("http://localhost")
    channel = client.channel("room")

    with pytest.raises(NotConnectedError):
        await anext(aiter(channel.messages))
    message = Message(topic=channel.topic, event=ChannelEvents.broadcast, payload={})
    channel.message_stream.put_nowait(message)
    await asyncio.sleep(0)

    assert channel.message_stream.qsize() == 1


async def test_join_after_a_reconnect_uses_the_current_token(
    server: FakeServer,
) -> None:
    token = "first-token"

    async def get_token() -> str:
        return token

    client = RealtimeClient(server.url, get_token)
    channel = client.channel("room")
    await channel.subscribe()
    await client.set_auth()
    failure = client._connection_failure
    assert failure is not None

    token = "second-token"
    await server.drop_connections()
    with pytest.raises(ConnectionClosed):
        await asyncio.wait_for(failure, timeout=1)
    await channel.subscribe()
    await client.aclose()

    joins = [m for m in server.received if m.event == ChannelEvents.join]
    assert joins[-1].payload["access_token"] == "second-token"


async def test_unsubscribe_while_connecting_stops_the_join(server: FakeServer) -> None:
    client = RealtimeClient(server.url)
    channel = client.channel("room")
    join = asyncio.create_task(channel.subscribe())
    await asyncio.sleep(0)

    await channel.unsubscribe()
    with pytest.raises(RealtimeError, match="was stopped"):
        await join
    await client.aclose()

    assert channel.state == ChannelStates.CLOSED
    assert client.get_channels() == []
    assert all(m.event != ChannelEvents.join for m in server.received)


async def test_unsubscribing_the_last_channel_closes_the_connection(
    server: FakeServer,
) -> None:
    client = RealtimeClient(server.url)
    channel = client.channel("room")
    await channel.subscribe()

    await channel.unsubscribe()
    await asyncio.wait_for(server.connections[0].wait_closed(), timeout=1)
    await channel.subscribe()

    assert channel.joined
    assert len(server.connections) == 2
    await client.aclose()


async def test_removing_all_channels_closes_the_connection(server: FakeServer) -> None:
    client = RealtimeClient(server.url)
    await client.channel("first").subscribe()
    await client.channel("second").subscribe()

    await client.remove_all_channels()

    await asyncio.wait_for(server.connections[0].wait_closed(), timeout=1)
    with pytest.raises(NotConnectedError):
        await client.channel("room").track({"user": "a"})


async def test_connection_stays_open_while_a_channel_is_registered(
    server: FakeServer,
) -> None:
    client = RealtimeClient(server.url)
    first = client.channel("first")
    client.channel("second")
    await first.subscribe()

    await first.unsubscribe()
    await client.channel("third").subscribe()

    assert len(server.connections) == 1
    await client.aclose()


async def test_reader_receives_close_when_the_last_channel_unsubscribes(
    server: FakeServer,
) -> None:
    client = RealtimeClient(server.url)
    channel = client.channel("room")
    await channel.subscribe()

    async def read_until_close() -> ChannelCloseMessage:
        async for message in channel.messages:
            if isinstance(message, ChannelCloseMessage):
                return message
        raise AssertionError

    reader = asyncio.create_task(read_until_close())
    await asyncio.sleep(0.05)
    await channel.unsubscribe()

    message = await asyncio.wait_for(reader, timeout=1)
    assert message.topic == channel.topic


async def test_cancelling_a_pending_join_sends_leave(server: FakeServer) -> None:
    server.join_reply_delay = 0.2
    client = RealtimeClient(server.url)
    channel = client.channel("room")
    join = asyncio.create_task(channel.subscribe())
    await asyncio.sleep(0.05)

    join.cancel()
    with pytest.raises(asyncio.CancelledError):
        await join
    await asyncio.sleep(0.3)
    await client.aclose()

    assert channel.state == ChannelStates.CLOSED
    [join_message] = [m for m in server.received if m.event == ChannelEvents.join]
    [leave_message] = [m for m in server.received if m.event == ChannelEvents.leave]
    assert leave_message.join_ref == join_message.ref


async def test_aclose_during_a_pending_join_stops_the_join(server: FakeServer) -> None:
    server.join_reply_delay = 0.2
    client = RealtimeClient(server.url)
    channel = client.channel("room")
    join = asyncio.create_task(channel.subscribe())
    await asyncio.sleep(0.05)

    await client.aclose()

    with pytest.raises(RealtimeError, match="was stopped"):
        await join
    assert channel.state == ChannelStates.CLOSED
