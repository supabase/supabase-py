import json
import os
from unittest.mock import AsyncMock

import pytest

from realtime import AsyncRealtimeChannel, AsyncRealtimeClient
from realtime.message import ServerMessageAdapter
from realtime.types import BroadcastPayload

URL = os.getenv("SUPABASE_URL") or "http://127.0.0.1:54321"
PUBLISHABLE_KEY = (
    os.getenv("SUPABASE_PUBLISHABLE_KEY")
    or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0"
)

INSERT_PAYLOAD = {"event": "INSERT", "payload": {"record": {"id": 1}}}


@pytest.fixture
def socket() -> AsyncRealtimeClient:
    url = f"{URL}/realtime/v1"
    return AsyncRealtimeClient(url, PUBLISHABLE_KEY)


async def subscribed_channel(socket: AsyncRealtimeClient) -> AsyncRealtimeChannel:
    socket._ws_connection = AsyncMock()
    await socket.connect()
    channel = socket.channel("test-broadcast-callback")
    await channel.subscribe(lambda state, error: None)
    return channel


def receive_broadcast(channel: AsyncRealtimeChannel, payload: dict) -> None:
    frame = {
        "event": "broadcast",
        "topic": channel.topic,
        "payload": {"type": "broadcast", **payload},
        "ref": None,
    }
    channel._handle_message(ServerMessageAdapter.validate_json(json.dumps(frame)))


@pytest.mark.asyncio
async def test_wildcard_and_matching_listeners_receive_broadcast(
    socket: AsyncRealtimeClient,
):
    channel = await subscribed_channel(socket)
    wildcard: list[BroadcastPayload] = []
    insert: list[BroadcastPayload] = []
    delete: list[BroadcastPayload] = []
    channel.on_broadcast("*", wildcard.append)
    channel.on_broadcast("INSERT", insert.append)
    channel.on_broadcast("DELETE", delete.append)

    receive_broadcast(channel, INSERT_PAYLOAD)

    assert wildcard == [INSERT_PAYLOAD]
    assert insert == [INSERT_PAYLOAD]
    assert delete == []

    await socket.close()


@pytest.mark.asyncio
async def test_broadcast_event_matching_ignores_case(socket: AsyncRealtimeClient):
    channel = await subscribed_channel(socket)
    received: list[BroadcastPayload] = []
    channel.on_broadcast("insert", received.append)

    receive_broadcast(channel, INSERT_PAYLOAD)

    assert received == [INSERT_PAYLOAD]

    await socket.close()
