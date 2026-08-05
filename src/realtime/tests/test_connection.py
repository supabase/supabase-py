import asyncio
import datetime
import json
import os
from typing import AsyncIterator

import aiohttp
import pytest
from dotenv import load_dotenv
from pydantic import BaseModel
from websockets import broadcast
from yarl import URL

from realtime import (
    RealtimeChannel,
    RealtimeClient,
    RealtimePostgresChangesListenEvent,
    RealtimeSubscribeStates,
)
from realtime.channel import RealtimeChannelOptions
from realtime.client import connect_once
from realtime.message import (
    BroadcastMessage,
    Message,
    PostgresChangesMessage,
    SystemMessage,
)
from realtime.types import DEFAULT_HEARTBEAT_INTERVAL, DEFAULT_TIMEOUT, ChannelEvents

load_dotenv()


SUPABASE_URL = os.getenv("SUPABASE_URL") or "http://127.0.0.1:54321"
PUBLISHABLE_KEY = (
    os.getenv("SUPABASE_PUBLISHABLE_KEY")
    or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0"
)


async def get_token() -> str:
    return PUBLISHABLE_KEY


@pytest.fixture
async def socket() -> AsyncIterator[RealtimeClient]:
    url = f"{SUPABASE_URL}/realtime/v1"
    async with connect_once(url, get_token) as client:
        yield client


