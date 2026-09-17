import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient


def _mock_chain(data):
    """Build a MagicMock representing a postgrest chain that returns data."""
    chain = MagicMock()
    chain.execute = AsyncMock(return_value=MagicMock(data=data))
    chain.eq.return_value = chain
    chain.select.return_value = chain
    chain.insert.return_value = chain
    chain.update.return_value = chain
    chain.delete.return_value = chain
    return chain


def _make_mock_service_client():
    mock = AsyncMock()
    mock.realtime = AsyncMock()
    mock.realtime.connect = AsyncMock()
    mock.realtime.close = AsyncMock()
    ch = AsyncMock()
    ch.subscribe = AsyncMock()
    mock.channel.return_value = ch
    return mock


@pytest.fixture
def app_with_user_client():
    mock_sc = _make_mock_service_client()
    mock_uc = AsyncMock()
    # table() is synchronous on the real AsyncClient — use MagicMock so the
    # postgrest chain mock returned by _mock_chain() is accessible directly.
    mock_uc.table = MagicMock()

    with patch("main.acreate_client", AsyncMock(return_value=mock_sc)), \
         patch("main.start_engine", AsyncMock()):
        from main import app
        from dependencies import get_client

        async def override():
            return mock_uc

        app.dependency_overrides[get_client] = override
        with TestClient(app) as tc:
            yield tc, mock_uc
        app.dependency_overrides.clear()


TASK = {"id": "t1", "title": "Fix bug", "status": "pending",
        "assigned_to": "u1", "created_by": "u1", "created_at": "2024-01-01T00:00:00Z"}


def test_list_tasks_empty(app_with_user_client):
    tc, mock_uc = app_with_user_client
    mock_uc.table.return_value = _mock_chain([])
    resp = tc.get("/tasks/")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_tasks_returns_tasks(app_with_user_client):
    tc, mock_uc = app_with_user_client
    mock_uc.table.return_value = _mock_chain([TASK])
    resp = tc.get("/tasks/")
    assert resp.status_code == 200
    assert resp.json()[0]["title"] == "Fix bug"


def test_create_task(app_with_user_client):
    tc, mock_uc = app_with_user_client
    created = {**TASK, "title": "New task"}
    mock_uc.table.return_value = _mock_chain([created])
    resp = tc.post("/tasks/", json={"title": "New task", "assigned_to": "u1"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "New task"


def test_update_task_status(app_with_user_client):
    tc, mock_uc = app_with_user_client
    updated = {**TASK, "status": "done"}
    mock_uc.table.return_value = _mock_chain([updated])
    resp = tc.patch("/tasks/t1", json={"status": "done"})
    assert resp.status_code == 200
    assert resp.json()["status"] == "done"


def test_update_task_invalid_status(app_with_user_client):
    tc, mock_uc = app_with_user_client
    resp = tc.patch("/tasks/t1", json={"status": "invalid"})
    assert resp.status_code == 400


def test_update_task_not_found(app_with_user_client):
    tc, mock_uc = app_with_user_client
    mock_uc.table.return_value = _mock_chain([])
    resp = tc.patch("/tasks/missing", json={"status": "done"})
    assert resp.status_code == 404
