import json
import os
from unittest.mock import AsyncMock

import pytest

from realtime import AsyncRealtimeChannel, AsyncRealtimeClient

URL = os.getenv("SUPABASE_URL") or "http://127.0.0.1:54321"
PUBLISHABLE_KEY = (
    os.getenv("SUPABASE_PUBLISHABLE_KEY")
    or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0"
)


@pytest.fixture
def socket() -> AsyncRealtimeClient:
    url = f"{URL}/realtime/v1"
    return AsyncRealtimeClient(url, PUBLISHABLE_KEY)


def sent_messages(mock_ws: AsyncMock) -> list[dict]:
    return [json.loads(call.args[0]) for call in mock_ws.send.call_args_list]


async def subscribe(channel: AsyncRealtimeChannel) -> None:
    await channel.subscribe(lambda state, error: None)


@pytest.mark.asyncio
async def test_join_carries_join_ref_equal_to_its_own_ref(socket: AsyncRealtimeClient):
    mock_ws = AsyncMock()
    socket._ws_connection = mock_ws
    await socket.connect()

    channel = socket.channel("test-join-ref")
    await subscribe(channel)

    [join_message] = sent_messages(mock_ws)
    assert join_message["event"] == "phx_join"
    assert join_message["join_ref"] == join_message["ref"]
    assert join_message["join_ref"] == channel.join_push.ref

    await socket.close()


@pytest.mark.asyncio
async def test_broadcast_push_carries_channel_join_ref(socket: AsyncRealtimeClient):
    mock_ws = AsyncMock()
    socket._ws_connection = mock_ws
    await socket.connect()

    channel = socket.channel(
        "test-join-ref-broadcast",
        params={
            "config": {
                "broadcast": {"ack": True, "self": False},
                "presence": {"key": "", "enabled": False},
                "private": False,
            }
        },
    )
    await subscribe(channel)
    mock_ws.send.reset_mock()

    await channel.send_broadcast("cursor", {"x": 1})

    [broadcast_message] = sent_messages(mock_ws)
    assert broadcast_message["event"] == "broadcast"
    assert broadcast_message["join_ref"] == channel.join_push.ref
    assert broadcast_message["join_ref"] is not None

    await socket.close()


@pytest.mark.asyncio
async def test_presence_track_and_untrack_carry_channel_join_ref(
    socket: AsyncRealtimeClient,
):
    mock_ws = AsyncMock()
    socket._ws_connection = mock_ws
    await socket.connect()

    channel = socket.channel(
        "test-join-ref-presence",
        params={
            "config": {
                "broadcast": {"ack": False, "self": False},
                "presence": {"key": "", "enabled": True},
                "private": False,
            }
        },
    )
    await subscribe(channel)
    mock_ws.send.reset_mock()

    await channel.track({"id": 123})
    await channel.untrack()

    track_message, untrack_message = sent_messages(mock_ws)
    assert track_message["payload"]["event"] == "track"
    assert track_message["join_ref"] == channel.join_push.ref

    assert untrack_message["payload"]["event"] == "untrack"
    assert untrack_message["join_ref"] == channel.join_push.ref

    await socket.close()


@pytest.mark.asyncio
async def test_leave_push_carries_channel_join_ref(socket: AsyncRealtimeClient):
    mock_ws = AsyncMock()
    socket._ws_connection = mock_ws
    await socket.connect()

    channel = socket.channel("test-join-ref-leave")
    await subscribe(channel)
    join_ref = channel.join_push.ref
    mock_ws.send.reset_mock()

    await channel.unsubscribe()

    [leave_message] = sent_messages(mock_ws)
    assert leave_message["event"] == "phx_leave"
    assert leave_message["join_ref"] == join_ref

    await socket.close()


@pytest.mark.asyncio
async def test_rejoin_sends_fresh_join_ref(socket: AsyncRealtimeClient):
    mock_ws = AsyncMock()
    socket._ws_connection = mock_ws
    await socket.connect()

    channel = socket.channel("test-join-ref-rejoin")
    await subscribe(channel)
    original_join_ref = channel.join_push.ref
    mock_ws.send.reset_mock()

    await channel._rejoin()

    [rejoin_message] = sent_messages(mock_ws)
    new_join_ref = channel.join_push.ref
    assert new_join_ref != original_join_ref
    assert rejoin_message["join_ref"] == new_join_ref
    assert rejoin_message["ref"] == new_join_ref

    await socket.close()
