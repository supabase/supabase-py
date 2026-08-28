"""
E2E test for the Realtime engine.

Flow:
  1. Create a rule via the API (user A).
  2. Create a task assigned to user A.
  3. Update the task status to "done" — triggers a Postgres Changes event.
  4. The engine receives the event, evaluates the rule, and inserts a row
     into rule_events.
  5. This test polls rule_events (via the service-role client) and asserts
     the row appears within a deadline.

This exercises the full supabase-py Realtime path from Python:
  AsyncRealtimeClient → Postgres Changes → on_task_change() → INSERT + broadcast
"""

import asyncio
from typing import Optional

_POLL_INTERVAL = 0.5
_TIMEOUT = 30


async def _wait_for_rule_event(
    service_client, rule_id: str, task_id: str, timeout: float = _TIMEOUT
) -> Optional[dict]:
    deadline = asyncio.get_running_loop().time() + timeout
    while asyncio.get_running_loop().time() < deadline:
        result = (
            await service_client.table("rule_events")
            .select("*")
            .eq("rule_id", rule_id)
            .eq("task_id", task_id)
            .execute()
        )
        if result.data:
            return result.data[0]
        await asyncio.sleep(_POLL_INTERVAL)
    return None


async def test_engine_creates_rule_event_on_status_change(
    running_app, service_client, client_a, user_a
):
    """
    Updating a task status to a watched value causes the engine to write
    a rule_event row within the poll timeout.
    """
    rule_r = await client_a.post(
        "/rules/",
        json={
            "label": "E2E engine rule",
            "watch_column": "status",
            "watch_value": "done",
            "broadcast_channel": "e2e-engine-test",
        },
    )
    assert rule_r.status_code == 200
    rule_id = rule_r.json()["id"]

    task_r = await client_a.post(
        "/tasks/",
        json={"title": "Engine test task", "assigned_to": user_a["user_id"]},
    )
    assert task_r.status_code == 200
    task_id = task_r.json()["id"]

    # Trigger the Postgres Changes event by updating the status.
    patch_r = await client_a.patch(f"/tasks/{task_id}", json={"status": "done"})
    assert patch_r.status_code == 200

    event = await _wait_for_rule_event(service_client, rule_id, task_id)
    assert event is not None, (
        f"Engine did not write a rule_event for rule={rule_id}, task={task_id} "
        f"within {_TIMEOUT}s. Check that the Realtime engine started successfully "
        "and that the tasks table is part of the supabase_realtime publication."
    )
    assert event["rule_id"] == rule_id
    assert event["task_id"] == task_id
    assert event["payload"]["status"] == "done"


async def test_engine_ignores_non_matching_status(
    running_app, service_client, client_a, user_a
):
    """
    Updating a task to a status that no rule watches must NOT create a rule_event.
    """
    rule_r = await client_a.post(
        "/rules/",
        json={
            "label": "Done-only rule",
            "watch_column": "status",
            "watch_value": "done",
            "broadcast_channel": "done-channel",
        },
    )
    rule_id = rule_r.json()["id"]

    task_r = await client_a.post(
        "/tasks/",
        json={"title": "Non-matching task", "assigned_to": user_a["user_id"]},
    )
    task_id = task_r.json()["id"]

    # Update to "in_progress" — not watched.
    await client_a.patch(f"/tasks/{task_id}", json={"status": "in_progress"})

    # Wait one full poll cycle and verify no event appeared.
    await asyncio.sleep(_POLL_INTERVAL * 3)
    result = (
        await service_client.table("rule_events")
        .select("*")
        .eq("rule_id", rule_id)
        .eq("task_id", task_id)
        .execute()
    )
    assert result.data == [], (
        "Engine created an unexpected rule_event for a non-matching status update."
    )
