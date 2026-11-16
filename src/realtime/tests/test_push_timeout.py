import asyncio
import logging
from collections.abc import AsyncIterator
from typing import TYPE_CHECKING

import pytest
from websockets.asyncio.server import Server, ServerConnection, serve
from websockets.exceptions import ConnectionClosed

from realtime import (
    AuthorizationError,
    ChannelClosedError,
    ChannelJoinError,
    ChannelStates,
    NotConnectedError,
    RealtimeChannelOptions,
    RealtimeClient,
    RealtimeTimeoutError,
)
from realtime._serializer import decode, encode
from realtime.client import connect_once
from realtime.message import Message
from realtime.types import ChannelEvents

if TYPE_CHECKING:
    from supabase_utils.types import JSON

HOST = "127.0.0.1"


class FakeServer:
    def __init__(self) -> None:
        self.ws_server: Server | None = None
        self.url = ""
        self.connections: list[ServerConnection] = []
        self.received: list[Message] = []
        self.silent_events: set[str] = set()
        self.join_reply: dict[str, JSON] = {
            "status": "ok",
            "response": {"postgres_changes": []},
        }
        self.drop_on_join = False
        self.presence_received = asyncio.Event()

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
            if message.event == ChannelEvents.presence:
                self.presence_received.set()
            if message.ref is None or message.event in self.silent_events:
                continue
            if message.event == ChannelEvents.join and self.drop_on_join:
                await connection.close()
                return
            payload: dict[str, JSON] = {"status": "ok", "response": {}}
            if message.event == ChannelEvents.join:
                payload = self.join_reply
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

    def sent(self, event: ChannelEvents) -> list[Message]:
        return [message for message in self.received if message.event == event]


def wait_an_hour(attempt: int) -> float:
    return 3600.0


