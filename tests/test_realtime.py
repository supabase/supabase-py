import pytest
from supabase import create_client
from supabase._sync.realtime_client import RealtimeClient, RealtimeMessage, RealtimeChannel

def test_realtime_message():
    message = RealtimeMessage(
        event="test_event",
        topic="test_topic",
        payload={"data": "test"}
    )
    assert message.event == "test_event"
    assert message.topic == "test_topic"
    assert message.payload == {"data": "test"}

def test_realtime_channel():
    channel = RealtimeChannel("test_topic")
    assert channel.topic == "test_topic"
    assert channel.params == {}
    assert not channel.subscribed

    def callback(message):
        pass

    channel.subscribe(callback)
    assert len(channel.listeners) == 1

    channel.unsubscribe()
    assert len(channel.listeners) == 0

def test_realtime_client_initialization():
    url = "ws://localhost:4000/socket"
    key = "test-key"
    client = RealtimeClient(url, key)
    assert client.url == url
    assert client.token == key
    assert not client._connected

def test_realtime_channel_creation():
    url = "ws://localhost:4000/socket"
    key = "test-key"
    client = RealtimeClient(url, key)
    
    channel = client.channel("test_topic")
    assert channel.topic == "test_topic"
    assert "test_topic" in client.channels

@pytest.mark.integration
def test_realtime_connection():
    # Replace the localhost URL with your Supabase WebSocket URL
    url = "wss://ntksfsyitevnjxgandjs.supabase.co/realtime/v1/websocket?apikey=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im50a3Nmc3lpdGV2bmp4Z2FuZGpzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTE3ODMxMjksImV4cCI6MjA2NzM1OTEyOX0.NwF9x2aTN5Vpe0rKgypRpqY2ZPTiavF_IO5vwhFlqH0"
    # Use your anon key from tests.env
    key = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im50a3Nmc3lpdGV2bmp4Z2FuZGpzIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NTE3ODMxMjksImV4cCI6MjA2NzM1OTEyOX0.NwF9x2aTN5Vpe0rKgypRpqY2ZPTiavF_IO5vwhFlqH0"
    client = RealtimeClient(url, key)
    
    client.connect()
    assert client._connected
    
    client.disconnect()
    assert not client._connected
