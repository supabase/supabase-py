import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient


def _mock_chain(data):
    chain = MagicMock()
    chain.execute = AsyncMock(return_value=MagicMock(data=data))
    chain.eq.return_value = chain
    chain.select.return_value = chain
    chain.insert.return_value = chain
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


RULE = {
    "id": "r1", "user_id": "u1", "watch_column": "status",
    "watch_value": "done", "broadcast_channel": "team-alerts",
    "label": "Alert on done", "created_at": "2024-01-01T00:00:00Z",
}


def test_list_rules_empty(app_with_user_client):
    tc, mock_uc = app_with_user_client
    mock_uc.table.return_value = _mock_chain([])
    resp = tc.get("/rules/")
    assert resp.status_code == 200
    assert resp.json() == []


def test_list_rules_returns_rules(app_with_user_client):
    tc, mock_uc = app_with_user_client
    mock_uc.table.return_value = _mock_chain([RULE])
    resp = tc.get("/rules/")
    assert resp.status_code == 200
    assert resp.json()[0]["label"] == "Alert on done"


def test_create_rule(app_with_user_client):
    tc, mock_uc = app_with_user_client
    mock_uc.table.return_value = _mock_chain([RULE])
    resp = tc.post("/rules/", json={
        "label": "Alert on done", "watch_column": "status",
        "watch_value": "done", "broadcast_channel": "team-alerts",
    })
    assert resp.status_code == 200
    assert resp.json()["broadcast_channel"] == "team-alerts"


def test_delete_rule(app_with_user_client):
    tc, mock_uc = app_with_user_client
    mock_uc.table.return_value = _mock_chain([RULE])
    resp = tc.delete("/rules/r1")
    assert resp.status_code == 200
    assert resp.json() == {"deleted": "r1"}


def test_delete_rule_not_found(app_with_user_client):
    tc, mock_uc = app_with_user_client
    mock_uc.table.return_value = _mock_chain([])
    resp = tc.delete("/rules/missing")
    assert resp.status_code == 404
