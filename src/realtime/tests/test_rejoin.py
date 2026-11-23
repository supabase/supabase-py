import asyncio
from collections.abc import AsyncIterator
from http import HTTPStatus

import pytest
from supabase_utils.types import JSON
from websockets.asyncio.server import Server, ServerConnection, serve
from websockets.datastructures import Headers
from websockets.exceptions import ConnectionClosed
from websockets.http11 import Request, Response

from realtime import (
    AuthorizationError,
    ChannelStateChange,
    ChannelStates,
    RealtimeChannelOptions,
    RealtimeClient,
    RealtimePostgresChangesListenEvent,
)
from realtime._serializer import decode, encode
from realtime.channel import ChannelMessage, RealtimeChannel
from realtime.message import Message
from realtime.types import ChannelEvents

HOST = "127.0.0.1"


class FakeServer:
    def __init__(self) -> None:
        self.ws_server: Server | None = None
        self.url = ""
        self.connections: list[ServerConnection] = []
        self.received: list[Message] = []
        self.join_errors: list[str] = []
        self.refuse_upgrades = 0
        self.hold_joins = False
        self.join_held = asyncio.Event()

    async def __aenter__(self) -> "FakeServer":
        self.ws_server = await serve(
            self.handler, HOST, 0, process_request=self.process_request
        )
        port = next(iter(self.ws_server.sockets)).getsockname()[1]
        self.url = f"http://{HOST}:{port}"
        await self.ws_server.start_serving()
        return self

    async def __aexit__(self, *exc: object) -> None:
        assert self.ws_server is not None
        self.ws_server.close()
        await self.ws_server.wait_closed()

    def process_request(
        self, connection: ServerConnection, request: Request
    ) -> Response | None:
        if self.refuse_upgrades:
            self.refuse_upgrades -= 1
            return Response(HTTPStatus.UNAUTHORIZED, "Unauthorized", Headers(), b"")
        return None

    async def handler(self, connection: ServerConnection) -> None:
        self.connections.append(connection)
        async for raw in connection:
            message = decode(raw)
            self.received.append(message)
            if message.ref is None:
                continue
            if message.event == ChannelEvents.join and self.hold_joins:
                self.join_held.set()
                continue
            payload: dict[str, JSON] = {
                "status": "ok",
                "response": {"postgres_changes": self.bindings(message)},
            }
            if message.event == ChannelEvents.join and self.join_errors:
                reason = self.join_errors.pop(0)
                payload = {"status": "error", "response": {"reason": reason}}
            reply = Message(
                event=ChannelEvents.reply,
                topic=message.topic,
                ref=message.ref,
                payload=payload,
            )
            try:
                await connection.send(encode(reply))
            except ConnectionClosed:
                return

    def bindings(self, message: Message) -> list[JSON]:
        if message.event != ChannelEvents.join:
            return []
        config = message.payload["config"]
        assert isinstance(config, dict)
        changes = config["postgres_changes"]
        assert isinstance(changes, list)
        return [
            {**change, "id": index}
            for index, change in enumerate(changes)
            if isinstance(change, dict)
        ]

    async def drop_connections(self) -> None:
        for connection in self.connections:
            await connection.close()

    def sent(self, event: ChannelEvents) -> list[Message]:
        return [message for message in self.received if message.event == event]


def after_a_tenth_of_a_second(attempt: int) -> float:
    return 0.1


def at_once(attempt: int) -> float:
    return 0.0


def after_ten_seconds(attempt: int) -> float:
    return 10.0


