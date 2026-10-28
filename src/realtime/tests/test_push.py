import json
from unittest.mock import AsyncMock, Mock

import pytest

from realtime import AsyncRealtimeClient
from realtime._async.push import AsyncPush
from realtime.message import ReplyMessage, ReplyPostgresChanges
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


@pytest.mark.asyncio
async def test_receive_timeout_after_push_send_outlasts_deadline():
    socket = AsyncRealtimeClient("http://localhost:54321/realtime/v1", timeout=1)
    channel = socket.channel("positions")

    async def send(raw):
        message = json.loads(raw)
        if message["event"] == "phx_join":
            channel._handle_message(
                ReplyMessage.model_validate(
                    {
                        "event": "phx_reply",
                        "topic": message["topic"],
                        "ref": message["ref"],
                        "payload": {"status": "ok", "response": {}},
                    }
                )
            )
        else:
            push = channel.messages_waiting_for_ack[message["ref"]]
            assert push.timeout_task is not None
            await push.timeout_task

    websocket = AsyncMock()
    websocket.send.side_effect = send
    socket._ws_connection = websocket
    timed_out = []

    def on_timeout():
        timed_out.append(True)

    try:
        await channel.subscribe()
        push = await channel.push(
            "broadcast", {"event": "position", "payload": {"x": 1}}
        )
        push.receive(RealtimeAcknowledgementStatus.Timeout, on_timeout)

        assert timed_out == [True]
    finally:
        await socket.close()


def test_receive_after_ok_preserves_response():
    push = AsyncPush(Mock(), "broadcast")
    response = ReplyPostgresChanges(postgres_changes=[])
    push.trigger(RealtimeAcknowledgementStatus.Ok, response)
    callback = Mock()

    push.receive(RealtimeAcknowledgementStatus.Ok, callback)

    callback.assert_called_once_with(response)


def test_receive_after_error_preserves_response():
    push = AsyncPush(Mock(), "broadcast")
    response = {"reason": "permission denied"}
    push.trigger(RealtimeAcknowledgementStatus.Error, response)
    callback = Mock()

    push.receive(RealtimeAcknowledgementStatus.Error, callback)

    callback.assert_called_once_with(response)
