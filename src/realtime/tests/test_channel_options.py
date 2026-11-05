import dataclasses

import pytest

from realtime.channel import RealtimeChannelOptions
from realtime.types import PostgresChangesBinding, RealtimePostgresChangesListenEvent


def test_builders_return_new_options_and_keep_the_original() -> None:
    options = RealtimeChannelOptions()

    configured = (
        options.broadcast(ack=True)
        .presence(key="user", enabled=True)
        .private(True)
        .postgres_changes(RealtimePostgresChangesListenEvent.Insert, table="todos")
    )

    assert options == RealtimeChannelOptions()
    assert configured.broadcast_ack
    assert configured.presence_key == "user"
    assert configured.presence_enabled
    assert configured.is_private
    assert [binding.table for binding in configured.postgres_changes_bindings] == [
        "todos"
    ]


def test_postgres_changes_do_not_leak_between_copies() -> None:
    base = RealtimeChannelOptions().postgres_changes(
        RealtimePostgresChangesListenEvent.Insert, table="todos"
    )

    first = base.postgres_changes(RealtimePostgresChangesListenEvent.Update, table="a")
    second = base.postgres_changes(RealtimePostgresChangesListenEvent.Delete, table="b")

    assert [binding.table for binding in base.postgres_changes_bindings] == ["todos"]
    assert [binding.table for binding in first.postgres_changes_bindings] == [
        "todos",
        "a",
    ]
    assert [binding.table for binding in second.postgres_changes_bindings] == [
        "todos",
        "b",
    ]


def test_options_are_frozen() -> None:
    options = RealtimeChannelOptions()

    with pytest.raises(dataclasses.FrozenInstanceError):
        options.is_private = True  # pyrefly: ignore[read-only]


def test_given_sequences_are_copied() -> None:
    columns = ["id"]
    binding = PostgresChangesBinding(
        event=RealtimePostgresChangesListenEvent.Insert,
        table="todos",
        schema="public",
        filter=None,
        select=columns,
    )
    bindings = [binding]
    options = RealtimeChannelOptions(postgres_changes_bindings=bindings)

    columns.append("secret")
    bindings.append(binding)

    assert binding.select == ("id",)
    assert options.postgres_changes_bindings == (binding,)
