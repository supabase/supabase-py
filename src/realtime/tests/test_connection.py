import asyncio
import datetime
import os

import aiohttp
import pytest
from dotenv import load_dotenv

from realtime import AsyncRealtimeChannel, AsyncRealtimeClient, RealtimeSubscribeStates
from realtime.message import Message
from realtime.types import DEFAULT_HEARTBEAT_INTERVAL, DEFAULT_TIMEOUT, ChannelEvents

load_dotenv()


URL = os.getenv("SUPABASE_URL") or "http://127.0.0.1:54321"
ANON_KEY = (
    os.getenv("SUPABASE_ANON_KEY")
    or "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZS1kZW1vIiwicm9sZSI6ImFub24iLCJleHAiOjE5ODM4MTI5OTZ9.CRXP1A7WOeoJeXxjNni43kdQwgnWNReilDMblYTn_I0"
)


@pytest.fixture
def socket() -> AsyncRealtimeClient:
    url = f"{URL}/realtime/v1"
    key = ANON_KEY
    return AsyncRealtimeClient(url, key)


async def access_token() -> str:
    url = f"{URL}/auth/v1/signup"
    headers = {"apikey": ANON_KEY, "Content-Type": "application/json"}
    data = {
        "email": os.getenv("SUPABASE_TEST_EMAIL")
        or f"test_{datetime.datetime.now().strftime('%Y%m%d%H%M%S.%f')}@example.com",
        "password": os.getenv("SUPABASE_TEST_PASSWORD") or "test.123",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=data) as response:
            if response.status == 200:
                json_response = await response.json()
                return json_response.get("access_token")
            else:
                raise Exception(
                    f"Failed to get access token. Status: {response.status}"
                )


def test_init_client():
    client = AsyncRealtimeClient(URL, ANON_KEY)

    assert client is not None
    assert client.url.startswith("ws://") or client.url.startswith("wss://")
    assert "/websocket" in client.url
    assert client.url.split("apikey=")[1] == ANON_KEY
    assert client.auto_reconnect is True
    assert client.params == {}
    assert client.hb_interval == DEFAULT_HEARTBEAT_INTERVAL
    assert client.max_retries == 5
    assert client.initial_backoff == 1.0
    assert client.timeout == DEFAULT_TIMEOUT


@pytest.mark.asyncio
async def test_broadcast_events(socket: AsyncRealtimeClient):
    await socket.connect()

    channel = socket.channel(
        "test-broadcast", params={"config": {"broadcast": {"self": True}}}
    )
    received_events = []

    semaphore = asyncio.Semaphore(0)

    def broadcast_callback(payload):
        print("broadcast: ", payload)
        received_events.append(payload)
        semaphore.release()

    subscribe_event = asyncio.Event()
    await channel.on_broadcast("test-event", broadcast_callback).subscribe(
        lambda state, _: (
            subscribe_event.set()
            if state == RealtimeSubscribeStates.SUBSCRIBED
            else None
        )
    )

    await asyncio.wait_for(subscribe_event.wait(), 5)

    # Send 3 broadcast events
    for i in range(3):
        await channel.send_broadcast("test-event", {"message": f"Event {i + 1}"})
        await asyncio.wait_for(semaphore.acquire(), 5)

    assert len(received_events) == 3
    assert received_events[0]["payload"]["message"] == "Event 1"
    assert received_events[1]["payload"]["message"] == "Event 2"
    assert received_events[2]["payload"]["message"] == "Event 3"

    await socket.close()


