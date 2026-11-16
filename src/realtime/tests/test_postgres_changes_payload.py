from datetime import UTC, datetime, timedelta, timezone

import pytest
from pydantic import ValidationError
from supabase_utils.types import JSON

from realtime import (
    PostgresChangesColumn,
    PostgresChangesMessage,
    PostgresChangesPayload,
    RealtimePostgresChangesListenEvent,
)
from realtime.message import ServerMessageAdapter


def raw_message(data: JSON) -> dict[str, JSON]:
    return {
        "event": "postgres_changes",
        "topic": "realtime:room",
        "ref": None,
        "payload": {"ids": [3, 7], "data": data},
    }


def postgres_changes_message(*without: str, **fields: JSON) -> PostgresChangesMessage:
    data: dict[str, JSON] = {
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
        **fields,
    }
    for key in without:
        del data[key]
    message = ServerMessageAdapter.validate_python(raw_message(data))
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
    payload = postgres_changes_message("old_record", type="INSERT").payload

    assert payload.event == RealtimePostgresChangesListenEvent.Insert
    assert payload.record == {"id": 1, "title": "new"}
    assert payload.old_record is None


def test_a_delete_has_no_record() -> None:
    payload = postgres_changes_message("record", type="DELETE").payload

    assert payload.event == RealtimePostgresChangesListenEvent.Delete
    assert payload.record is None
    assert payload.old_record == {"id": 1}


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


@pytest.mark.parametrize(
    ("timestamp", "expected"),
    [
        (
            "2026-11-04 12:30:00.123+00",
            datetime(2026, 11, 4, 12, 30, 0, 123000, tzinfo=UTC),
        ),
        (
            "2026-11-04T14:30:00+02:00",
            datetime(2026, 11, 4, 14, 30, tzinfo=timezone(timedelta(hours=2))),
        ),
        ("2026-11-04T12:30:00", datetime(2026, 11, 4, 12, 30, tzinfo=UTC)),
    ],
    ids=["postgres-text", "offset", "naive-as-utc"],
)
def test_the_commit_timestamp_is_a_timezone_aware_datetime(
    timestamp: str, expected: datetime
) -> None:
    payload = postgres_changes_message(commit_timestamp=timestamp).payload

    assert payload.commit_timestamp == expected
    assert payload.commit_timestamp.tzinfo is not None


@pytest.mark.parametrize("data", [None, [], "change"], ids=["null", "list", "str"])
def test_a_payload_without_a_data_object_fails_validation(data: JSON) -> None:
    with pytest.raises(ValidationError):
        ServerMessageAdapter.validate_python(raw_message(data))


def test_the_payload_model_takes_only_the_flat_shape() -> None:
    envelope = raw_message(
        {
            "schema": "public",
            "table": "todos",
            "commit_timestamp": "2026-11-04T12:30:00Z",
            "type": "INSERT",
            "columns": [],
        }
    )["payload"]

    with pytest.raises(ValidationError):
        PostgresChangesPayload.model_validate(envelope)
