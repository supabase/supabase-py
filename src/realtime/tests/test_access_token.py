import asyncio
import logging
from collections.abc import AsyncIterator

import pytest
from websockets.asyncio.server import Server, ServerConnection, serve
from websockets.exceptions import ConnectionClosed

from realtime import ChannelStates, RealtimeChannel, RealtimeClient
from realtime._serializer import decode, encode
from realtime.message import Message
from realtime.types import ChannelEvents

HOST = "127.0.0.1"


class RecordingServer:
    def __init__(self) -> None:
        self.websocket_server: Server | None = None
        self.url = ""
        self.received: list[Message] = []
        self.join_received = asyncio.Event()
        self.access_token_received = asyncio.Event()
        self.leave_received = asyncio.Event()
        self.heartbeats = 0
        self.heartbeats_received = asyncio.Event()
        self.release_join = asyncio.Event()
        self.release_join.set()

    async def __aenter__(self) -> "RecordingServer":
        self.websocket_server = await serve(self.handler, HOST, 0)
        port = next(iter(self.websocket_server.sockets)).getsockname()[1]
        self.url = f"http://{HOST}:{port}"
        await self.websocket_server.start_serving()
        return self

    async def __aexit__(self, *exception: object) -> None:
        assert self.websocket_server is not None
        self.websocket_server.close()
        await self.websocket_server.wait_closed()

    async def handler(self, connection: ServerConnection) -> None:
        async for raw in connection:
            message = decode(raw)
            self.received.append(message)
            if message.event == ChannelEvents.access_token:
                self.access_token_received.set()
            if message.event == ChannelEvents.leave:
                self.leave_received.set()
            if message.event == ChannelEvents.heartbeat:
                self.heartbeats += 1
                if self.heartbeats >= 3:
                    self.heartbeats_received.set()
            if message.ref is None:
                continue
            if message.event == ChannelEvents.join:
                self.join_received.set()
                await self.release_join.wait()
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

    def joins(self) -> list[Message]:
        return [
            message for message in self.received if message.event == ChannelEvents.join
        ]

    def access_tokens(self, topic: str) -> list[object]:
        return [
            message.payload["access_token"]
            for message in self.received
            if message.event == ChannelEvents.access_token and message.topic == topic
        ]


class Token:
    def __init__(self, value: str) -> None:
        self.value = value

    async def __call__(self) -> str:
        return self.value


@pytest.fixture
async def server() -> AsyncIterator[RecordingServer]:
    async with RecordingServer() as server:
        yield server


async def wait_for_access_token(server: RecordingServer) -> None:
    async with asyncio.timeout(1):
        await server.access_token_received.wait()


async def test_the_first_join_carries_the_token(server: RecordingServer) -> None:
    client = RealtimeClient(server.url, Token("token-1"))

    await client.channel("room").subscribe()
    await client.aclose()

    assert [join.payload["access_token"] for join in server.joins()] == ["token-1"]


async def test_every_join_carries_the_current_token(server: RecordingServer) -> None:
    token = Token("token-1")
    client = RealtimeClient(server.url, token)

    await client.channel("first").subscribe()
    token.value = "token-2"
    await client.channel("second").subscribe()
    await client.aclose()

    assert [join.payload["access_token"] for join in server.joins()] == [
        "token-1",
        "token-2",
    ]
    assert server.access_tokens("realtime:first") == ["token-2"]


async def test_set_auth_sends_the_token_to_joined_channels_right_away(
    server: RecordingServer,
) -> None:
    token = Token("token-1")
    client = RealtimeClient(server.url, token)
    await client.channel("room").subscribe()

    token.value = "token-2"
    await client.set_auth()
    await wait_for_access_token(server)
    await client.aclose()

    assert server.access_tokens("realtime:room") == ["token-2"]
    assert client.last_token == "token-2"


async def test_a_token_set_during_the_join_is_sent_after_it(
    server: RecordingServer,
) -> None:
    token = Token("token-1")
    client = RealtimeClient(server.url, token)
    server.release_join.clear()
    subscribe = asyncio.create_task(client.channel("room").subscribe())

    await server.join_received.wait()
    token.value = "token-2"
    await client.set_auth()
    server.release_join.set()
    await subscribe
    await wait_for_access_token(server)
    await client.aclose()

    assert server.joins()[0].payload["access_token"] == "token-1"
    assert server.access_tokens("realtime:room") == ["token-2"]


