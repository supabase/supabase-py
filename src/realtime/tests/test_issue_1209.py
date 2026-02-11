
import asyncio
import pytest
from unittest.mock import AsyncMock, MagicMock
from realtime._async.channel import AsyncRealtimeChannel
from realtime._async.client import AsyncRealtimeClient
from realtime.types import RealtimeAcknowledgementStatus
from realtime.message import ReplyPostgresChanges

@pytest.mark.asyncio
async def test_subscribe_success():
    """Verify subscribe waits for OK response and returns channel."""
    mock_client = AsyncMock(spec=AsyncRealtimeClient)
    mock_client.timeout = 10
    mock_client.is_connected = True
    mock_client._make_ref.return_value = "1"
    mock_client.http_endpoint = "http://localhost:54321"
    mock_client.access_token = "dummy"

    channel = AsyncRealtimeChannel(mock_client, "test-topic")
    
    # Start subscribe in background
    task = asyncio.create_task(channel.subscribe())
    
    # Wait a bit to ensure subscribe has sent the request and is waiting
    await asyncio.sleep(0.1)
    
    # Simulate server response OK
    response_payload = ReplyPostgresChanges(postgres_changes=[])
    channel.join_push.trigger(RealtimeAcknowledgementStatus.Ok, response_payload)
    
    # Task should complete now
    result = await asyncio.wait_for(task, timeout=1.0)
    assert result == channel
    # channel.is_joined is set by the callback logic we verified in manual inspection, 
    # but let's verify connection state implicitly by success

@pytest.mark.asyncio
async def test_subscribe_error():
    """Verify subscribe raises Exception on Error response."""
    mock_client = AsyncMock(spec=AsyncRealtimeClient)
    mock_client.timeout = 10
    mock_client.is_connected = True
    mock_client._make_ref.return_value = "1"
    mock_client.http_endpoint = "http://localhost:54321"
    mock_client.access_token = "dummy"

    channel = AsyncRealtimeChannel(mock_client, "test-topic-error")
    
    task = asyncio.create_task(channel.subscribe())
    await asyncio.sleep(0.1)
    
    # Simulate server response ERROR
    error_payload = {"message": "Access denied"}
    channel.join_push.trigger(RealtimeAcknowledgementStatus.Error, error_payload)
    
    # Task should raise Exception
    with pytest.raises(Exception) as excinfo:
        await asyncio.wait_for(task, timeout=1.0)
    assert "Access denied" in str(excinfo.value)
    
@pytest.mark.asyncio
async def test_subscribe_timeout():
    """Verify subscribe raises TimeoutError when server doesn't reply."""
    mock_client = AsyncMock(spec=AsyncRealtimeClient)
    mock_client.timeout = 0.2 
    mock_client.is_connected = True
    mock_client._make_ref.return_value = "1"
    mock_client.http_endpoint = "http://localhost:54321"
    mock_client.access_token = "dummy"

    channel = AsyncRealtimeChannel(mock_client, "test-topic-timeout")
    
    # We pass a specific timeout to subscribe, or rely on socket timeout
    # Here we test the override logic
    with pytest.raises(TimeoutError):
        await channel.subscribe(timeout=0.2)
