import logging
from collections.abc import AsyncIterator

import pytest
from websockets.asyncio.server import ServerConnection, serve
from websockets.exceptions import ConnectionClosed
from websockets.frames import Frame

from realtime._redact import RedactingLoggerAdapter, redact
from realtime.client import connect_once
from realtime.message import Message, ReplyMessage, SuccessReplyMessage
from realtime.types import ChannelEvents

HOST = "127.0.0.1"
URL_TOKEN = "url-secret-token"
REFRESHED_TOKEN = "refreshed-secret-token"


async def handler(connection: ServerConnection) -> None:
    try:
        async for raw in connection:
            message = Message.model_validate_json(raw)
            if message.ref is None or message.event == ChannelEvents.access_token:
                continue
            reply = ReplyMessage.model_validate(
                {
                    "event": ChannelEvents.reply,
                    "topic": message.topic,
                    "ref": message.ref,
                    "payload": SuccessReplyMessage.model_validate(
                        {"status": "ok", "response": {}}
                    ),
                }
            )
            await connection.send(reply.model_dump_json())
    except ConnectionClosed:
        pass


@pytest.fixture
async def server_url() -> AsyncIterator[str]:
    async with serve(handler, HOST, 0) as server:
        port = next(iter(server.sockets)).getsockname()[1]
        yield f"http://{HOST}:{port}"


@pytest.mark.parametrize("max_log_size", [Frame.MAX_LOG_SIZE, 10_000])
async def test_tokens_are_not_logged(
    server_url: str,
    caplog: pytest.LogCaptureFixture,
    monkeypatch: pytest.MonkeyPatch,
    max_log_size: int,
) -> None:
    monkeypatch.setattr(Frame, "MAX_LOG_SIZE", max_log_size)

    async def get_token() -> str:
        return URL_TOKEN

    with caplog.at_level(logging.DEBUG):
        async with connect_once(server_url, get_token) as client:
            await client.channel("first").subscribe()
            await client.set_auth(REFRESHED_TOKEN)
            await client.channel("second").subscribe()

    client_logs = "\n".join(
        record.getMessage()
        for record in caplog.records
        if not record.name.startswith("websockets.server")
    )
    assert "apikey=<redacted>" in client_logs
    assert '"event":"access_token"' in client_logs
    assert '"event":"phx_join"' in client_logs
    assert URL_TOKEN not in client_logs
    assert REFRESHED_TOKEN not in client_logs
    assert {
        record.filename
        for record in caplog.records
        if record.name in {"realtime.client", "websockets.client"}
    }.isdisjoint({"_redact.py", "__init__.py"})


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        (
            "/websocket?vsn=2.0.0&apikey=secret",
            "/websocket?vsn=2.0.0&apikey=<redacted>",
        ),
        (
            "/websocket?apikey=secret&vsn=2.0.0",
            "/websocket?apikey=<redacted>&vsn=2.0.0",
        ),
        (
            '{"payload":{"access_token":"secret"},"topic":"realtime:room"}',
            '{"payload":{"access_token":"<redacted>"},"topic":"realtime:room"}',
        ),
        (
            '{"payload":{"access_token": "secret"}}',
            '{"payload":{"access_token": "<redacted>"}}',
        ),
        (
            "/websocket?APIKey=secret",
            "/websocket?APIKey=<redacted>",
        ),
        (
            "{'access_token': 'secret'}",
            "{'access_token': '<redacted>'}",
        ),
        (
            "RealtimeChannelOptionsPayload(access_token='secret')",
            "RealtimeChannelOptionsPayload(access_token='<redacted>')",
        ),
        (
            '{"event":"access_token","payload":{}}',
            '{"event":"access_token","payload":{}}',
        ),
        ("x_apikey=public", "x_apikey=public"),
        ("no secrets here", "no secrets here"),
    ],
)
def test_redact(text: str, expected: str) -> None:
    assert redact(text) == expected


def test_adapter_redacts_arguments_that_are_not_strings(
    caplog: pytest.LogCaptureFixture,
) -> None:
    logger = RedactingLoggerAdapter(logging.getLogger("realtime.test"))
    raw = b'{"payload":{"access_token":"secret"}}'

    with caplog.at_level(logging.ERROR, logger="realtime.test"):
        logger.error("Unrecognized message %r\n%s", raw, ValueError(raw.decode()))

    [record] = caplog.records
    assert "secret" not in record.getMessage()
    assert record.getMessage().count('"access_token":"<redacted>"') == 2
