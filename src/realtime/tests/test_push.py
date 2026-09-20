from unittest.mock import AsyncMock, Mock

import pytest

from realtime._async.push import AsyncPush
from realtime.types import RealtimeAcknowledgementStatus


@pytest.mark.asyncio
async def test_resend_starts_a_new_timeout():
    channel = Mock()
    channel.topic = "realtime:test"
    channel.join_push.ref = "join-ref"
    channel.messages_waiting_for_ack = {}
    channel.socket._make_ref.side_effect = ["1", "2"]
    channel.socket.send = AsyncMock()

    timeout_count = 0

    def on_timeout():
        nonlocal timeout_count
        timeout_count += 1

    push = AsyncPush(channel, "broadcast", timeout=0)
    push.receive(RealtimeAcknowledgementStatus.Timeout, on_timeout)

    await push.send()
    first_timeout = push.timeout_task
    assert first_timeout is not None
    await first_timeout

    await push.resend()
    second_timeout = push.timeout_task
    assert second_timeout is not None
    await second_timeout

    assert timeout_count == 2