@pytest.mark.asyncio
async def test_postgrest_changes(socket: AsyncRealtimeClient):
    token = await access_token()

    await socket.connect()

    await socket.set_auth(token)

    channel: AsyncRealtimeChannel = socket.channel("test-postgres-changes")
    received_events = {"all": [], "insert": [], "update": [], "delete": []}

    def all_changes_callback(payload):
        print("all_changes_callback: ", payload)
        received_events["all"].append(payload)

    insert_event = asyncio.Event()

    def insert_callback(payload):
        print("insert_callback: ", payload)
        received_events["insert"].append(payload)
        insert_event.set()

    update_event = asyncio.Event()

    def update_callback(payload):
        print("update_callback: ", payload)
        received_events["update"].append(payload)
        update_event.set()

    delete_event = asyncio.Event()

    def delete_callback(payload):
        print("delete_callback: ", payload)
        received_events["delete"].append(payload)
        delete_event.set()

    subscribed_event = asyncio.Event()
    system_event = asyncio.Event()

    await (
        channel.on_postgres_changes("*", all_changes_callback, table="todos")
        .on_postgres_changes("INSERT", insert_callback, table="todos")
        .on_postgres_changes("UPDATE", update_callback, table="todos")
        .on_postgres_changes("DELETE", delete_callback, table="todos")
        .on_system(lambda _: system_event.set())
        .subscribe(
            lambda state, _: (
                subscribed_event.set()
                if state == RealtimeSubscribeStates.SUBSCRIBED
                else None
            )
        )
    )

    await asyncio.wait_for(system_event.wait(), 10)

    # Wait for the channel to be subscribed
    await asyncio.wait_for(subscribed_event.wait(), 10)

    created_todo_id = await create_todo(
        token, {"description": "Test todo", "is_completed": False}
    )
    await asyncio.wait_for(insert_event.wait(), 10)

    await update_todo(
        token, created_todo_id, {"description": "Updated todo", "is_completed": True}
    )
    await asyncio.wait_for(update_event.wait(), 10)

    await delete_todo(token, created_todo_id)
    await asyncio.wait_for(delete_event.wait(), 10)

    assert len(received_events["all"]) == 3

    insert = received_events["all"][0]
    update = received_events["all"][1]
    delete = received_events["all"][2]

    assert insert["data"]["record"]["id"] == created_todo_id
    assert insert["data"]["record"]["description"] == "Test todo"
    assert not insert["data"]["record"]["is_completed"]

    assert update["data"]["record"]["id"] == created_todo_id
    assert update["data"]["record"]["description"] == "Updated todo"
    assert update["data"]["record"]["is_completed"]

    assert delete["data"]["old_record"]["id"] == created_todo_id

    assert received_events["insert"] == [insert]
    assert received_events["update"] == [update]
    assert received_events["delete"] == [delete]

    await socket.close()


@pytest.mark.asyncio
async def test_postgrest_changes_on_different_tables(socket: AsyncRealtimeClient):
    token = await access_token()

    await socket.connect()

    await socket.set_auth(token)

    channel: AsyncRealtimeChannel = socket.channel("test-postgres-changes")
    received_events = {"all": [], "insert": []}

    def all_changes_callback(payload):
        print("all_changes_callback: ", payload)
        received_events["all"].append(payload)

    insert_event = asyncio.Event()

    def insert_callback(payload):
        print("insert_callback: ", payload)
        received_events["insert"].append(payload)
        insert_event.set()

    subscribed_event = asyncio.Event()
    system_event = asyncio.Event()

    await (
        channel.on_postgres_changes("*", all_changes_callback, table="todos")
        .on_postgres_changes("INSERT", insert_callback, table="todos")
        .on_postgres_changes("INSERT", insert_callback, table="messages")
        .on_system(lambda _: system_event.set())
        .subscribe(
            lambda state, _: (
                subscribed_event.set()
                if state == RealtimeSubscribeStates.SUBSCRIBED
                else None
            )
        )
    )

    await asyncio.wait_for(system_event.wait(), 10)

    # Wait for the channel to be subscribed
    await asyncio.wait_for(subscribed_event.wait(), 10)

    created_todo_id = await create_todo(
        token, {"description": "Test todo", "is_completed": False}
    )
    await asyncio.wait_for(insert_event.wait(), 10)
    insert_event.clear()

    created_message_id = await create_message(
        token, {"title": "Test message", "message": "This is a test message"}
    )

    await asyncio.wait_for(insert_event.wait(), 10)

    assert len(received_events["all"]) == 1
    assert len(received_events["insert"]) == 2

    insert = received_events["all"][0]
    message_insert = received_events["insert"][1]

    assert insert["data"]["record"]["id"] == created_todo_id
    assert insert["data"]["record"]["description"] == "Test todo"
    assert insert["data"]["record"]["is_completed"] == False

    assert received_events["insert"] == [insert, message_insert]

    assert message_insert["data"]["record"]["id"] == created_message_id
    assert message_insert["data"]["record"]["title"] == "Test message"
    assert message_insert["data"]["record"]["message"] == "This is a test message"

    assert received_events["insert"] == [insert, message_insert]
    await socket.close()


