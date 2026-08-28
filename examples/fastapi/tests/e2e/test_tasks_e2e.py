"""
E2E tests for the /tasks endpoints against a real Supabase instance with RLS enforced.

RLS policy summary (from 001_initial.sql):
  - Any authenticated user may SELECT all tasks.
  - Only the user whose id matches assigned_to may UPDATE a task.
"""

import pytest


async def test_list_tasks_returns_200_for_authenticated_user(client_a):
    """Authenticated user can list tasks (RLS SELECT policy: all users see all tasks)."""
    r = await client_a.get("/tasks/")
    assert r.status_code == 200
    assert isinstance(r.json(), list)


async def test_create_task(client_a, user_a):
    r = await client_a.post(
        "/tasks/",
        json={"title": "E2E task", "assigned_to": user_a["user_id"]},
    )
    assert r.status_code == 200
    task = r.json()
    assert task["title"] == "E2E task"
    assert task["status"] == "pending"
    assert task["assigned_to"] == user_a["user_id"]


async def test_list_tasks_returns_created_task(client_a, user_a):
    await client_a.post(
        "/tasks/",
        json={"title": "Listed task", "assigned_to": user_a["user_id"]},
    )
    r = await client_a.get("/tasks/")
    assert r.status_code == 200
    titles = [t["title"] for t in r.json()]
    assert "Listed task" in titles


async def test_update_task_status(client_a, user_a):
    create_r = await client_a.post(
        "/tasks/",
        json={"title": "Status task", "assigned_to": user_a["user_id"]},
    )
    task_id = create_r.json()["id"]

    r = await client_a.patch(f"/tasks/{task_id}", json={"status": "in_progress"})
    assert r.status_code == 200
    assert r.json()["status"] == "in_progress"


async def test_update_task_invalid_status_returns_400(client_a, user_a):
    create_r = await client_a.post(
        "/tasks/",
        json={"title": "Bad status task", "assigned_to": user_a["user_id"]},
    )
    task_id = create_r.json()["id"]

    r = await client_a.patch(f"/tasks/{task_id}", json={"status": "flying"})
    assert r.status_code == 400


async def test_rls_user_b_cannot_update_user_a_task(client_a, client_b, user_a):
    """RLS: user B cannot update a task assigned to user A."""
    create_r = await client_a.post(
        "/tasks/",
        json={"title": "User A task", "assigned_to": user_a["user_id"]},
    )
    task_id = create_r.json()["id"]

    r = await client_b.patch(f"/tasks/{task_id}", json={"status": "done"})
    # RLS UPDATE policy returns 0 rows → router returns 404
    assert r.status_code == 404


async def test_rls_user_b_can_read_user_a_tasks(client_a, client_b, user_a):
    """RLS: all authenticated users may read all tasks (SELECT policy)."""
    await client_a.post(
        "/tasks/",
        json={"title": "Readable by all", "assigned_to": user_a["user_id"]},
    )

    r = await client_b.get("/tasks/")
    assert r.status_code == 200
    titles = [t["title"] for t in r.json()]
    assert "Readable by all" in titles
