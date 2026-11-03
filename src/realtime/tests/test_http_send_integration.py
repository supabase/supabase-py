"""End-to-end tests for `http_send` against a running local Supabase stack."""

import asyncio
import os
import uuid
from collections.abc import AsyncIterator
from typing import Any

import httpx
import pytest
import pytest_asyncio
from dotenv import load_dotenv

from realtime import (
    AsyncRealtimeChannel,
    AsyncRealtimeClient,
    RealtimeHTTPError,
    RealtimeSubscribeStates,
)
from realtime.types import RealtimeChannelOptions

load_dotenv()

URL = os.getenv("SUPABASE_URL") or "http://127.0.0.1:54321"
PUBLISHABLE_KEY = (
    os.getenv("SUPABASE_PUBLISHABLE_KEY")
    or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0"
)
REALTIME_URL = f"{URL}/realtime/v1"


async def sign_up() -> str:
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{URL}/auth/v1/signup",
            headers={"apikey": PUBLISHABLE_KEY},
            json={
                "email": f"http_send_{uuid.uuid4().hex}@example.com",
                "password": "test.123",
            },
        )
    response.raise_for_status()
    return str(response.json()["access_token"])


async def subscribe(
    client: AsyncRealtimeClient, topic: str, private: bool = False, event: str = "evt"
) -> tuple[AsyncRealtimeChannel, "asyncio.Queue[Any]"]:
    channel = client.channel(
        topic,
        params={
            "config": {
                "broadcast": {"self": False, "ack": False},
                "presence": {"enabled": False, "key": ""},
                "private": private,
            }
        },
    )
    received: asyncio.Queue[Any] = asyncio.Queue()
    subscribed = asyncio.Event()
    errors: list[Any] = []

    def on_state(state: RealtimeSubscribeStates, error: Any) -> None:
        if state == RealtimeSubscribeStates.SUBSCRIBED:
            subscribed.set()
        elif error is not None:
            errors.append(error)

    await channel.on_broadcast(event, received.put_nowait).subscribe(on_state)
    await asyncio.wait_for(subscribed.wait(), 10)
    assert not errors
    return channel, received


def private_options() -> RealtimeChannelOptions:
    return {"config": {"broadcast": None, "presence": None, "private": True}}


@pytest_asyncio.fixture
async def receiver() -> AsyncIterator[AsyncRealtimeClient]:
    client = AsyncRealtimeClient(REALTIME_URL, PUBLISHABLE_KEY)
    await client.connect()
    yield client
    await client.close()


@pytest_asyncio.fixture
async def sender() -> AsyncIterator[AsyncRealtimeClient]:
    # Never connects: http_send must not depend on the websocket.
    client = AsyncRealtimeClient(REALTIME_URL, PUBLISHABLE_KEY)
    yield client
    await client.close()


@pytest.mark.asyncio
async def test_http_send_delivers_to_subscribers(
    receiver: AsyncRealtimeClient, sender: AsyncRealtimeClient
) -> None:
    topic = f"http-send-{uuid.uuid4().hex}"
    _, received = await subscribe(receiver, topic)

    result = await sender.channel(topic).http_send("evt", {"hello": "world"})

    assert result == {"success": True}
    message = await asyncio.wait_for(received.get(), 5)
    assert message["event"] == "evt"
    assert message["payload"] == {"hello": "world"}


@pytest.mark.asyncio
async def test_http_send_encodes_topic_and_event(
    receiver: AsyncRealtimeClient, sender: AsyncRealtimeClient
) -> None:
    topic = f"http send/{uuid.uuid4().hex}:room"
    _, received = await subscribe(receiver, topic, event="my event/1")

    await sender.channel(topic).http_send("my event/1", {"ok": True})

    message = await asyncio.wait_for(received.get(), 5)
    assert message["event"] == "my event/1"
    assert message["payload"] == {"ok": True}


@pytest.mark.asyncio
async def test_http_send_on_private_channel_with_user_token(
    receiver: AsyncRealtimeClient, sender: AsyncRealtimeClient
) -> None:
    token = await sign_up()
    await receiver.set_auth(token)
    await sender.set_auth(token)
    topic = f"http-send-private-{uuid.uuid4().hex}"
    _, received = await subscribe(receiver, topic, private=True)

    result = await sender.channel(topic, private_options()).http_send(
        "evt", {"secret": 1}
    )

    assert result == {"success": True}
    message = await asyncio.wait_for(received.get(), 5)
    assert message["payload"] == {"secret": 1}


@pytest.mark.asyncio
async def test_http_send_private_channel_without_user_is_rejected(
    sender: AsyncRealtimeClient,
) -> None:
    channel = sender.channel(f"http-send-denied-{uuid.uuid4().hex}", private_options())
    with pytest.raises(RealtimeHTTPError, match="Unauthorized") as exc_info:
        await channel.http_send("evt", {"secret": 1})
    assert exc_info.value.status == 403


@pytest.mark.asyncio
async def test_http_send_default_timeout_is_not_too_short(
    receiver: AsyncRealtimeClient, sender: AsyncRealtimeClient
) -> None:
    # The client timeout is in seconds; it must not be misread as milliseconds.
    assert sender.timeout >= 1
    topic = f"http-send-timeout-{uuid.uuid4().hex}"
    _, received = await subscribe(receiver, topic)
    assert await sender.channel(topic).http_send("evt", {"n": 1}, timeout=30) == {
        "success": True
    }
    await asyncio.wait_for(received.get(), 5)


@pytest.mark.asyncio
async def test_http_send_with_invalid_api_key_raises() -> None:
    client = AsyncRealtimeClient(REALTIME_URL, "not-a-valid-key")
    with pytest.raises(RealtimeHTTPError, match="Unauthorized") as exc_info:
        await client.channel("http-send-bad-key").http_send("evt", {"a": 1})
    assert exc_info.value.status in (401, 403)
    await client.close()
