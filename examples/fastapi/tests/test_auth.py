import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient


def _make_auth_response(email: str) -> MagicMock:
    user = MagicMock()
    user.id = "user-123"
    user.email = email
    session = MagicMock()
    session.access_token = "fake-access-token"
    session.refresh_token = "fake-refresh-token"
    resp = MagicMock()
    resp.user = user
    resp.session = session
    return resp


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
def app_client():
    mock_sc = _make_mock_service_client()
    with patch("main.acreate_client", AsyncMock(return_value=mock_sc)), \
         patch("main.start_engine", AsyncMock()):
        from main import app
        with TestClient(app) as tc:
            yield tc


def test_signup_returns_user_and_session(app_client):
    mock_anon = AsyncMock()
    mock_anon.auth.sign_up = AsyncMock(return_value=_make_auth_response("a@b.com"))
    with patch("routers.auth.acreate_client", AsyncMock(return_value=mock_anon)):
        resp = app_client.post("/auth/signup", json={"email": "a@b.com", "password": "pass1234"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["user"]["email"] == "a@b.com"
    assert body["session"]["access_token"] == "fake-access-token"


def test_signin_returns_session(app_client):
    mock_anon = AsyncMock()
    mock_anon.auth.sign_in_with_password = AsyncMock(return_value=_make_auth_response("a@b.com"))
    with patch("routers.auth.acreate_client", AsyncMock(return_value=mock_anon)):
        resp = app_client.post("/auth/signin", json={"email": "a@b.com", "password": "pass1234"})
    assert resp.status_code == 200
    assert resp.json()["session"]["access_token"] == "fake-access-token"


def test_signout_returns_ok(app_client):
    resp = app_client.post("/auth/signout")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
