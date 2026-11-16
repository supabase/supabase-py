import asyncio
from collections.abc import AsyncIterator

import pytest
from supabase_utils.types import JSON
from websockets.asyncio.server import Server, ServerConnection, serve
from websockets.exceptions import ConnectionClosed

from realtime import ChannelStates, RealtimeClient
from realtime._serializer import decode, encode
from realtime.message import (
    BroadcastMessage,
    ChannelCloseMessage,
    ChannelErrorMessage,
    Message,
)
from realtime.types import ChannelEvents

HOST = "127.0.0.1"


class FakeServer:
    def __init__(self) -> None:
        self.ws_server: Server | None = None
        self.url = ""
        self.connections: list[ServerConnection] = []
        self.received: list[Message] = []
        self.reply_heartbeats = True
        self.error_after_join = False

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
            if message.event == ChannelEvents.heartbeat and not self.reply_heartbeats:
                continue
            reply = Message(
                event=ChannelEvents.reply,
                topic=message.topic,
                ref=message.ref,
                payload={"status": "ok", "response": {"postgres_changes": []}},
            )
            frames = [encode(reply)]
            if message.event == ChannelEvents.join and self.error_after_join:
                error = Message(
                    event=ChannelEvents.error,
                    topic=message.topic,
                    ref=message.ref,
                    join_ref=message.ref,
                    payload={},
                )
                frames.append(encode(error))
            try:
                for frame in frames:
                    await connection.send(frame)
            except ConnectionClosed:
                return

    async def send(
        self,
        topic: str,
        event: ChannelEvents,
        join_ref: str | None,
        payload: dict[str, JSON] | None = None,
    ) -> None:
        message = Message(
            event=event,
            topic=topic,
            ref=join_ref,
            join_ref=join_ref,
            payload=payload or {},
        )
        await self.connections[-1].send(encode(message))

    async def drop_connections(self) -> None:
        for connection in self.connections:
            await connection.close()

    def joins(self) -> list[Message]:
        return [
            message for message in self.received if message.event == ChannelEvents.join
        ]

    def events(self) -> list[str]:
        return [
            message.event
            for message in self.received
            if message.event != ChannelEvents.heartbeat
        ]


@pytest.fixture
async def server() -> AsyncIterator[FakeServer]:
    async with FakeServer() as server:
        yield server


async def wait_for_failure(
    client: RealtimeClient, exception: type[Exception] = ConnectionClosed
) -> None:
    assert client._connection_failure is not None
    with pytest.raises(exception):
        await asyncio.wait_for(client._connection_failure, timeout=1)


async def test_phx_error_moves_the_channel_to_errored(server: FakeServer) -> None:
    client = RealtimeClient(server.url)
    channel = client.channel("room")
    await channel.subscribe()

    await server.send(channel.topic, ChannelEvents.error, channel.join_ref)
    message = await asyncio.wait_for(channel.messages.__anext__(), timeout=1)
    state = channel.state
    await client.aclose()

    assert isinstance(message, ChannelErrorMessage)
    assert state == ChannelStates.ERRORED


async def test_phx_close_moves_the_channel_to_closed(server: FakeServer) -> None:
    client = RealtimeClient(server.url)
    channel = client.channel("room")
    await channel.subscribe()

    await server.send(channel.topic, ChannelEvents.close, channel.join_ref)
    message = await asyncio.wait_for(channel.messages.__anext__(), timeout=1)
    state = channel.state
    await client.aclose()

    assert isinstance(message, ChannelCloseMessage)
    assert state == ChannelStates.CLOSED


@pytest.mark.parametrize("event", [ChannelEvents.error, ChannelEvents.close])
async def test_a_message_for_an_earlier_join_is_dropped(
    server: FakeServer, event: ChannelEvents
) -> None:
    client = RealtimeClient(server.url)
    channel = client.channel("room")
    await channel.subscribe()

    await server.send(channel.topic, event, "stale-join-ref")
    await server.send(
        channel.topic, ChannelEvents.broadcast, None, {"event": "a", "payload": {}}
    )
    message = await asyncio.wait_for(channel.messages.__anext__(), timeout=1)
    state = channel.state
    await client.aclose()

    assert isinstance(message, BroadcastMessage)
    assert state == ChannelStates.JOINED


async def test_phx_error_right_after_the_join_reply_leaves_the_channel_errored(
    server: FakeServer,
) -> None:
    server.error_after_join = True
    client = RealtimeClient(server.url)
    channel = client.channel("room")

    reply = await channel.subscribe()
    message = await asyncio.wait_for(channel.messages.__anext__(), timeout=1)
    state = channel.state
    await client.aclose()

    assert reply.payload.status == "ok"
    assert isinstance(message, ChannelErrorMessage)
    assert state == ChannelStates.ERRORED
    assert client.get_channels() == [channel]


