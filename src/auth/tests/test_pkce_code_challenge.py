from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest
from httpx import Response
from supabase_auth import AsyncGoTrueClient, SyncGoTrueClient
from supabase_auth.helpers import generate_pkce_challenge
from supabase_auth.types import Session

USER = {
    "id": "11111111-1111-1111-1111-111111111111",
    "aud": "authenticated",
    "app_metadata": {},
    "user_metadata": {},
    "created_at": "2020-01-01T00:00:00Z",
}
SESSION = {
    "access_token": "access-token",
    "refresh_token": "refresh-token",
    "expires_in": 3600,
    "token_type": "bearer",
    "user": USER,
}


def _response(payload: dict) -> Response:
    return Response(200, json=payload)


def _verifier_key(client: SyncGoTrueClient | AsyncGoTrueClient) -> str:
    return f"{client._storage_key}-code-verifier"


def test_sync_email_sign_up_pkce_sends_code_challenge() -> None:
    client = SyncGoTrueClient(
        url="https://example.supabase.co/auth/v1", flow_type="pkce"
    )
    with patch.object(client, "_request", return_value=_response(USER)) as request:
        client.sign_up({"email": "a@example.com", "password": "password"})

    stored = client._storage.get_item(_verifier_key(client))
    body = request.call_args.kwargs["body"]
    assert stored
    assert "/" not in stored
    assert body["code_challenge"] == generate_pkce_challenge(stored)
    assert body["code_challenge_method"] == "s256"


def test_sync_email_sign_up_implicit_omits_code_challenge() -> None:
    client = SyncGoTrueClient(
        url="https://example.supabase.co/auth/v1", flow_type="implicit"
    )
    with patch.object(client, "_request", return_value=_response(USER)) as request:
        client.sign_up({"email": "a@example.com", "password": "password"})

    assert "code_challenge" not in request.call_args.kwargs["body"]
    assert client._storage.get_item(_verifier_key(client)) is None


def test_sync_phone_sign_up_pkce_omits_code_challenge() -> None:
    client = SyncGoTrueClient(
        url="https://example.supabase.co/auth/v1", flow_type="pkce"
    )
    with patch.object(client, "_request", return_value=_response(USER)) as request:
        client.sign_up({"phone": "+15555550100", "password": "password"})

    assert "code_challenge" not in request.call_args.kwargs["body"]
    assert client._storage.get_item(_verifier_key(client)) is None


def test_sync_email_otp_pkce_sends_code_challenge() -> None:
    client = SyncGoTrueClient(
        url="https://example.supabase.co/auth/v1", flow_type="pkce"
    )
    with patch.object(client, "_request", return_value=_response({})) as request:
        client.sign_in_with_otp({"email": "a@example.com"})

    stored = client._storage.get_item(_verifier_key(client))
    body = request.call_args.kwargs["body"]
    assert stored
    assert body["code_challenge"] == generate_pkce_challenge(stored)
    assert body["code_challenge_method"] == "s256"


def test_sync_sso_pkce_sends_code_challenge() -> None:
    client = SyncGoTrueClient(
        url="https://example.supabase.co/auth/v1", flow_type="pkce"
    )
    with patch.object(
        client, "_request", return_value=_response({"url": "https://idp.example/sso"})
    ) as request:
        client.sign_in_with_sso({"domain": "example.com"})

    stored = client._storage.get_item(_verifier_key(client))
    body = request.call_args.kwargs["body"]
    assert stored
    assert body["code_challenge"] == generate_pkce_challenge(stored)
    assert body["code_challenge_method"] == "s256"


def test_sync_reset_password_pkce_stores_recovery_verifier() -> None:
    client = SyncGoTrueClient(
        url="https://example.supabase.co/auth/v1", flow_type="pkce"
    )
    with patch.object(client, "_request", return_value=_response({})) as request:
        client.reset_password_for_email("a@example.com")

    stored = client._storage.get_item(_verifier_key(client))
    assert stored
    verifier, redirect_type = stored.split("/", 1)
    assert redirect_type == "PASSWORD_RECOVERY"
    body = request.call_args.kwargs["body"]
    assert body["code_challenge"] == generate_pkce_challenge(verifier)
    assert body["code_challenge_method"] == "s256"


def test_sync_update_user_email_pkce_sends_code_challenge() -> None:
    client = SyncGoTrueClient(
        url="https://example.supabase.co/auth/v1", flow_type="pkce"
    )
    session = Session.model_validate(SESSION)
    with (
        patch.object(client, "get_session", return_value=session),
        patch.object(client, "_request", return_value=_response(USER)) as request,
    ):
        client.update_user({"email": "new@example.com"})

    stored = client._storage.get_item(_verifier_key(client))
    body = request.call_args.kwargs["body"]
    assert stored
    assert body["email"] == "new@example.com"
    assert body["code_challenge"] == generate_pkce_challenge(stored)
    assert body["code_challenge_method"] == "s256"


def test_sync_exchange_code_strips_recovery_suffix() -> None:
    client = SyncGoTrueClient(
        url="https://example.supabase.co/auth/v1", flow_type="pkce"
    )
    client._storage.set_item(_verifier_key(client), "verifier-value/PASSWORD_RECOVERY")
    with patch.object(client, "_request", return_value=_response(SESSION)) as request:
        client.exchange_code_for_session(
            {"auth_code": "auth-code", "code_verifier": "", "redirect_to": ""}
        )

    assert request.call_args.kwargs["body"]["code_verifier"] == "verifier-value"


@pytest.mark.asyncio
async def test_async_email_sign_up_pkce_sends_code_challenge() -> None:
    client = AsyncGoTrueClient(
        url="https://example.supabase.co/auth/v1", flow_type="pkce"
    )
    with patch.object(
        client, "_request", new=AsyncMock(return_value=_response(USER))
    ) as request:
        await client.sign_up({"email": "a@example.com", "password": "password"})

    stored = await client._storage.get_item(_verifier_key(client))
    body = request.call_args.kwargs["body"]
    assert stored
    assert body["code_challenge"] == generate_pkce_challenge(stored)
    assert body["code_challenge_method"] == "s256"


@pytest.mark.asyncio
async def test_async_reset_password_pkce_stores_recovery_verifier() -> None:
    client = AsyncGoTrueClient(
        url="https://example.supabase.co/auth/v1", flow_type="pkce"
    )
    with patch.object(
        client, "_request", new=AsyncMock(return_value=_response({}))
    ) as request:
        await client.reset_password_for_email("a@example.com")

    stored = await client._storage.get_item(_verifier_key(client))
    assert stored
    verifier, redirect_type = stored.split("/", 1)
    assert redirect_type == "PASSWORD_RECOVERY"
    assert request.call_args.kwargs["body"][
        "code_challenge"
    ] == generate_pkce_challenge(verifier)