class SignupMessageResponse(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
    expires_at: int
    refresh_token: str


async def access_token() -> str:
    url = f"{SUPABASE_URL}/auth/v1/signup"
    headers = {"apikey": PUBLISHABLE_KEY, "Content-Type": "application/json"}
    data = {
        "email": os.getenv("SUPABASE_TEST_EMAIL")
        or f"test_{datetime.datetime.now().strftime('%Y%m%d%H%M%S.%f')}@example.com",
        "password": os.getenv("SUPABASE_TEST_PASSWORD") or "test.123",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            if response.status == 200:
                response_content = await response.read()
                signup_response = SignupMessageResponse.model_validate_json(
                    response_content
                )
                return signup_response.access_token
            else:
                raise Exception(
                    f"Failed to get access token. Status: {response.status}"
                )


async def realtime_send(
    token: str, topic: str, event: str, payload: dict[str, str]
) -> None:
    """
    Trigger a `realtime.send` through PostgREST's rpc endpoint.
    This is done through a public function created in the migration,
    `send_realtime`, that internally calls the unexposed counterpart.
    """
    url = f"{SUPABASE_URL}/rest/v1/rpc/send_realtime"
    headers = {
        "apikey": PUBLISHABLE_KEY,
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    data = {
        "payload": payload,
        "topic": topic,
        "event": event,
        "private": True,
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            response.raise_for_status()


@pytest.mark.asyncio
async def test_broadcast_events(socket: RealtimeClient):
    channel_options = (
        RealtimeChannelOptions()
        .broadcast(listen_self=True, ack=True)
        .presence(enabled=True)
    )
    async with socket.channel(
        "test-broadcast",
        params=channel_options,
    ) as chan:
        # Send 3 broadcast events
        for i in range(3):
            await chan.send_broadcast("test-event", {"message": f"Event {i + 1}"})

        message_stream = chan.messages
        msg1 = await message_stream.__anext__()
        assert isinstance(msg1, BroadcastMessage)
        msg2 = await message_stream.__anext__()
        assert isinstance(msg2, BroadcastMessage)
        msg3 = await message_stream.__anext__()
        assert isinstance(msg3, BroadcastMessage)
        assert msg1.payload["event"] == "test-event"
        assert msg2.payload["event"] == "test-event"
        assert msg3.payload["event"] == "test-event"
        assert msg1.payload["payload"]["message"] == "Event 1"
        assert msg2.payload["payload"]["message"] == "Event 2"
        assert msg3.payload["payload"]["message"] == "Event 3"


@pytest.mark.asyncio
async def test_postgrest_changes(socket: RealtimeClient):
    token = await access_token()
    await socket.set_auth(token)

    channel_options = (
        RealtimeChannelOptions()
        .postgres_changes(RealtimePostgresChangesListenEvent.All, table="todos")
        .postgres_changes(RealtimePostgresChangesListenEvent.Insert, table="todos")
        .postgres_changes(RealtimePostgresChangesListenEvent.Update, table="todos")
        .postgres_changes(RealtimePostgresChangesListenEvent.Delete, table="todos")
    )

    async with socket.channel("test-postgres-changes", channel_options) as chan:
        message_stream = chan.messages
        system_msg = await message_stream.__anext__()
        assert isinstance(system_msg, SystemMessage)
        assert system_msg.payload.status == "ok"
        print("received system message")
        created_todo_id = await create_todo(
            token, {"description": "Test todo", "is_completed": False}
        )
        print("created todo")
        insert = await message_stream.__anext__()
        assert isinstance(insert, PostgresChangesMessage)
        print("received insert")
        await update_todo(
            token,
            created_todo_id,
            {"description": "Updated todo", "is_completed": True},
        )
        update = await message_stream.__anext__()
        assert isinstance(update, PostgresChangesMessage)

        await delete_todo(token, created_todo_id)
        delete = await message_stream.__anext__()
        assert isinstance(delete, PostgresChangesMessage)

    assert insert.payload["data"]["record"] is not None
    assert insert.payload["data"]["record"]["id"] == created_todo_id
    assert insert.payload["data"]["record"]["description"] == "Test todo"
    assert not insert.payload["data"]["record"]["is_completed"]

    assert update.payload["data"]["record"] is not None
    assert update.payload["data"]["record"]["id"] == created_todo_id
    assert update.payload["data"]["record"]["description"] == "Updated todo"
    assert update.payload["data"]["record"]["is_completed"]

    assert delete.payload["data"]["old_record"]["id"] == created_todo_id


@pytest.mark.asyncio
async def test_postgrest_changes_on_different_tables(socket: RealtimeClient):
    token = await access_token()

    await socket.set_auth(token)

    channel_options = (
        RealtimeChannelOptions()
        .postgres_changes(RealtimePostgresChangesListenEvent.Insert, table="todos")
        .postgres_changes(RealtimePostgresChangesListenEvent.Insert, table="messages")
    )
    async with socket.channel(
        "test-postgres-changes", params=channel_options
    ) as channel:
        message_stream = channel.messages
        system_msg = await message_stream.__anext__()
        assert isinstance(system_msg, SystemMessage)
        assert system_msg.payload.status == "ok"
        created_todo_id = await create_todo(
            token, {"description": "Test todo", "is_completed": False}
        )
        insert_todo = await message_stream.__anext__()
        assert isinstance(insert_todo, PostgresChangesMessage)
        created_message_id = await create_message(
            token, {"title": "Test message", "message": "This is a test message"}
        )
        insert_message = await message_stream.__anext__()
        assert isinstance(insert_message, PostgresChangesMessage)

    assert insert_todo.payload["data"]["record"] is not None
    assert insert_todo.payload["data"]["record"]["id"] == created_todo_id
    assert insert_todo.payload["data"]["record"]["description"] == "Test todo"
    assert insert_todo.payload["data"]["record"]["is_completed"] is False

    assert insert_message.payload["data"]["record"] is not None
    assert insert_message.payload["data"]["record"]["id"] == created_message_id
    assert insert_message.payload["data"]["record"]["title"] == "Test message"
    assert (
        insert_message.payload["data"]["record"]["message"] == "This is a test message"
    )


class CreateTodoResponse(BaseModel):
    id: str


async def create_todo(access_token: str, todo: dict) -> str:
    url = f"{SUPABASE_URL}/rest/v1/todos?select=id"
    headers = {
        "apikey": PUBLISHABLE_KEY,
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/vnd.pgrst.object+json",
        "Prefer": "return=representation",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=todo) as response:
            if response.status == 201:
                response_content = await response.read()
                create_todo_response = CreateTodoResponse.model_validate_json(
                    response_content
                )
                return create_todo_response.id
            else:
                raise Exception(f"Failed to create todo. Status: {response.status}")


async def update_todo(access_token: str, id: str, todo: dict):
    url = f"{SUPABASE_URL}/rest/v1/todos?id=eq.{id}"
    headers = {
        "apikey": PUBLISHABLE_KEY,
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    async with aiohttp.ClientSession() as session:
        async with session.patch(url, headers=headers, json=todo) as response:
            if response.status != 204:
                raise Exception(f"Failed to update todo. Status: {response.status}")


class CreateMsgResponse(BaseModel):
    id: int


async def create_message(access_token: str, message: dict) -> int:
    url = f"{SUPABASE_URL}/rest/v1/messages?select=id"
    headers = {
        "apikey": PUBLISHABLE_KEY,
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/vnd.pgrst.object+json",
        "Prefer": "return=representation",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=message) as response:
            if response.status == 201:
                response_content = await response.read()
                create_msg_response = CreateMsgResponse.model_validate_json(
                    response_content
                )
                return create_msg_response.id
            else:
                raise Exception(f"Failed to create message. Status: {response.status}")


async def delete_todo(access_token: str, id: str):
    url = f"{SUPABASE_URL}/rest/v1/todos?id=eq.{id}"
    headers = {
        "apikey": PUBLISHABLE_KEY,
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    async with aiohttp.ClientSession() as session:
        async with session.delete(url, headers=headers) as response:
            if response.status != 204:
                raise Exception(f"Failed to delete todo. Status: {response.status}")


@pytest.mark.asyncio
async def test_subscribe_to_private_channel_with_broadcast_replay(
    socket: RealtimeClient,
):
    """Test that channel subscription sends correct payload with broadcast replay configuration."""
    token = await access_token()

    await socket.set_auth(token)

    messages = 10

    topic = "test-channel"
    event = "broadcast"

    # Calculate replay timestamp
    ten_mins_ago = datetime.datetime.now() - datetime.timedelta(minutes=10)
    ten_mins_ago_ms = int(ten_mins_ago.timestamp() * 1000)

    channel_options = (
        RealtimeChannelOptions()
        .private(True)
        .broadcast(replay_since=ten_mins_ago_ms, replay_limit=messages)
    )

    for i in range(messages):
        await realtime_send(token, topic, event, {"i": str(i)})

    async with socket.channel(topic, params=channel_options) as chan:
        message_stream = chan.messages
        for i in range(messages):
            broadcast = await message_stream.__anext__()
            assert isinstance(broadcast, BroadcastMessage)
            assert broadcast.payload["payload"]["i"] == str(i)
            assert broadcast.payload["meta"]
            assert broadcast.payload["meta"]["replayed"]
