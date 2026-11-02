import asyncio
import json

import pytest
from websockets.asyncio.server import ServerConnection, serve

from realtime import AsyncRealtimeClient
from realtime.types import PostgresChangesPayload, RealtimePostgresChangesListenEvent


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "event",
    [
        RealtimePostgresChangesListenEvent.Insert,
        RealtimePostgresChangesListenEvent.Update,
        RealtimePostgresChangesListenEvent.Delete,
    ],
)
async def test_postgres_changes_preserves_errors(
    event: RealtimePostgresChangesListenEvent,
) -> None:
    processed = asyncio.Event()
    received: list[PostgresChangesPayload] = []

    def on_change(payload: PostgresChangesPayload) -> None:
        received.append(payload)
        if payload["data"]["errors"] is None:
            processed.set()

    async def handler(connection: ServerConnection) -> None:
        async for raw in connection:
            message = json.loads(raw)
            if message["event"] != "phx_join":
                continue

            await connection.send(
                json.dumps(
                    {
                        "event": "phx_reply",
                        "topic": message["topic"],
                        "ref": message["ref"],
                        "payload": {
                            "status": "ok",
                            "response": {
                                "postgres_changes": [
                                    {
                                        "id": 1,
                                        "event": event,
                                        "schema": "public",
                                        "table": "notes",
                                    }
                                ]
                            },
                        },
                    }
                )
            )
            for errors in (
                ["Error 413: Payload Too Large"],
                [],
                "legacy-diagnostic",
                None,
            ):
                data: dict[str, object] = {
                    "schema": "public",
                    "table": "notes",
                    "commit_timestamp": "2026-11-02T00:00:00Z",
                    "type": event,
                    "columns": [{"name": "id", "type": "int4"}],
                    "errors": errors,
                }
                row_field = "old_record" if event == "DELETE" else "record"
                data[row_field] = {"id": 1}
                await connection.send(
                    json.dumps(
                        {
                            "event": "postgres_changes",
                            "topic": message["topic"],
                            "ref": None,
                            "payload": {"ids": [1], "data": data},
                        }
                    )
                )

    async with serve(handler, "127.0.0.1", 0) as server:
        port = next(iter(server.sockets)).getsockname()[1]
        client = AsyncRealtimeClient(
            f"ws://127.0.0.1:{port}/realtime/v1", auto_reconnect=False
        )
        channel = client.channel("changes").on_postgres_changes(
            event, on_change, schema="public", table="notes"
        )
        try:
            await channel.subscribe()
            await asyncio.wait_for(processed.wait(), 2)

            assert [payload["data"]["errors"] for payload in received] == [
                ["Error 413: Payload Too Large"],
                [],
                "legacy-diagnostic",
                None,
            ]
            row_field = "old_record" if event == "DELETE" else "record"
            assert [payload["data"].get(row_field) for payload in received] == [
                {"id": 1}
            ] * 4
        finally:
            tasks = [
                task
                for task in (
                    channel.rejoin_timer.timer,
                    channel.join_push.timeout_task,
                    client._listen_task,
                    client._heartbeat_task,
                )
                if task is not None
            ]
            channel.rejoin_timer.reset()
            channel.join_push.destroy()
            await client.close()
            await asyncio.gather(*tasks, return_exceptions=True)
