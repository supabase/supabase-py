import pytest
from supabase._async.client import create_client as create_async_client

class DummySession:
    def __init__(self, token):
        self.access_token = token

@pytest.mark.asyncio
async def test_async_auth_header_updates(monkeypatch):
    client = await create_async_client("https://example.supabase.co", "svc-key")

    # Fake realtime.set_auth
    called = {"token": None}
    async def fake_set_auth(token):
        called["token"] = token

    monkeypatch.setattr(client.realtime, "set_auth", fake_set_auth)

    client.options.headers["Authorization"] = "Bearer stale-token"
    session = DummySession("refreshed-token")

    await client._listen_to_auth_events("TOKEN_REFRESHED", session)

    assert client.options.headers["Authorization"] == "Bearer refreshed-token"
    assert called["token"] == "refreshed-token"
    assert client._postgrest is None
    assert client._storage is None
    assert client._functions is None


@pytest.mark.asyncio
async def test_async_no_update_if_original_token_used():
    client = await create_async_client("https://example.supabase.co", "svc-role-key")

    original_auth = client._create_auth_header(client.supabase_key)
    client.options.headers["Authorization"] = original_auth

    session = DummySession("some-other-token")
    await client._listen_to_auth_events("TOKEN_REFRESHED", session)

    # Should skip the update logic
    assert client.options.headers["Authorization"] == original_auth