@pytest.fixture(autouse=True)
def no_reconnect(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("realtime.client.reconnect_delay", wait_an_hour)


@pytest.fixture
async def server() -> AsyncIterator[FakeServer]:
    async with FakeServer() as server:
        yield server


async def test_a_join_without_a_reply_times_out_and_is_left(
    server: FakeServer,
) -> None:
    server.silent_events = {ChannelEvents.join}
    async with connect_once(server.url, timeout=0.1) as client:
        channel = client.channel("room")
        with pytest.raises(RealtimeTimeoutError) as error:
            await channel.subscribe()
        await asyncio.sleep(0.05)
        connected = client._is_connected()

    assert error.value.event == ChannelEvents.join
    assert error.value.topic == channel.topic
    assert error.value.timeout == 0.1
    assert channel.state == ChannelStates.CLOSED
    assert connected
    (join,) = server.sent(ChannelEvents.join)
    (leave,) = server.sent(ChannelEvents.leave)
    assert leave.join_ref == join.ref


async def test_a_presence_update_without_a_reply_times_out(
    server: FakeServer,
) -> None:
    server.silent_events = {ChannelEvents.presence}
    async with connect_once(server.url, timeout=0.1) as client:
        channel = client.channel("room")
        await channel.subscribe()
        with pytest.raises(RealtimeTimeoutError):
            await channel.track({"user": "a"})
        connected = client._is_connected()

    assert connected
    assert client.message_refs == {}


async def test_a_presence_update_can_be_given_a_shorter_timeout(
    server: FakeServer,
) -> None:
    server.silent_events = {ChannelEvents.presence}
    async with connect_once(server.url, timeout=10) as client:
        channel = client.channel("room")
        await channel.subscribe()
        with pytest.raises(TimeoutError):
            async with asyncio.timeout(0.1):
                await channel.track({"user": "a"})
        joined = channel.joined

    assert joined
    assert client.message_refs == {}
    assert channel._pending_presence == set()


async def send_to_client(server: FakeServer, message: Message) -> None:
    await server.connections[-1].send(encode(message))


@pytest.mark.parametrize("event", [ChannelEvents.close, ChannelEvents.error])
@pytest.mark.parametrize("untrack", [False, True], ids=["track", "untrack"])
async def test_a_presence_update_fails_at_once_when_the_channel_closes(
    server: FakeServer, event: ChannelEvents, untrack: bool
) -> None:
    server.silent_events = {ChannelEvents.presence}
    async with connect_once(server.url, timeout=10) as client:
        channel = client.channel("room")
        await channel.subscribe()
        call = channel.untrack() if untrack else channel.track({"user": "a"})
        pending = asyncio.ensure_future(call)
        await asyncio.wait_for(server.presence_received.wait(), timeout=1)
        await send_to_client(
            server,
            Message(
                event=event,
                topic=channel.topic,
                payload={},
                join_ref=channel.join_ref,
            ),
        )
        with pytest.raises(ChannelClosedError) as error:
            await asyncio.wait_for(pending, timeout=1)

    assert error.value.reason is None
    assert error.value.topic == channel.topic
    assert client.message_refs == {}


async def test_a_presence_update_fails_with_the_servers_system_error(
    server: FakeServer,
) -> None:
    server.silent_events = {ChannelEvents.presence}
    async with connect_once(server.url, timeout=10) as client:
        channel = client.channel("room")
        await channel.subscribe()
        pending = asyncio.ensure_future(channel.track({"user": "a"}))
        await asyncio.wait_for(server.presence_received.wait(), timeout=1)
        reason = "Client presence rate limit exceeded"
        await send_to_client(
            server,
            Message(
                event=ChannelEvents.system,
                topic=channel.topic,
                payload={
                    "channel": "room",
                    "extension": "presence",
                    "message": reason,
                    "status": "error",
                },
            ),
        )
        await send_to_client(
            server,
            Message(
                event=ChannelEvents.close,
                topic=channel.topic,
                payload={},
                join_ref=channel.join_ref,
            ),
        )
        with pytest.raises(ChannelClosedError) as error:
            await asyncio.wait_for(pending, timeout=1)

    assert error.value.reason == reason
    assert reason in str(error.value)


async def test_a_presence_update_fails_at_once_on_unsubscribe(
    server: FakeServer,
) -> None:
    server.silent_events = {ChannelEvents.presence}
    async with connect_once(server.url, timeout=10) as client:
        channel = client.channel("room")
        await channel.subscribe()
        pending = asyncio.ensure_future(channel.track({"user": "a"}))
        await asyncio.wait_for(server.presence_received.wait(), timeout=1)
        await channel.unsubscribe()
        with pytest.raises(ChannelClosedError):
            await asyncio.wait_for(pending, timeout=1)


async def test_a_presence_update_of_an_earlier_join_is_not_failed_by_its_close(
    server: FakeServer,
) -> None:
    server.silent_events = {ChannelEvents.presence}
    async with connect_once(server.url, timeout=0.3) as client:
        channel = client.channel("room")
        await channel.subscribe()
        pending = asyncio.ensure_future(channel.track({"user": "a"}))
        await asyncio.wait_for(server.presence_received.wait(), timeout=1)
        await send_to_client(
            server,
            Message(
                event=ChannelEvents.close,
                topic=channel.topic,
                payload={},
                join_ref="earlier",
            ),
        )
        with pytest.raises(RealtimeTimeoutError):
            await asyncio.wait_for(pending, timeout=1)


async def test_an_unsubscribe_without_a_reply_times_out(server: FakeServer) -> None:
    server.silent_events = {ChannelEvents.leave}
    client = RealtimeClient(server.url, timeout=0.1)
    channel = client.channel("room")
    await channel.subscribe()

    with pytest.raises(RealtimeTimeoutError):
        await channel.unsubscribe()

    assert channel.state == ChannelStates.CLOSED
    assert client.channels == {}


async def test_an_acknowledged_broadcast_without_a_reply_times_out(
    server: FakeServer,
) -> None:
    server.silent_events = {ChannelEvents.broadcast}
    async with connect_once(server.url, timeout=0.1) as client:
        options = RealtimeChannelOptions().broadcast(ack=True)
        async with client.channel("room", options) as channel:
            with pytest.raises(RealtimeTimeoutError):
                await channel.send_broadcast("ping", {})


async def test_the_heartbeat_uses_its_own_timeout(server: FakeServer) -> None:
    server.silent_events = {ChannelEvents.heartbeat}
    async with connect_once(
        server.url, heartbeat_interval=0.05, heartbeat_timeout=0.05, timeout=10
    ) as client:
        failure = client._connection_failure
        assert failure is not None
        with pytest.raises(RealtimeTimeoutError) as error:
            await asyncio.wait_for(failure, timeout=1)

    assert error.value.event == ChannelEvents.heartbeat
    assert error.value.timeout == 0.05


async def test_a_heartbeat_timeout_during_a_join_raises_not_connected(
    server: FakeServer,
) -> None:
    server.silent_events = {ChannelEvents.join, ChannelEvents.heartbeat}
    client = RealtimeClient(
        server.url, heartbeat_interval=0.05, heartbeat_timeout=0.05, timeout=10
    )
    channel = client.channel("room")

    with pytest.raises(NotConnectedError) as error:
        await asyncio.wait_for(channel.subscribe(), timeout=2)
    await client.aclose()

    cause = error.value.__cause__
    assert isinstance(cause, RealtimeTimeoutError)
    assert cause.event == ChannelEvents.heartbeat
    assert server.sent(ChannelEvents.leave) == []


async def test_leaving_on_exit_without_a_reply_does_not_raise(
    server: FakeServer,
) -> None:
    server.silent_events = {ChannelEvents.leave}
    client = RealtimeClient(server.url, timeout=0.1)

    async with client.channel("room") as channel:
        pass

    assert channel.state == ChannelStates.CLOSED
    await client.aclose()


@pytest.mark.parametrize(
    ("reason", "error_class", "code"),
    [
        (
            "Unauthorized: You do not have permissions to read from this Channel topic",
            AuthorizationError,
            "Unauthorized",
        ),
        ("InvalidJWTToken: Token has expired", AuthorizationError, "InvalidJWTToken"),
        (
            "ChannelRateLimitReached: Too many channels",
            ChannelJoinError,
            "ChannelRateLimitReached",
        ),
        ("Unknown Error on Channel", ChannelJoinError, None),
    ],
)
async def test_a_rejected_join_raises_a_classified_error(
    server: FakeServer,
    reason: str,
    error_class: type[ChannelJoinError],
    code: str | None,
) -> None:
    server.join_reply = {"status": "error", "response": {"reason": reason}}
    async with connect_once(server.url) as client:
        channel = client.channel("room")
        with pytest.raises(ChannelJoinError) as error:
            await channel.subscribe()

    assert type(error.value) is error_class
    assert error.value.reason == reason
    assert error.value.code == code
    assert error.value.topic == channel.topic
    assert channel.state == ChannelStates.CLOSED


async def test_a_rejected_join_without_a_reason_keeps_the_response(
    server: FakeServer,
) -> None:
    server.join_reply = {"status": "error", "response": {"unexpected": 1}}
    async with connect_once(server.url) as client:
        with pytest.raises(ChannelJoinError, match="unexpected"):
            await client.channel("room").subscribe()


async def test_a_connection_dropped_during_the_join_raises_not_connected(
    server: FakeServer,
) -> None:
    server.drop_on_join = True
    client = RealtimeClient(server.url)
    channel = client.channel("room")

    with pytest.raises(NotConnectedError) as error:
        await channel.subscribe()
    await client.aclose()

    assert isinstance(error.value.__cause__, ConnectionClosed)
    assert channel.state == ChannelStates.CLOSED


@pytest.mark.parametrize(
    ("timeout", "max_queued_messages", "message"),
    [
        (0, 10, "timeout must be positive"),
        (-1, 10, "timeout must be positive"),
        (float("nan"), 10, "timeout must be positive"),
        (10, 0, "max_queued_messages must be positive"),
    ],
)
def test_non_positive_options_are_rejected(
    timeout: float, max_queued_messages: int, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        RealtimeClient(
            "http://localhost", timeout=timeout, max_queued_messages=max_queued_messages
        )


def test_a_full_queue_drops_its_oldest_message_and_warns_once(
    caplog: pytest.LogCaptureFixture,
) -> None:
    channel = RealtimeClient("http://localhost", max_queued_messages=2).channel("room")

    with caplog.at_level(logging.WARNING, logger="realtime.channel"):
        for index in range(4):
            channel._receive(
                Message(
                    event=ChannelEvents.broadcast,
                    topic=channel.topic,
                    payload={"index": index},
                )
            )

    queued = [channel.message_stream.get_nowait() for _ in range(2)]
    assert [m.payload["index"] for m in queued if isinstance(m, Message)] == [2, 3]
    assert len([r for r in caplog.records if "is full" in r.message]) == 1


def test_a_full_queue_warns_again_after_it_was_read(
    caplog: pytest.LogCaptureFixture,
) -> None:
    channel = RealtimeClient("http://localhost", max_queued_messages=1).channel("room")
    message = Message(event=ChannelEvents.broadcast, topic=channel.topic, payload={})

    with caplog.at_level(logging.WARNING, logger="realtime.channel"):
        channel._receive(message)
        channel._receive(message)
        channel.message_stream.get_nowait()
        channel._receive(message)
        channel._receive(message)

    assert len([r for r in caplog.records if "is full" in r.message]) == 2


def test_a_full_queue_keeps_the_presence_state() -> None:
    channel = RealtimeClient("http://localhost", max_queued_messages=1).channel("room")
    _listener = channel.presence_events()

    channel._receive(
        Message(
            event=ChannelEvents.presence_state,
            topic=channel.topic,
            payload={"alice": {"metas": [{"phx_ref": "ref-alice"}]}},
        )
    )
    channel._receive(
        Message(
            event=ChannelEvents.presence_diff,
            topic=channel.topic,
            payload={
                "joins": {"bob": {"metas": [{"phx_ref": "ref-bob"}]}},
                "leaves": {},
            },
        )
    )

    assert set(channel.presence_state()) == {"alice", "bob"}
    assert channel.message_stream.qsize() == 0
    assert [queue.qsize() for queue in channel._presence_listeners] == [1]
