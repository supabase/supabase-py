import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import AsyncMock

import pytest

from realtime import AsyncRealtimeClient
from realtime.types import BroadcastPayload


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "data",
    [
        [{"user_id": "alice", "x": 10, "y": 20}],
        "hello",
        42,
        1.5,
        False,
        None,
        [],
        {"user_id": "alice", "x": 10, "y": 20},
    ],
    ids=[
        "array",
        "string",
        "integer",
        "float",
        "boolean",
        "null",
        "empty-array",
        "object",
    ],
)
async def test_broadcast_json_payload_round_trip(
    monkeypatch: pytest.MonkeyPatch, data: Any
):
    received: list[BroadcastPayload] = []
    ready = asyncio.Event()
    exhausted = asyncio.Event()
    websocket = AsyncMock()
    client = AsyncRealtimeClient("https://example.com/realtime/v1")
    channel = client.channel(
        "positions",
        {
            "config": {
                "broadcast": {"self": True, "ack": True},
                "presence": {"key": "", "enabled": False},
                "private": False,
            }
        },
    )

    async def server_messages() -> AsyncIterator[str]:
        await ready.wait()
        for call in websocket.send.call_args_list:
            message = json.loads(call.args[0])
            if message["topic"] != channel.topic:
                continue
            yield json.dumps(
                {
                    "topic": channel.topic,
                    "event": "phx_reply",
                    "ref": message["ref"],
                    "payload": {"status": "ok", "response": {}},
                }
            )
            if message["event"] == "broadcast":
                yield json.dumps(
                    {
                        "topic": channel.topic,
                        "event": "broadcast",
                        "ref": None,
                        "payload": message["payload"],
                    }
                )
        exhausted.set()

    websocket.__aiter__.side_effect = server_messages
    monkeypatch.setattr(
        "realtime._async.client.connect", AsyncMock(return_value=websocket)
    )

    try:
        await channel.on_broadcast("positions", received.append).subscribe()
        await channel.send_broadcast("positions", data)
        await channel.send_broadcast("other-event", data)
        ready.set()
        await asyncio.wait_for(exhausted.wait(), timeout=1)
        assert [message["payload"] for message in received] == [data]
        assert type(received[0]["payload"]) is type(data)
    finally:
        await client.close()
