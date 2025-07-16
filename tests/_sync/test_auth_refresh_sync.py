from supabase import create_client
import pytest

class DummySession:
    def __init__(self, access_token):
        self.access_token = access_token

def test_token_refresh_updates_header(monkeypatch):
    supabase = create_client("https://test.supabase.co", "original-key")

    session = DummySession("new-token-123")

    # simulate stale token (pretend something else set a new one)
    supabase.options.headers["Authorization"] = "Bearer old-token"

    supabase._listen_to_auth_events("TOKEN_REFRESHED", session)

    assert supabase.options.headers["Authorization"] == "Bearer new-token-123"
    assert supabase._postgrest is None
    assert supabase._storage is None
    assert supabase._functions is None

def test_no_update_when_auth_unchanged():
    supabase = create_client("https://test.supabase.co", "svc-role-key")
    auth_header_before = supabase.options.headers["Authorization"]
    supabase._listen_to_auth_events("SIGNED_IN", DummySession("new-token"))
    auth_header_after = supabase.options.headers["Authorization"]

    assert auth_header_before == auth_header_after
