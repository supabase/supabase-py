import json

import httpx
import pytest
from supabase_auth import AsyncGoTrueClient, AsyncMemoryStorage
from supabase_auth.constants import STORAGE_KEY
from supabase_auth.errors import AuthApiError
from supabase_auth.helpers import generate_pkce_challenge

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


def _client(
    token_status: int = 200,
) -> tuple[AsyncGoTrueClient, AsyncMemoryStorage, list[httpx.Request]]:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        if request.url.path == "/token":
            assert request.url.params["grant_type"] == "pkce"
            payload = (
                _SESSION
                if token_status == 200
                else {"msg": "Invalid auth code", "error_code": "bad_code"}
            )
            return httpx.Response(token_status, json=payload)
        assert request.url.path in {"/recover", "/otp"}
        return httpx.Response(200, json={})

    storage = AsyncMemoryStorage()
    client = AsyncGoTrueClient(
        url="http://localhost",
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        storage=storage,
        storage_key="test-auth",
        flow_type="pkce",
        auto_refresh_token=False,
    )
    return client, storage, requests


@pytest.mark.parametrize(
    "recovery, explicit_verifier, expected_event",
    [
        (True, "", "PASSWORD_RECOVERY"),
        (False, "", "SIGNED_IN"),
        (True, "explicit-verifier", "SIGNED_IN"),
    ],
)
async def test_exchange_code_notifies_selected_flow(
    recovery: bool, explicit_verifier: str, expected_event: str
) -> None:
    client, storage, requests = _client()
    events: list[str] = []
    client.on_auth_state_change(lambda event, session: events.append(event))

    async with client:
        if recovery:
            await client.reset_password_for_email("user@example.com")
        else:
            await client.sign_in_with_otp({"email": "user@example.com"})

        stored = await storage.get_item("test-auth-code-verifier")
        assert stored is not None
        verifier = stored.split("/", 1)[0]
        challenge_body = json.loads(requests[0].content)
        assert challenge_body["code_challenge"] == generate_pkce_challenge(verifier)

        response = await client.exchange_code_for_session(
            {
                "auth_code": "auth-code",
                "code_verifier": explicit_verifier,
                "redirect_to": "",
            }
        )

        assert json.loads(requests[1].content) == {
            "auth_code": "auth-code",
            "code_verifier": explicit_verifier or verifier,
        }
        assert response.session is not None
        assert response.session.access_token == "access-token"
        saved = await client.get_session()
        assert saved is not None
        assert saved.access_token == "access-token"
        assert await storage.get_item("test-auth-code-verifier") is None
        assert events == [expected_event]


async def test_failed_recovery_exchange_preserves_verifier_without_notifying() -> None:
    client, storage, _ = _client(token_status=400)
    events: list[str] = []
    client.on_auth_state_change(lambda event, session: events.append(event))

    async with client:
        await client.reset_password_for_email("user@example.com")
        stored = await storage.get_item("test-auth-code-verifier")
        assert stored is not None

        with pytest.raises(AuthApiError, match="Invalid auth code"):
            await client.exchange_code_for_session(
                {"auth_code": "bad-code", "code_verifier": "", "redirect_to": ""}
            )

        assert await storage.get_item("test-auth-code-verifier") == stored
        assert await client.get_session() is None
        assert events == []


async def test_exchange_code_without_code_verifier_uses_stored_verifier() -> None:
    requests: list[httpx.Request] = []

    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=_SESSION)

    storage = AsyncMemoryStorage()
    client = AsyncGoTrueClient(
        url="http://localhost",
        http_client=httpx.AsyncClient(transport=httpx.MockTransport(handler)),
        storage=storage,
        flow_type="pkce",
        auto_refresh_token=False,
    )
    await storage.set_item(f"{STORAGE_KEY}-code-verifier", "stored-verifier")

    async with client:
        response = await client.exchange_code_for_session({"auth_code": "code"})

    assert len(requests) == 1
    assert requests[0].url.path == "/token"
    assert json.loads(requests[0].content) == {
        "auth_code": "code",
        "code_verifier": "stored-verifier",
    }
    assert response.session is not None
    assert await storage.get_item(f"{STORAGE_KEY}-code-verifier") is None
