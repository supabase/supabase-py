import asyncio
import itertools
from collections.abc import AsyncIterator

import pytest
from websockets.asyncio.server import Server, ServerConnection, serve

from realtime._serializer import decode, encode
from realtime.client import connect_once
from realtime.message import Message
from realtime.types import ChannelEvents

HOST = "127.0.0.1"


class HeartbeatServer:
    """Acks every heartbeat and records when each one arrives."""

    def __init__(self, expected_heartbeats: int) -> None:
        self.ws_server: Server | None = None
        self.url = ""
        self.expected_heartbeats = expected_heartbeats
        self.heartbeat_times: list[float] = []
        self.received_expected = asyncio.Event()

    async def __aenter__(self) -> "HeartbeatServer":
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
        async for raw in connection:
            message = decode(raw)
            if message.event != ChannelEvents.heartbeat or message.ref is None:
                continue
            reply = Message(
                event=ChannelEvents.reply,
                topic=message.topic,
                ref=message.ref,
                payload={"status": "ok", "response": {}},
            )
            self.heartbeat_times.append(asyncio.get_running_loop().time())
            await connection.send(encode(reply))
            if len(self.heartbeat_times) >= self.expected_heartbeats:
                self.received_expected.set()


@pytest.fixture
async def server() -> AsyncIterator[HeartbeatServer]:
    async with HeartbeatServer(expected_heartbeats=3) as server:
        yield server


async def test_heartbeat_interval_below_fifteen_seconds_is_honored(
    server: HeartbeatServer,
) -> None:
    interval = 0.05

    async with connect_once(server.url, heartbeat_interval=interval):
        await asyncio.wait_for(server.received_expected.wait(), timeout=5)

    times = server.heartbeat_times
    gaps = [later - earlier for earlier, later in itertools.pairwise(times)]
    assert len(times) >= 3
    assert all(gap >= interval * 0.8 for gap in gaps)


@pytest.mark.parametrize(
    ("heartbeat_interval", "heartbeat_timeout", "message"),
    [
        (0, 5, "heartbeat_interval must be positive"),
        (-1.5, 5, "heartbeat_interval must be positive"),
        (25, 0, "heartbeat_timeout must be positive"),
        (25, -0.5, "heartbeat_timeout must be positive"),
        (float("nan"), 5, "heartbeat_interval must be positive"),
        (25, float("nan"), "heartbeat_timeout must be positive"),
    ],
)
def test_connect_once_rejects_non_positive_heartbeat_durations(
    heartbeat_interval: float, heartbeat_timeout: float, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        connect_once(
            "http://localhost",
            heartbeat_interval=heartbeat_interval,
            heartbeat_timeout=heartbeat_timeout,
        )


def test_connect_once_accepts_fractional_heartbeat_durations() -> None:
    connection = connect_once(
        "http://localhost", heartbeat_interval=2.5, heartbeat_timeout=0.5
    )

    assert connection.heartbeat_interval == 2.5
    assert connection.heartbeat_timeout == 0.5