async def test_unsubscribe_after_phx_error_sends_no_leave(server: FakeServer) -> None:
    client = RealtimeClient(server.url)
    channel = client.channel("room")
    await channel.subscribe()
    await server.send(channel.topic, ChannelEvents.error, channel.join_ref)
    await asyncio.wait_for(channel.messages.__anext__(), timeout=1)

    await channel.unsubscribe()

    assert channel.state == ChannelStates.CLOSED
    assert server.events() == [ChannelEvents.join]


async def test_an_errored_channel_can_subscribe_again(server: FakeServer) -> None:
    client = RealtimeClient(server.url)
    channel = client.channel("room")
    await channel.subscribe()
    await server.send(channel.topic, ChannelEvents.error, channel.join_ref)
    await asyncio.wait_for(channel.messages.__anext__(), timeout=1)

    await channel.subscribe()
    await client.aclose()

    assert len(server.joins()) == 2
    assert channel.state == ChannelStates.CLOSED


async def test_a_dropped_connection_moves_joined_channels_to_errored(
    server: FakeServer,
) -> None:
    client = RealtimeClient(server.url)
    first = client.channel("first")
    second = client.channel("second")
    await first.subscribe()
    await second.subscribe()

    await server.drop_connections()
    await wait_for_failure(client)
    states = (first.state, second.state)
    await client.aclose()

    assert states == (ChannelStates.ERRORED, ChannelStates.ERRORED)


async def test_unsubscribe_after_a_dropped_connection_does_not_raise(
    server: FakeServer,
) -> None:
    client = RealtimeClient(server.url)
    channel = client.channel("room")
    await channel.subscribe()
    await server.drop_connections()
    await wait_for_failure(client)

    await channel.unsubscribe()

    assert channel.state == ChannelStates.CLOSED
    assert client.get_channels() == []
    assert server.events() == [ChannelEvents.join]


async def test_a_heartbeat_timeout_moves_joined_channels_to_errored(
    server: FakeServer,
) -> None:
    server.reply_heartbeats = False
    client = RealtimeClient(server.url, heartbeat_interval=0.05, heartbeat_timeout=0.05)
    channel = client.channel("room")
    await channel.subscribe()

    await wait_for_failure(client, TimeoutError)
    errored = channel.state
    await server.send(channel.topic, ChannelEvents.close, channel.join_ref)
    await asyncio.sleep(0.05)
    after_close = channel.state
    await client.aclose()

    assert errored == ChannelStates.ERRORED
    assert after_close == ChannelStates.ERRORED
    assert channel.message_stream.empty()


async def test_aclose_moves_joined_channels_to_closed(server: FakeServer) -> None:
    client = RealtimeClient(server.url)
    channel = client.channel("room")
    await channel.subscribe()

    await client.aclose()

    assert channel.state == ChannelStates.CLOSED


async def test_set_auth_skips_the_channels_of_a_dropped_connection(
    server: FakeServer,
) -> None:
    client = RealtimeClient(server.url)
    channel = client.channel("room")
    await channel.subscribe()
    await server.drop_connections()
    await wait_for_failure(client)

    await client.set_auth("new-token")
    await channel.subscribe()
    await client.aclose()

    assert client.last_token == "new-token"
    assert server.events() == [ChannelEvents.join, ChannelEvents.join]
    assert server.joins()[1].payload["access_token"] == "new-token"


@pytest.mark.parametrize(
    ("event", "state", "expected"),
    [
        (ChannelEvents.error, ChannelStates.JOINED, ChannelStates.ERRORED),
        (ChannelEvents.error, ChannelStates.JOINING, ChannelStates.ERRORED),
        (ChannelEvents.error, ChannelStates.LEAVING, ChannelStates.LEAVING),
        (ChannelEvents.error, ChannelStates.CLOSED, ChannelStates.CLOSED),
        (ChannelEvents.close, ChannelStates.JOINED, ChannelStates.CLOSED),
        (ChannelEvents.close, ChannelStates.ERRORED, ChannelStates.CLOSED),
        (ChannelEvents.close, ChannelStates.LEAVING, ChannelStates.LEAVING),
    ],
)
def test_state_transitions(
    event: ChannelEvents, state: ChannelStates, expected: ChannelStates
) -> None:
    channel = RealtimeClient("ws://localhost").channel("room")
    channel.state = state

    channel._receive(Message(event=event, topic=channel.topic, payload={}))

    assert channel.state == expected
    assert channel.message_stream.get_nowait().event == event
