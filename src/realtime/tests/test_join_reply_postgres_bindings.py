import asyncio
import json
from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest
import pytest_asyncio

from realtime import AsyncRealtimeClient
from realtime._async.channel import AsyncRealtimeChannel
from realtime.message import ServerMessageAdapter
from realtime.types import RealtimePostgresChangesListenEvent, RealtimeSubscribeStates

URL = "ws://localhost/realtime/v1"
MISMATCH = "mismatch between server and client bindings for postgres changes"


class RecordingConnection:
    def __init__(self) -> None:
        self.sent: list[dict[str, Any]] = []
        self.close = AsyncMock()

    async def send(self, message: str) -> None:
        self.sent.append(json.loads(message))

    def __aiter__(self) -> "RecordingConnection":
        return self

    async def __anext__(self) -> str:
        await asyncio.Event().wait()
        raise StopAsyncIteration

    def events(self) -> list[str]:
        return [message["event"] for message in self.sent]


Statuses = list[tuple[RealtimeSubscribeStates, Exception | None]]


@pytest_asyncio.fixture
async def connection() -> AsyncIterator[RecordingConnection]:
    connection = RecordingConnection()
    with patch(
        "realtime._async.client.connect", new=AsyncMock(return_value=connection)
    ):
        yield connection


@pytest_asyncio.fixture
async def socket(
    connection: RecordingConnection,
) -> AsyncIterator[AsyncRealtimeClient]:
    socket = AsyncRealtimeClient(URL, "token", auto_reconnect=False)
    await socket.connect()
    yield socket
    await socket.close()


def noop(payload: Any) -> None:
    return None


async def subscribe(channel: AsyncRealtimeChannel, statuses: Statuses) -> None:
    await channel.subscribe(lambda status, error: statuses.append((status, error)))


def reply_to_join(
    channel: AsyncRealtimeChannel,
    connection: RecordingConnection,
    response: dict[str, Any],
) -> None:
    [join] = [message for message in connection.sent if message["event"] == "phx_join"]
    channel._handle_message(
        ServerMessageAdapter.validate_python(
            {
                "event": "phx_reply",
                "topic": channel.topic,
                "ref": join["ref"],
                "payload": {"status": "ok", "response": response},
            }
        )
    )


def server_binding(id: int, **fields: Any) -> dict[str, Any]:
    return {"id": id, "event": "*", "schema": "public", **fields}


async def let_background_tasks_run() -> None:
    for _ in range(5):
        await asyncio.sleep(0)


@pytest.mark.asyncio
async def test_matching_bindings_receive_server_ids(
    socket: AsyncRealtimeClient, connection: RecordingConnection
) -> None:
    channel = socket.channel("join-reply")
    channel.on_postgres_changes(
        RealtimePostgresChangesListenEvent.All, noop, table="todos"
    )
    channel.on_postgres_changes(
        RealtimePostgresChangesListenEvent.Insert,
        noop,
        table="notes",
        filter="id=eq.1",
    )
    statuses: Statuses = []
    await subscribe(channel, statuses)

    reply_to_join(
        channel,
        connection,
        {
            "postgres_changes": [
                server_binding(11, table="todos"),
                {
                    "id": 22,
                    "event": "INSERT",
                    "schema": "public",
                    "table": "notes",
                    "filter": "id=eq.1",
                },
            ]
        },
    )

    assert statuses == [(RealtimeSubscribeStates.SUBSCRIBED, None)]
    assert [c.id for c in channel.postgres_changes_callbacks] == [11, 22]
    assert channel.is_joined


@pytest.mark.asyncio
async def test_reply_without_postgres_changes_keeps_bindings(
    socket: AsyncRealtimeClient, connection: RecordingConnection
) -> None:
    channel = socket.channel("join-reply")
    channel.on_postgres_changes(
        RealtimePostgresChangesListenEvent.All, noop, table="todos"
    )
    bindings = list(channel.postgres_changes_callbacks)
    statuses: Statuses = []
    await subscribe(channel, statuses)

    reply_to_join(channel, connection, {})
    await let_background_tasks_run()

    assert statuses == [(RealtimeSubscribeStates.SUBSCRIBED, None)]
    assert channel.postgres_changes_callbacks == bindings
    assert channel.is_joined
    assert "phx_leave" not in connection.events()


