from httpx import Client, MockTransport, Request, Response
from supabase_utils.http.adapters.httpx import HttpxSession
from supabase_utils.types import JSON

from supabase_auth import SyncSupabaseAuthClient
from supabase_auth.types import Session

PHONE_FACTOR: dict[str, JSON] = {
    "id": "17a27e7e-8d2d-4a40-8614-e68e39c50891",
    "factor_type": "phone",
    "status": "verified",
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-01T00:00:00Z",
    "phone": "14155552671",
}

TOTP_FACTOR: dict[str, JSON] = {
    "id": "149a70cd-f90a-4c4a-9705-5d379bd8dacb",
    "factor_type": "totp",
    "status": "verified",
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-01T00:00:00Z",
}

USER: dict[str, JSON] = {
    "id": "ed6372d2-7107-425a-aecf-e5122c28cd9a",
    "aud": "authenticated",
    "app_metadata": {},
    "user_metadata": {},
    "created_at": "2026-01-01T00:00:00Z",
    "factors": [PHONE_FACTOR, TOTP_FACTOR],
}

SESSION: dict[str, JSON] = {
    "access_token": "access-token",
    "refresh_token": "refresh-token",
    "expires_in": 3600,
    "token_type": "bearer",
    "user": USER,
}


def test_list_factors_preserves_the_phone_number() -> None:
    def handler(request: Request) -> Response:
        assert request.method == "GET"
        assert request.url.path == "/auth/v1/user"
        assert request.headers["authorization"] == "Bearer access-token"
        return Response(200, json=USER)

    client = SyncSupabaseAuthClient(
        url="https://example.supabase.co/auth/v1",
        http_session=HttpxSession(client=Client(transport=MockTransport(handler))),
        auto_refresh_token=False,
    )
    client.session_manager.save_session(Session.model_validate(SESSION))

    factors = client.mfa.list_factors()

    assert len(factors.phone) == 1
    assert factors.phone[0].phone == "14155552671"
    assert len(factors.totp) == 1
    assert factors.totp[0].phone is None
    assert [factor.id for factor in factors.all] == [
        PHONE_FACTOR["id"],
        TOTP_FACTOR["id"],
    ]