async def test_a_failed_send_after_the_join_is_logged(
    server: RecordingServer,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    token = Token("token-1")
    client = RealtimeClient(server.url, token)
    server.release_join.clear()
    channel = client.channel("room")
    subscribe = asyncio.create_task(channel.subscribe())

    await server.join_received.wait()
    token.value = "token-2"
    await client.set_auth()

    async def fail(message: Message) -> None:
        raise OSError("socket closed")

    monkeypatch.setattr(client, "_send_no_wait", fail)
    server.release_join.set()
    with caplog.at_level(logging.WARNING, logger="realtime.client"):
        reply = await subscribe
    await client.aclose()

    assert reply.payload.status == "ok"
    assert "could not send the new access token to realtime:room" in caplog.text


async def test_a_subscribe_cancelled_after_the_join_leaves_the_channel(
    server: RecordingServer, monkeypatch: pytest.MonkeyPatch
) -> None:
    client = RealtimeClient(server.url, Token("token-1"))
    sending_token = asyncio.Event()

    async def wait_forever(channel: RealtimeChannel, joined_with: str | None) -> None:
        sending_token.set()
        await asyncio.Event().wait()

    monkeypatch.setattr(client, "_send_token_if_changed", wait_forever)
    channel = client.channel("room")
    subscribe = asyncio.create_task(channel.subscribe())

    await sending_token.wait()
    subscribe.cancel()
    with pytest.raises(asyncio.CancelledError):
        await subscribe
    async with asyncio.timeout(1):
        await server.leave_received.wait()
    await client.aclose()

    assert channel.state == ChannelStates.CLOSED
    leave = next(
        message for message in server.received if message.event == ChannelEvents.leave
    )
    assert leave.join_ref == channel.join_ref


async def test_a_token_passed_to_set_auth_is_kept_on_joins_and_heartbeats(
    server: RecordingServer,
) -> None:
    client = RealtimeClient(
        server.url,
        Token("callback-token"),
        heartbeat_interval=0.01,
        heartbeat_timeout=1,
    )
    await client.set_auth("user-token")

    await client.channel("room").subscribe()
    async with asyncio.timeout(1):
        await server.heartbeats_received.wait()
    await client.aclose()

    assert [join.payload["access_token"] for join in server.joins()] == ["user-token"]
    assert server.access_tokens("realtime:room") == []
    assert client.last_token == "user-token"


async def test_set_auth_without_a_token_returns_to_the_callback(
    server: RecordingServer,
) -> None:
    client = RealtimeClient(server.url, Token("callback-token"))
    await client.set_auth("user-token")
    await client.channel("room").subscribe()

    await client.set_auth()
    await wait_for_access_token(server)
    await client.aclose()

    assert server.joins()[0].payload["access_token"] == "user-token"
    assert server.access_tokens("realtime:room") == ["callback-token"]


async def test_concurrent_set_auth_calls_send_the_tokens_in_order(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    client = RealtimeClient("ws://localhost")
    for topic in ("first", "second"):
        client.channel(topic).state = ChannelStates.JOINED
    sent: list[tuple[str, object]] = []

    async def send_no_wait(message: Message) -> None:
        await asyncio.sleep(0)
        sent.append((message.topic, message.payload["access_token"]))

    monkeypatch.setattr(client, "_send_no_wait", send_no_wait)

    await asyncio.gather(client.set_auth("token-1"), client.set_auth("token-2"))

    assert sent == [
        ("realtime:first", "token-1"),
        ("realtime:second", "token-1"),
        ("realtime:first", "token-2"),
        ("realtime:second", "token-2"),
    ]
    assert client.last_token == "token-2"


async def test_set_auth_without_a_token_from_the_callback_keeps_the_token() -> None:
    async def no_token() -> None:
        return None

    client = RealtimeClient("ws://localhost", no_token)
    client.last_token = "token-1"

    await client.set_auth()

    assert client.last_token == "token-1"