@pytest.fixture(autouse=True)
def reconnect_at_once(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("realtime.client.reconnect_delay", at_once)


@pytest.fixture
async def server() -> AsyncIterator[FakeServer]:
    async with FakeServer() as server:
        yield server


async def next_message(channel: RealtimeChannel) -> ChannelMessage:
    return await asyncio.wait_for(anext(aiter(channel.messages)), timeout=2)


async def test_a_dropped_connection_is_reopened_and_the_channel_joined_again(
    server: FakeServer,
) -> None:
    client = RealtimeClient(server.url)
    channel = client.channel("room")
    await channel.subscribe()

    await server.drop_connections()
    errored = await next_message(channel)
    joined = await next_message(channel)
    await client.aclose()

    assert isinstance(errored, ChannelStateChange)
    assert errored.state == ChannelStates.ERRORED
    assert isinstance(errored.error, ConnectionClosed)
    assert joined == ChannelStateChange(ChannelStates.JOINED)
    assert len(server.connections) == 2
    assert len(server.sent(ChannelEvents.join)) == 2


async def test_the_channel_keeps_receiving_messages_after_the_rejoin(
    server: FakeServer,
) -> None:
    client = RealtimeClient(server.url)
    channel = client.channel("room")
    await channel.subscribe()

    await server.drop_connections()
    await next_message(channel)
    await next_message(channel)
    broadcast = Message(
        event=ChannelEvents.broadcast,
        topic=channel.topic,
        payload={"type": "broadcast", "event": "ping", "payload": {}},
    )
    await server.connections[-1].send(encode(broadcast))
    message = await next_message(channel)
    await client.aclose()

    assert getattr(message, "event", None) == ChannelEvents.broadcast


async def test_the_rejoin_keeps_the_bindings_and_sends_the_current_token(
    server: FakeServer,
) -> None:
    token = "first-token"

    async def get_token() -> str:
        return token

    options = RealtimeChannelOptions().postgres_changes(
        RealtimePostgresChangesListenEvent.Insert, table="messages"
    )
    client = RealtimeClient(server.url, get_token)
    channel = client.channel("room", options)
    await channel.subscribe()

    token = "second-token"
    await server.drop_connections()
    await next_message(channel)
    await next_message(channel)
    await client.aclose()

    first, second = server.sent(ChannelEvents.join)
    assert first.payload["access_token"] == "first-token"
    assert second.payload["access_token"] == "second-token"
    assert first.payload["config"] == second.payload["config"]


async def test_the_presence_is_not_tracked_again_after_a_rejoin(
    server: FakeServer,
) -> None:
    client = RealtimeClient(server.url)
    channel = client.channel("room")
    await channel.subscribe()
    await channel.track({"user": "a"})

    await server.drop_connections()
    await next_message(channel)
    await next_message(channel)
    await asyncio.sleep(0.05)
    await client.aclose()

    assert len(server.sent(ChannelEvents.presence)) == 1


async def test_the_rejoin_sends_the_presence_flag_computed_at_subscribe(
    server: FakeServer,
) -> None:
    client = RealtimeClient(server.url)
    channel = client.channel("room")
    _listener = channel.presence_events()
    await channel.subscribe()

    await server.drop_connections()
    await next_message(channel)
    await next_message(channel)
    await client.aclose()

    first, second = server.sent(ChannelEvents.join)
    for join in (first, second):
        config = join.payload["config"]
        assert isinstance(config, dict)
        presence = config["presence"]
        assert isinstance(presence, dict)
        assert presence["enabled"] is True


async def test_the_token_is_fetched_once_for_all_rejoins(server: FakeServer) -> None:
    calls = 0

    async def get_token() -> str:
        nonlocal calls
        calls += 1
        return "token"

    client = RealtimeClient(server.url, get_token)
    channels = [client.channel(f"room-{index}") for index in range(3)]
    for channel in channels:
        await channel.subscribe()
    calls_before = calls

    await server.drop_connections()
    for channel in channels:
        await next_message(channel)
        await next_message(channel)
    await client.aclose()

    assert calls - calls_before < 2 + len(channels)


async def test_a_reader_of_a_closed_channel_sees_the_dropped_connection(
    server: FakeServer,
) -> None:
    client = RealtimeClient(server.url)
    channel = client.channel("room")
    await channel.subscribe()
    close = Message(
        event=ChannelEvents.close,
        topic=channel.topic,
        payload={},
        ref=channel.join_ref,
        join_ref=channel.join_ref,
    )
    await server.connections[-1].send(encode(close))
    await next_message(channel)

    await server.drop_connections()
    with pytest.raises(ConnectionClosed):
        await next_message(channel)
    await client.aclose()

    assert len(server.connections) == 1


async def test_a_transient_join_error_is_retried(server: FakeServer) -> None:
    client = RealtimeClient(server.url)
    channel = client.channel("room")
    await channel.subscribe()

    server.join_errors = [
        "ChannelRateLimitReached: Too many channels",
        "Unknown Error on Channel",
    ]
    await server.drop_connections()
    await next_message(channel)
    joined = await next_message(channel)
    await client.aclose()

    assert joined == ChannelStateChange(ChannelStates.JOINED)
    assert len(server.sent(ChannelEvents.join)) == 4


async def test_an_expired_token_is_retried_once(server: FakeServer) -> None:
    client = RealtimeClient(server.url)
    channel = client.channel("room")
    await channel.subscribe()

    server.join_errors = ["InvalidJWTToken: Token has expired 5 seconds ago"]
    await server.drop_connections()
    await next_message(channel)
    joined = await next_message(channel)
    await client.aclose()

    assert joined == ChannelStateChange(ChannelStates.JOINED)


async def test_a_fatal_join_error_ends_the_channel(server: FakeServer) -> None:
    client = RealtimeClient(server.url)
    channel = client.channel("room")
    await channel.subscribe()

    server.join_errors = ["Unauthorized: denied", "Unauthorized: denied"]
    await server.drop_connections()
    await next_message(channel)
    with pytest.raises(AuthorizationError) as error:
        await next_message(channel)
    await asyncio.sleep(0.05)
    joins = len(server.sent(ChannelEvents.join))
    await client.aclose()

    assert error.value.code == "Unauthorized"
    assert channel.state == ChannelStates.CLOSED
    assert joins == 3


async def test_a_refused_reconnect_ends_the_channels(server: FakeServer) -> None:
    client = RealtimeClient(server.url)
    channel = client.channel("room")
    await channel.subscribe()

    server.refuse_upgrades = 2
    await server.drop_connections()
    await next_message(channel)
    with pytest.raises(AuthorizationError, match="HTTP 401"):
        await next_message(channel)
    await client.aclose()

    assert len(server.connections) == 1
    assert channel.state == ChannelStates.CLOSED


async def test_a_refused_reconnect_is_retried_once(server: FakeServer) -> None:
    client = RealtimeClient(server.url)
    channel = client.channel("room")
    await channel.subscribe()

    server.refuse_upgrades = 1
    await server.drop_connections()
    await next_message(channel)
    joined = await next_message(channel)
    await client.aclose()

    assert joined == ChannelStateChange(ChannelStates.JOINED)
    assert len(server.connections) == 2


async def test_unsubscribe_stops_the_rejoin(
    server: FakeServer, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("realtime.client.reconnect_delay", after_a_tenth_of_a_second)
    client = RealtimeClient(server.url)
    channel = client.channel("room")
    other = client.channel("other")
    await channel.subscribe()
    await other.subscribe()

    await server.drop_connections()
    await next_message(channel)
    await channel.unsubscribe()
    await next_message(other)
    rejoined_state = await next_message(other)
    await asyncio.sleep(0.05)
    await client.aclose()

    rejoined = [m.topic for m in server.sent(ChannelEvents.join)[2:]]
    assert rejoined_state == ChannelStateChange(ChannelStates.JOINED)
    assert rejoined == [other.topic]
    assert channel.state == ChannelStates.CLOSED


async def test_aclose_stops_reconnecting(
    server: FakeServer, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("realtime.client.reconnect_delay", after_a_tenth_of_a_second)
    client = RealtimeClient(server.url)
    channel = client.channel("room")
    await channel.subscribe()

    await server.drop_connections()
    await next_message(channel)
    await client.aclose()
    await asyncio.sleep(0.2)

    assert len(server.connections) == 1
    assert channel.state == ChannelStates.ERRORED


async def test_channels_that_were_not_joined_are_not_joined_again(
    server: FakeServer,
) -> None:
    client = RealtimeClient(server.url)
    joined = client.channel("joined")
    client.channel("created")
    await joined.subscribe()

    await server.drop_connections()
    await next_message(joined)
    await next_message(joined)
    await client.aclose()

    assert [m.topic for m in server.sent(ChannelEvents.join)] == [
        joined.topic,
        joined.topic,
    ]


async def test_connect_after_aclose_joins_the_channels_again(
    server: FakeServer,
) -> None:
    client = RealtimeClient(server.url)
    channel = client.channel("room")
    await channel.subscribe()

    await client.aclose()
    await client.connect()
    errored = await next_message(channel)
    joined = await next_message(channel)
    await client.aclose()

    assert errored == ChannelStateChange(ChannelStates.ERRORED)
    assert joined == ChannelStateChange(ChannelStates.JOINED)
    assert len(server.connections) == 2
    assert len(server.sent(ChannelEvents.join)) == 2


async def test_subscribing_another_channel_after_aclose_joins_the_others_again(
    server: FakeServer,
) -> None:
    client = RealtimeClient(server.url)
    channel = client.channel("room")
    await channel.subscribe()

    await client.aclose()
    other = client.channel("other")
    await other.subscribe()
    await next_message(channel)
    joined = await next_message(channel)
    await client.aclose()

    assert joined == ChannelStateChange(ChannelStates.JOINED)
    assert sorted(m.topic for m in server.sent(ChannelEvents.join)) == sorted(
        [channel.topic, channel.topic, other.topic]
    )


async def test_subscribe_after_aclose_joins_the_channel_once(
    server: FakeServer,
) -> None:
    client = RealtimeClient(server.url)
    channel = client.channel("room")
    await channel.subscribe()

    await client.aclose()
    await channel.subscribe()
    rejoin = client._reconnect_task
    await client.aclose()

    assert rejoin is None
    assert len(server.sent(ChannelEvents.join)) == 2


async def test_an_unsubscribed_channel_is_not_joined_again_after_aclose(
    server: FakeServer,
) -> None:
    client = RealtimeClient(server.url)
    left = client.channel("left")
    kept = client.channel("kept")
    await left.subscribe()
    await kept.subscribe()

    await left.unsubscribe()
    await client.aclose()
    await client.connect()
    await next_message(kept)
    await next_message(kept)
    await client.aclose()

    assert [m.topic for m in server.sent(ChannelEvents.join)] == [
        left.topic,
        kept.topic,
        kept.topic,
    ]
    assert left.state == ChannelStates.CLOSED


async def test_unsubscribe_after_aclose_stops_the_rejoin(
    server: FakeServer,
) -> None:
    client = RealtimeClient(server.url)
    channel = client.channel("room")
    other = client.channel("other")
    await channel.subscribe()
    await other.subscribe()

    await client.aclose()
    await channel.unsubscribe()
    await client.connect()
    await next_message(other)
    await next_message(other)
    await client.aclose()

    rejoined = [m.topic for m in server.sent(ChannelEvents.join)[2:]]
    assert rejoined == [other.topic]
    assert channel.state == ChannelStates.CLOSED
    assert server.sent(ChannelEvents.leave) == []


async def test_a_channel_waiting_to_rejoin_is_joined_after_aclose_and_connect(
    server: FakeServer, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("realtime.client.reconnect_delay", after_ten_seconds)
    client = RealtimeClient(server.url)
    channel = client.channel("room")
    await channel.subscribe()

    await server.drop_connections()
    await next_message(channel)
    await client.aclose()
    await client.connect()
    joined = await next_message(channel)
    await client.aclose()

    assert joined == ChannelStateChange(ChannelStates.JOINED)
    assert len(server.sent(ChannelEvents.join)) == 2


async def test_aclose_during_a_rejoin_keeps_the_channel_errored(
    server: FakeServer,
) -> None:
    client = RealtimeClient(server.url)
    channel = client.channel("room")
    await channel.subscribe()

    server.hold_joins = True
    await server.drop_connections()
    await next_message(channel)
    async with asyncio.timeout(2):
        await server.join_held.wait()
    await client.aclose()
    state = channel.state
    server.hold_joins = False
    await client.connect()
    joined = await next_message(channel)
    await client.aclose()

    assert state == ChannelStates.ERRORED
    assert joined == ChannelStateChange(ChannelStates.JOINED)