async def create_todo(access_token: str, todo: dict) -> str:
    url = f"{URL}/rest/v1/todos?select=id"
    headers = {
        "apikey": ANON_KEY,
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/vnd.pgrst.object+json",
        "Prefer": "return=representation",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=todo) as response:
            if response.status == 201:
                json_response = await response.json()
                return json_response.get("id")
            else:
                raise Exception(f"Failed to create todo. Status: {response.status}")


async def update_todo(access_token: str, id: str, todo: dict):
    url = f"{URL}/rest/v1/todos?id=eq.{id}"
    headers = {
        "apikey": ANON_KEY,
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    async with aiohttp.ClientSession() as session:
        async with session.patch(url, headers=headers, json=todo) as response:
            if response.status != 204:
                raise Exception(f"Failed to update todo. Status: {response.status}")


async def create_message(access_token: str, message: dict) -> str:
    url = f"{URL}/rest/v1/messages?select=id"
    headers = {
        "apikey": ANON_KEY,
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
        "Accept": "application/vnd.pgrst.object+json",
        "Prefer": "return=representation",
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=message) as response:
            if response.status == 201:
                json_response = await response.json()
                return json_response.get("id")
            else:
                raise Exception(f"Failed to create message. Status: {response.status}")


async def delete_todo(access_token: str, id: str):
    url = f"{URL}/rest/v1/todos?id=eq.{id}"
    headers = {
        "apikey": ANON_KEY,
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json",
    }

    async with aiohttp.ClientSession() as session:
        async with session.delete(url, headers=headers) as response:
            if response.status != 204:
                raise Exception(f"Failed to delete todo. Status: {response.status}")


@pytest.mark.asyncio
async def test_multiple_connect_attempts(socket: AsyncRealtimeClient):
    # First connection should succeed
    await socket.connect()
    assert socket.is_connected
    initial_ws = socket._ws_connection

    # Second connection attempt should be a no-op since we're already connected
    await socket.connect()
    assert socket.is_connected
    assert socket._ws_connection == initial_ws  # Should be the same connection object

    await socket.close()
    assert not socket.is_connected

    # Test connection failure and retry behavior
    # Temporarily modify the URL to force a connection failure
    original_url = socket.url
    socket.url = "ws://invalid-url-that-will-fail:12345/websocket"
    socket.max_retries = 2  # Reduce retries for faster test
    socket.initial_backoff = 0.1  # Reduce backoff for faster test

    start_time = datetime.datetime.now()

    with pytest.raises(Exception) as exc_info:
        await socket.connect()

    end_time = datetime.datetime.now()
    duration = (end_time - start_time).total_seconds()

    # Should have tried to connect max_retries times with exponential backoff
    # First attempt: immediate
    # Second attempt: after 0.1s
    # Total time should be at least the sum of backoff times but not much more
    assert duration >= 0.1, "Should have waited for backoff between retries"
    assert duration < 1.0, "Should not have waited longer than necessary"

    # The error message can vary depending on the system and Python version
    # Common messages include DNS resolution errors or connection refused
    error_msg = str(exc_info.value)
    assert any(
        msg in error_msg.lower()
        for msg in [
            "temporary failure in name resolution",
            "nodename nor servname provided",
            "name or service not known",
            "connection refused",
            "failed to establish",
        ]
    ), f"Unexpected error message: {error_msg}"

    # Restore original URL and verify we can connect again
    socket.url = original_url
    await socket.connect()
    assert socket.is_connected

    await socket.close()


@pytest.mark.asyncio
async def test_send_message_reconnection(socket: AsyncRealtimeClient):
    # First establish a connection
    await socket.connect()
    assert socket.is_connected

    # Create a channel and subscribe to it
    channel = socket.channel("test-channel")
    subscribe_event = asyncio.Event()
    await channel.subscribe(
        lambda state, _: (
            subscribe_event.set()
            if state == RealtimeSubscribeStates.SUBSCRIBED
            else None
        )
    )
    await asyncio.wait_for(subscribe_event.wait(), 5)

    # Simulate a connection failure by closing the WebSocket
    if socket._ws_connection:
        await socket._ws_connection.close()

    # Try to send a message - this should trigger reconnection
    message = Message(
        topic="test-channel",
        event=ChannelEvents.broadcast,
        payload={"test": "data"},
    )
    await socket.send(message)

    # Wait for reconnection to complete
    await asyncio.sleep(1)  # Give some time for reconnection

    # Verify we're connected again
    assert socket.is_connected

    # Try sending another message to verify the connection is working
    await socket.send(message)

    await socket.close()
