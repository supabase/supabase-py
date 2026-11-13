from collections.abc import AsyncIterator

import pytest
from supabase_utils.types import JSON
from websockets.asyncio.server import Server, ServerConnection, serve

from realtime._serializer import decode, encode
from realtime.channel import RealtimeChannelOptions
from realtime.client import connect_once
from realtime.exceptions import RealtimeError
from realtime.message import Message, PostgresChangesMessage, ServerMessageAdapter
from realtime.types import ChannelEvents, RealtimePostgresChangesListenEvent

HOST = "127.0.0.1"
MISMATCH = "mismatch between server and client bindings for postgres changes"


async def get_token() -> str:
    return "my-publishable-key"


class JoinReplyServer:
    """A local websocket server that acks every ref'd message and replies to
    joins with the configured `postgres_changes` response."""

    def __init__(self, postgres_changes: JSON) -> None:
        self.postgres_changes = postgres_changes
        self.ws_server: Server | None = None
        self.url = ""
        self.received: list[Message] = []

    async def __aenter__(self) -> "JoinReplyServer":
        self.ws_server = await serve(self.handler, HOST, 0)
        port = next(iter(self.ws_server.sockets)).getsockname()[1]
        self.url = f"http://{HOST}:{port}"
        await self.ws_server.start_serving()
        return self

    async def __aexit__(self, *exc: object) -> None:
        assert self.ws_server is not None
        self.ws_server.close()
        await self.ws_server.wait_closed()

    async def handler(self, connection: ServerConnection) -> None:
        async for frame in connection:
            message = decode(frame)
            self.received.append(message)
            if message.ref is None:
                continue
            response: dict[str, JSON] = {}
            if message.event == ChannelEvents.join:
                response = {"postgres_changes": self.postgres_changes}
            await connection.send(
                encode(
                    Message(
                        event=ChannelEvents.reply,
                        topic=message.topic,
                        ref=message.ref,
                        payload={"status": "ok", "response": response},
                    )
                )
            )

    def events(self) -> list[str]:
        return [
            message.event
            for message in self.received
            if message.event != ChannelEvents.heartbeat
        ]


@pytest.fixture
async def server(request: pytest.FixtureRequest) -> AsyncIterator[JoinReplyServer]:
    async with JoinReplyServer(request.param) as server:
        yield server


def server_binding(id: int, **fields: JSON) -> dict[str, JSON]:
    return {"id": id, "event": "*", "schema": "public", **fields}


def test_postgres_changes_schema_defaults_to_public() -> None:
    options = (
        RealtimeChannelOptions()
        .postgres_changes(RealtimePostgresChangesListenEvent.All)
        .postgres_changes(
            RealtimePostgresChangesListenEvent.Insert, table="todos", filter="id=eq.1"
        )
    )

    payload = options.to_payload().model_dump(mode="json", exclude_none=True)

    assert payload["config"]["postgres_changes"] == [
        {"event": "*", "schema": "public"},
        {
            "event": "INSERT",
            "schema": "public",
            "table": "todos",
            "filter": "id=eq.1",
        },
    ]


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "server",
    [
        [
            server_binding(11, table="todos"),
            {
                "id": 22,
                "event": "INSERT",
                "schema": "public",
                "table": "notes",
                "filter": "id=eq.1",
            },
        ]
    ],
    indirect=True,
)
async def test_matching_bindings_subscribe(server: JoinReplyServer) -> None:
    options = (
        RealtimeChannelOptions()
        .postgres_changes(RealtimePostgresChangesListenEvent.All, table="todos")
        .postgres_changes(
            RealtimePostgresChangesListenEvent.Insert, table="notes", filter="id=eq.1"
        )
    )
    async with (
        connect_once(server.url, get_token) as client,
        client.channel("room", options) as channel,
    ):
        assert channel.joined

    assert "phx_leave" in server.events()


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "server",
    [
        [server_binding(11, table="todos")],
        [server_binding(11, table="todos", filter=None)],
    ],
    ids=["missing", "null"],
    indirect=True,
)
async def test_missing_and_null_filter_match_no_filter(
    server: JoinReplyServer,
) -> None:
    options = RealtimeChannelOptions().postgres_changes(
        RealtimePostgresChangesListenEvent.All, table="todos"
    )
    async with (
        connect_once(server.url, get_token) as client,
        client.channel("room", options) as channel,
    ):
        assert channel.joined


@pytest.mark.asyncio
@pytest.mark.parametrize("server", [[]], indirect=True)
async def test_empty_reply_without_client_bindings_subscribes(
    server: JoinReplyServer,
) -> None:
    async with (
        connect_once(server.url, get_token) as client,
        client.channel("room") as channel,
    ):
        assert channel.joined


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "server",
    [
        [],
        [server_binding(11, table="todos", filter="id=eq.2")],
        [server_binding(11, table="other", filter="id=eq.1")],
        [server_binding(11, schema="private", table="todos", filter="id=eq.1")],
        [{**server_binding(11, table="todos", filter="id=eq.1"), "event": "INSERT"}],
    ],
    ids=["empty", "filter", "table", "schema", "event"],
    indirect=True,
)
async def test_mismatched_reply_leaves_and_raises(server: JoinReplyServer) -> None:
    options = RealtimeChannelOptions().postgres_changes(
        RealtimePostgresChangesListenEvent.All, table="todos", filter="id=eq.1"
    )
    async with connect_once(server.url, get_token) as client:
        channel = client.channel("room", options)

        with pytest.raises(RealtimeError, match=MISMATCH):
            await channel.subscribe()

        assert not channel.joined
        assert client.get_channels() == []

    assert server.events() == ["phx_join", "phx_leave"]


def postgres_changes_message(errors: JSON) -> PostgresChangesMessage:
    message = ServerMessageAdapter.validate_python(
        {
            "event": "postgres_changes",
            "topic": "realtime:room",
            "ref": None,
            "payload": {
                "ids": [1],
                "data": {
                    "schema": "public",
                    "table": "todos",
                    "commit_timestamp": "2026-11-04T00:00:00Z",
                    "type": "INSERT",
                    "errors": errors,
                    "columns": [{"name": "id", "type": "int8"}],
                },
            },
        }
    )
    assert isinstance(message, PostgresChangesMessage)
    return message


@pytest.mark.parametrize(
    "errors",
    ["Error 413: Payload Too Large", ["Error 413: Payload Too Large"], None],
    ids=["string", "list", "null"],
)
def test_postgres_changes_errors_accept_a_string_a_list_or_null(
    errors: JSON,
) -> None:
    assert postgres_changes_message(errors).payload.data.errors == errors
