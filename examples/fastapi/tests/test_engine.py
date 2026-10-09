# examples/fastapi/tests/test_engine.py
from unittest.mock import AsyncMock, MagicMock

import pytest


def _make_service_client(rules_data=None, events_insert_data=None):
    """Build a mock service_client for engine tests."""
    client = AsyncMock()

    rules_chain = MagicMock()
    rules_chain.execute = AsyncMock(return_value=MagicMock(data=rules_data or []))
    rules_chain.select.return_value = rules_chain
    rules_chain.insert.return_value = rules_chain
    rules_chain.eq.return_value = rules_chain

    events_chain = MagicMock()
    events_chain.execute = AsyncMock(
        return_value=MagicMock(data=events_insert_data or [{}])
    )
    events_chain.insert.return_value = events_chain

    def table_side_effect(name):
        if name == "rules":
            return rules_chain
        return events_chain

    client.table = MagicMock(side_effect=table_side_effect)

    broadcast_channel = AsyncMock()
    broadcast_channel.subscribe = AsyncMock()
    broadcast_channel.send = AsyncMock()
    client.channel = MagicMock(return_value=broadcast_channel)

    return client, broadcast_channel


def _payload(record, old_record=None):
    """Build a supabase-py Realtime Postgres Changes payload."""
    return {"data": {"record": record, "old_record": old_record or {}}}


@pytest.mark.asyncio
async def test_no_matching_rules_does_not_broadcast():
    """When no rules match the new status, channel.send is not called."""
    client, broadcast_channel = _make_service_client(
        rules_data=[
            {
                "id": "r1",
                "watch_column": "status",
                "watch_value": "in_progress",
                "broadcast_channel": "ch1",
                "label": "In progress alert",
            }
        ]
    )

    from engine import on_task_change

    await on_task_change(client, _payload({"id": "task-1", "status": "done"}))

    broadcast_channel.send.assert_not_called()


@pytest.mark.asyncio
async def test_matching_rule_inserts_event_and_broadcasts():
    """When a rule matches, a rule_event is inserted and broadcast is sent."""
    client, broadcast_channel = _make_service_client(
        rules_data=[
            {
                "id": "r1",
                "watch_column": "status",
                "watch_value": "done",
                "broadcast_channel": "team-alerts",
                "label": "Done alert",
            }
        ]
    )

    from engine import on_task_change

    await on_task_change(
        client,
        _payload({"id": "task-1", "status": "done"}, {"status": "in_progress"}),
    )

    # Must insert a rule_event row
    client.table("rule_events").insert.assert_called_once()
    insert_args = client.table("rule_events").insert.call_args[0][0]
    assert insert_args["rule_id"] == "r1"
    assert insert_args["task_id"] == "task-1"

    # Must broadcast to the configured channel
    broadcast_channel.send.assert_called_once()
    send_kwargs = broadcast_channel.send.call_args[1]
    assert send_kwargs["event"] == "rule_fired"
    assert send_kwargs["payload"]["rule"]["id"] == "r1"


@pytest.mark.asyncio
async def test_rule_with_non_status_column_fires():
    """Rules watching columns other than 'status' should also fire."""
    client, broadcast_channel = _make_service_client(
        rules_data=[
            {
                "id": "r2",
                "watch_column": "title",
                "watch_value": "urgent",
                "broadcast_channel": "alerts",
                "label": "Urgent title alert",
            }
        ]
    )

    from engine import on_task_change

    await on_task_change(
        client,
        _payload({"id": "task-2", "title": "urgent", "status": "pending"}),
    )

    broadcast_channel.send.assert_called_once()


@pytest.mark.asyncio
async def test_empty_new_record_is_ignored():
    """Payloads without a record (e.g. missing data key) are silently ignored."""
    client, broadcast_channel = _make_service_client(
        rules_data=[
            {
                "id": "r1",
                "watch_column": "status",
                "watch_value": "done",
                "broadcast_channel": "ch1",
                "label": "Done",
            }
        ]
    )

    from engine import on_task_change

    await on_task_change(client, {"data": {"record": {}}})
    broadcast_channel.send.assert_not_called()