@pytest.mark.asyncio
async def test_empty_server_bindings_with_client_bindings_report_channel_error(
    socket: AsyncRealtimeClient, connection: RecordingConnection
) -> None:
    channel = socket.channel("join-reply")
    channel.on_postgres_changes(
        RealtimePostgresChangesListenEvent.All, noop, table="todos"
    )
    statuses: Statuses = []
    await subscribe(channel, statuses)

    reply_to_join(channel, connection, {"postgres_changes": []})

    assert channel.is_errored
    [(status, error)] = statuses
    assert status == RealtimeSubscribeStates.CHANNEL_ERROR
    assert str(error) == MISMATCH

    await let_background_tasks_run()
    assert connection.events()[-1] == "phx_leave"


@pytest.mark.asyncio
async def test_mismatched_filter_reports_channel_error(
    socket: AsyncRealtimeClient, connection: RecordingConnection
) -> None:
    channel = socket.channel("join-reply")
    channel.on_postgres_changes(
        RealtimePostgresChangesListenEvent.All,
        noop,
        table="todos",
        filter="id=eq.1",
    )
    statuses: Statuses = []
    await subscribe(channel, statuses)

    reply_to_join(
        channel,
        connection,
        {"postgres_changes": [server_binding(11, table="todos", filter="id=eq.2")]},
    )

    assert channel.is_errored
    [(status, error)] = statuses
    assert status == RealtimeSubscribeStates.CHANNEL_ERROR
    assert str(error) == MISMATCH

    await let_background_tasks_run()
    assert connection.events()[-1] == "phx_leave"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "server_fields",
    [{"table": "todos"}, {"table": "todos", "filter": None}],
    ids=["missing", "null"],
)
async def test_null_and_missing_filter_are_equal(
    socket: AsyncRealtimeClient,
    connection: RecordingConnection,
    server_fields: dict[str, Any],
) -> None:
    channel = socket.channel("join-reply")
    channel.on_postgres_changes(
        RealtimePostgresChangesListenEvent.All, noop, table="todos", filter=None
    )
    statuses: Statuses = []
    await subscribe(channel, statuses)

    reply_to_join(
        channel, connection, {"postgres_changes": [server_binding(11, **server_fields)]}
    )

    assert statuses == [(RealtimeSubscribeStates.SUBSCRIBED, None)]
    assert [c.id for c in channel.postgres_changes_callbacks] == [11]


@pytest.mark.asyncio
async def test_empty_server_bindings_without_client_bindings_subscribe(
    socket: AsyncRealtimeClient, connection: RecordingConnection
) -> None:
    channel = socket.channel("join-reply")
    statuses: Statuses = []
    await subscribe(channel, statuses)

    reply_to_join(channel, connection, {"postgres_changes": []})
    await let_background_tasks_run()

    assert statuses == [(RealtimeSubscribeStates.SUBSCRIBED, None)]
    assert channel.is_joined
    assert "phx_leave" not in connection.events()


@pytest.mark.asyncio
async def test_partial_mismatch_leaves_binding_ids_untouched(
    socket: AsyncRealtimeClient, connection: RecordingConnection
) -> None:
    channel = socket.channel("join-reply")
    channel.on_postgres_changes(
        RealtimePostgresChangesListenEvent.All, noop, table="todos"
    )
    channel.on_postgres_changes(
        RealtimePostgresChangesListenEvent.All, noop, table="notes"
    )
    statuses: Statuses = []
    await subscribe(channel, statuses)

    reply_to_join(
        channel,
        connection,
        {
            "postgres_changes": [
                server_binding(11, table="todos"),
                server_binding(22, table="other"),
            ]
        },
    )

    assert [status for status, _ in statuses] == [RealtimeSubscribeStates.CHANNEL_ERROR]
    assert [c.id for c in channel.postgres_changes_callbacks] == [None, None]
