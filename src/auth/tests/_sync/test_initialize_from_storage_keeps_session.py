import json
import time

import httpx
from supabase_auth import SyncGoTrueClient, SyncMemoryStorage

_STORAGE_KEY = "supabase.auth.token"
_USER = {
    "id": "11111111-1111-1111-1111-111111111111",
    "aud": "authenticated",
    "app_metadata": {},
    "user_metadata": {},
    "created_at": "2026-01-01T00:00:00Z",
    "email": "user@example.com",
}


def _expired_session() -> dict:
    return {
        "access_token": "old-access",
        "refresh_token": "old-refresh",
        "expires_in": 3600,
        "expires_at": round(time.time()) - 60,
        "token_type": "bearer",
        "user": _USER,
    }


def _client(
    auto_refresh_token: bool,
) -> tuple[SyncGoTrueClient, SyncMemoryStorage]:
    storage = SyncMemoryStorage()
    storage.set_item(_STORAGE_KEY, json.dumps(_expired_session()))

    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "access_token": "new-access",
                "refresh_token": "new-refresh",
                "expires_in": 3600,
                "token_type": "bearer",
                "user": _USER,
            },
        )

    client = SyncGoTrueClient(
        url="http://localhost",
        storage=storage,
        storage_key=_STORAGE_KEY,
        http_client=httpx.Client(transport=httpx.MockTransport(handler)),
        auto_refresh_token=auto_refresh_token,
    )
    return client, storage


def test_initialize_from_storage_keeps_expired_session_without_auto_refresh() -> None:
    client, storage = _client(auto_refresh_token=False)

    client.initialize_from_storage()

    stored = storage.get_item(_STORAGE_KEY)
    assert stored is not None
    assert json.loads(stored)["refresh_token"] == "old-refresh"

    session = client.get_session()
    assert session is not None
    assert session.access_token == "new-access"


def test_initialize_from_storage_refreshes_expired_session_with_auto_refresh() -> None:
    client, storage = _client(auto_refresh_token=True)

    client.initialize_from_storage()

    stored = storage.get_item(_STORAGE_KEY)
    assert stored is not None
    assert json.loads(stored)["access_token"] == "new-access"
