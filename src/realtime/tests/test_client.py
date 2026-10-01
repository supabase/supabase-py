import asyncio
from unittest.mock import AsyncMock

import pytest

from realtime import AsyncRealtimeClient


@pytest.mark.asyncio
async def test_remove_all_channels_concurrency():
    """
    Test that remove_all_channels does not crash with RuntimeError when
    channels are removed from the client dictionary asynchronously during
    unsubscription, and that channels are successfully removed.
    """
    client = AsyncRealtimeClient("ws://localhost:4000/socket", "anon-key")
    
    # Fake the socket connection
    class FakeConnection:
        def __init__(self):
            self.closed = False
            
        async def send(self, msg):
            pass
            
        async def close(self):
            self.closed = True
            
    fake_conn = FakeConnection()
    client._ws_connection = fake_conn

    # Fake channels
    class FakeChannel:
        def __init__(self, topic, client_ref):
            self.topic = topic
            self.client = client_ref
            
        async def unsubscribe(self):
            # Yield to event loop to simulate network latency
            await asyncio.sleep(0.01)
            # Simulate the background loop receiving the leave confirmation
            # and automatically closing the channel, removing it from dict.
            self.client._remove_channel(self)

    client.channels = {
        "room-1": FakeChannel("room-1", client),
        "room-2": FakeChannel("room-2", client),
        "room-3": FakeChannel("room-3", client),
    }

    # This will crash with RuntimeError: dictionary changed size during iteration
    # on the old implementation.
    await client.remove_all_channels()

    # Verify channels were removed correctly (also validating the memory leak fix)
    assert len(client.channels) == 0
    assert fake_conn.closed is True
    assert client._ws_connection is None


@pytest.mark.asyncio
async def test_remove_all_channels_unsubscribe_failure():
    """
    Test that if channel.unsubscribe() raises an exception, the teardown process
    still attempts to remove the remaining channels and successfully closes the socket,
    while propagating the first exception encountered.
    """
    client = AsyncRealtimeClient("ws://localhost:4000/socket", "anon-key")
    
    class FakeConnection:
        def __init__(self):
            self.closed = False
            
        async def close(self):
            self.closed = True
            
    fake_conn = FakeConnection()
    client._ws_connection = fake_conn

    class FailingChannel:
        def __init__(self, topic, client_ref, should_fail=False):
            self.topic = topic
            self.client = client_ref
            self.should_fail = should_fail
            
        async def unsubscribe(self):
            if self.should_fail:
                raise ConnectionError("Network dropped!")
            # Yield to event loop to simulate network latency
            await asyncio.sleep(0.01)

    client.channels = {
        "room-1": FailingChannel("room-1", client, should_fail=True),
        "room-2": FailingChannel("room-2", client, should_fail=False),
    }

    with pytest.raises(ConnectionError, match="Network dropped!"):
        await client.remove_all_channels()

    # Verify that the teardown continued despite the first failure
    assert len(client.channels) == 0
    assert fake_conn.closed is True
    assert client._ws_connection is None
