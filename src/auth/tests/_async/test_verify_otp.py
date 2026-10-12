import httpx
from supabase_auth import AsyncGoTrueClient

_SESSION = {
    "access_token": "access-token",
    "refresh_token": "refresh-token",
    "expires_in": 3600,
    "token_type": "bearer",
    "user": {
        "id": "11111111-1111-1111-1111-111111111111",
        "aud": "authenticated",
        "app_metadata": {},
        "user_metadata": {},
        "created_at": "2026-01-01T00:00:00Z",
    },
}


def _client() -> AsyncGoTrueClient:
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json=_SESSION))
    return AsyncGoTrueClient(
        url="http://localhost",
        http_client=httpx.AsyncClient(transport=transport),
        auto_refresh_token=False,
    )


async def test_verify_otp_recovery_notifies_password_recovery() -> None:
    client = _client()
    events: list[str] = []
    client.on_auth_state_change(lambda event, session: events.append(event))

    await client.verify_otp({"token_hash": "hash", "type": "recovery"})

    assert events == ["PASSWORD_RECOVERY"]


async def test_verify_otp_magiclink_notifies_signed_in() -> None:
    client = _client()
    events: list[str] = []
    client.on_auth_state_change(lambda event, session: events.append(event))

    await client.verify_otp({"token_hash": "hash", "type": "magiclink"})

    assert events == ["SIGNED_IN"]
