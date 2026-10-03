from unittest.mock import AsyncMock, patch


def _make_mock_service_client():
    mock = AsyncMock()
    mock.realtime = AsyncMock()
    mock.realtime.connect = AsyncMock()
    mock.realtime.close = AsyncMock()
    ch = AsyncMock()
    ch.subscribe = AsyncMock()
    mock.channel.return_value = ch
    return mock


def test_health_returns_ok():
    mock_sc = _make_mock_service_client()
    with patch("main.acreate_client", AsyncMock(return_value=mock_sc)), \
         patch("main.start_engine", AsyncMock()):
        from fastapi.testclient import TestClient
        from main import app
        with TestClient(app) as client:
            response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
