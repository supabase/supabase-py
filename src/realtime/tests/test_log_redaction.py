import logging
from unittest.mock import AsyncMock, patch
from urllib.parse import parse_qs, urlparse

import pytest

from realtime import AsyncRealtimeClient
from realtime.message import Message
from realtime.types import ChannelEvents

SECRET = "secret-key&x=1#frag+"


@pytest.mark.asyncio
async def test_connect_does_not_log_apikey(caplog: pytest.LogCaptureFixture) -> None:
    client = AsyncRealtimeClient(
        "https://project.supabase.co/realtime/v1",
        SECRET,
        params={"log_level": "info"},
    )

    with (
        caplog.at_level(logging.DEBUG, logger="realtime"),
        patch("realtime._async.client.connect", new_callable=AsyncMock) as connect,
        patch.object(client, "_on_connect", new_callable=AsyncMock),
    ):
        await client.connect()

    assert "secret-key" not in caplog.text
    assert "apikey=REDACTED" in caplog.text
    assert "log_level=info" in caplog.text
    assert "project.supabase.co/realtime/v1/websocket" in caplog.text
    assert connect.await_args is not None
    query = parse_qs(urlparse(connect.await_args.args[0]).query)
    assert query["apikey"] == [SECRET]


@pytest.mark.asyncio
async def test_send_does_not_log_access_token(
    caplog: pytest.LogCaptureFixture,
) -> None:
    client = AsyncRealtimeClient("https://project.supabase.co/realtime/v1", "key")

    with caplog.at_level(logging.DEBUG, logger="realtime"):
        await client.send(
            Message(
                topic="realtime:room",
                event=ChannelEvents.join,
                payload={"config": {"private": True}, "access_token": SECRET},
                ref="1",
            )
        )

    assert SECRET not in caplog.text
    assert "realtime:room" in caplog.text
