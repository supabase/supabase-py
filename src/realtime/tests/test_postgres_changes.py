from typing import Any

import pytest

from realtime import AsyncRealtimeClient
from realtime.message import PostgresChangesMessage, ServerMessageAdapter
from realtime.types import PostgresChangesPayload, RealtimePostgresChangesListenEvent


def postgres_changes_message(
    event: RealtimePostgresChangesListenEvent, errors: Any
) -> dict[str, Any]:
    row_field = "old_record" if event == "DELETE" else "record"
    return {
        "event": "postgres_changes",
        "topic": "realtime:changes",
        "ref": None,
        "payload": {
            "ids": [1],
            "data": {
                "schema": "public",
                "table": "notes",
                "commit_timestamp": "2026-11-02T00:00:00Z",
                "type": event,
                "columns": [{"name": "id", "type": "int4"}],
                "errors": errors,
                row_field: {"id": 1},
            },
        },
    }


@pytest.mark.parametrize(
    "event",
    [
        RealtimePostgresChangesListenEvent.Insert,
        RealtimePostgresChangesListenEvent.Update,
        RealtimePostgresChangesListenEvent.Delete,
    ],
)
@pytest.mark.parametrize(
    "errors",
    [["Error 413: Payload Too Large"], [], "legacy-diagnostic", None],
)
def test_postgres_changes_preserves_errors(
    event: RealtimePostgresChangesListenEvent, errors: Any
) -> None:
    received: list[PostgresChangesPayload] = []
    channel = AsyncRealtimeClient("ws://localhost/realtime/v1").channel("changes")
    channel.on_postgres_changes(event, received.append, schema="public", table="notes")
    channel.postgres_changes_callbacks[0].id = 1

    message = ServerMessageAdapter.validate_python(
        postgres_changes_message(event, errors)
    )
    assert isinstance(message, PostgresChangesMessage)
    channel._handle_message(message)

    [payload] = received
    assert payload["data"]["errors"] == errors
    row_field = "old_record" if event == "DELETE" else "record"
    assert payload["data"].get(row_field) == {"id": 1}
