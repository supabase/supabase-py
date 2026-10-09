"""
E2E tests for the /rules endpoints against a real Supabase instance with RLS enforced.

RLS policy summary (from 001_initial.sql):
  - Users may only SELECT, INSERT, and DELETE their own rules (user_id = auth.uid()).
"""

import pytest


async def test_list_rules_empty_for_new_user(client_a):
    r = await client_a.get("/rules/")
    assert r.status_code == 200
    assert r.json() == []


async def test_create_rule(client_a):
    r = await client_a.post(
        "/rules/",
        json={
            "label": "Done alert",
            "watch_column": "status",
            "watch_value": "done",
            "broadcast_channel": "team-alerts",
        },
    )
    assert r.status_code == 200
    rule = r.json()
    assert rule["label"] == "Done alert"
    assert rule["watch_column"] == "status"
    assert rule["watch_value"] == "done"
    assert rule["broadcast_channel"] == "team-alerts"


async def test_list_rules_returns_own_rules(client_a):
    await client_a.post(
        "/rules/",
        json={
            "label": "Listed rule",
            "watch_column": "status",
            "watch_value": "in_progress",
            "broadcast_channel": "ops-channel",
        },
    )
    r = await client_a.get("/rules/")
    assert r.status_code == 200
    labels = [rule["label"] for rule in r.json()]
    assert "Listed rule" in labels


async def test_delete_rule(client_a):
    create_r = await client_a.post(
        "/rules/",
        json={
            "label": "To delete",
            "watch_column": "status",
            "watch_value": "done",
            "broadcast_channel": "delete-test",
        },
    )
    rule_id = create_r.json()["id"]

    r = await client_a.delete(f"/rules/{rule_id}")
    assert r.status_code == 200
    assert r.json()["deleted"] == rule_id

    # Verify it's gone
    list_r = await client_a.get("/rules/")
    ids = [rule["id"] for rule in list_r.json()]
    assert rule_id not in ids


async def test_rls_user_b_cannot_see_user_a_rules(client_a, client_b):
    """RLS: user B gets an empty list — user A's rules are invisible."""
    await client_a.post(
        "/rules/",
        json={
            "label": "User A private rule",
            "watch_column": "status",
            "watch_value": "done",
            "broadcast_channel": "private-channel",
        },
    )

    r = await client_b.get("/rules/")
    assert r.status_code == 200
    assert r.json() == []


async def test_rls_user_b_cannot_delete_user_a_rule(client_a, client_b):
    """RLS: user B cannot delete user A's rule (returns 404)."""
    create_r = await client_a.post(
        "/rules/",
        json={
            "label": "Protected rule",
            "watch_column": "status",
            "watch_value": "done",
            "broadcast_channel": "protected",
        },
    )
    rule_id = create_r.json()["id"]

    r = await client_b.delete(f"/rules/{rule_id}")
    assert r.status_code == 404
