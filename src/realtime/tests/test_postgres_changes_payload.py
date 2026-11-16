from datetime import UTC, datetime

import pytest
from supabase_utils.types import JSON

from realtime import (
    PostgresChangesColumn,
    PostgresChangesMessage,
    PostgresChangesPayload,
    RealtimePostgresChangesListenEvent,
)
from realtime.message import ServerMessageAdapter


def postgres_changes_message(**data: JSON) -> PostgresChangesMessage:
    message = ServerMessageAdapter.validate_python(
        {
            "event": "postgres_changes",
            "topic": "realtime:room",
            "ref": None,
            "payload": {
                "ids": [3, 7],
                "data": {
                    "schema": "public",
                    "table": "todos",
                    "commit_timestamp": "2026-11-04T12:30:00.123Z",
                    "type": "UPDATE",
                    "errors": None,
                    "columns": [
                        {"name": "id", "type": "int8"},
                        {"name": "title", "type": "text"},
                    ],
                    "record": {"id": 1, "title": "new"},
                    "old_record": {"id": 1},
                    **data,
                },
            },
        }
    )
    assert isinstance(message, PostgresChangesMessage)
    return message


def test_the_change_is_read_into_one_flat_payload() -> None:
    assert postgres_changes_message().payload == PostgresChangesPayload(
        event=RealtimePostgresChangesListenEvent.Update,
        schema_="public",
        table="todos",
        commit_timestamp=datetime(2026, 11, 4, 12, 30, 0, 123000, tzinfo=UTC),
        columns=[
            PostgresChangesColumn(name="id", type="int8"),
            PostgresChangesColumn(name="title", type="text"),
        ],
        record={"id": 1, "title": "new"},
        old_record={"id": 1},
        errors=[],
        ids=[3, 7],
    )


def test_an_insert_has_no_old_record() -> None:
    payload = postgres_changes_message(type="INSERT", old_record=None).payload

    assert payload.event == RealtimePostgresChangesListenEvent.Insert
    assert payload.record == {"id": 1, "title": "new"}
    assert payload.old_record is None


def test_a_delete_has_no_record() -> None:
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
                    "commit_timestamp": "2026-11-04T12:30:00Z",
                    "type": "DELETE",
                    "errors": None,
                    "columns": [{"name": "id", "type": "int8"}],
                    "old_record": {"id": 1},
                },
            },
        }
    )
    assert isinstance(message, PostgresChangesMessage)

    assert message.payload.event == RealtimePostgresChangesListenEvent.Delete
    assert message.payload.record is None
    assert message.payload.old_record == {"id": 1}


@pytest.mark.parametrize(
    ("errors", "expected"),
    [
        ("Error 413: Payload Too Large", ["Error 413: Payload Too Large"]),
        (["Error 413: Payload Too Large"], ["Error 413: Payload Too Large"]),
        (None, []),
    ],
    ids=["string", "list", "null"],
)
def test_errors_are_always_a_list(errors: JSON, expected: list[str]) -> None:
    assert postgres_changes_message(errors=errors).payload.errors == expected
