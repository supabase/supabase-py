from httpx import AsyncClient, MockTransport, Request, Response
from jwt import encode
from supabase_auth import AsyncGoTrueClient


async def test_list_factors_preserves_phone_number() -> None:
    user = {
        "id": "ed6372d2-7107-425a-aecf-e5122c28cd9a",
        "aud": "authenticated",
        "app_metadata": {},
        "user_metadata": {},
        "created_at": "2026-01-01T00:00:00Z",
        "factors": [
            {
                "id": "17a27e7e-8d2d-4a40-8614-e68e39c50891",
                "factor_type": "phone",
                "status": "verified",
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
                "phone": "14155552671",
            },
            {
                "id": "149a70cd-f90a-4c4a-9705-5d379bd8dacb",
                "factor_type": "totp",
                "status": "verified",
                "created_at": "2026-01-01T00:00:00Z",
                "updated_at": "2026-01-01T00:00:00Z",
            },
        ],
    }
    access_token = encode(
        {"sub": user["id"], "exp": 4102444800},
        "development-only-signing-key-32-bytes",
        algorithm="HS256",
    )

    def handler(request: Request) -> Response:
        if request.url.path == "/auth/v1/token":
            assert request.method == "POST"
            return Response(
                200,
                json={
                    "access_token": access_token,
                    "token_type": "bearer",
                    "expires_in": 3600,
                    "refresh_token": "refresh-token",
                    "user": user,
                },
            )
        assert request.method == "GET"
        assert request.url.path == "/auth/v1/user"
        assert request.headers["authorization"] == f"Bearer {access_token}"
        return Response(200, json=user)

    async with AsyncClient(transport=MockTransport(handler)) as http_client:
        auth = AsyncGoTrueClient(
            url="https://example.supabase.co/auth/v1",
            http_client=http_client,
            auto_refresh_token=False,
            persist_session=False,
        )
        await auth.sign_in_with_password(
            {"email": "caller@example.com", "password": "password"}
        )
        factors = await auth.mfa.list_factors()

    assert len(factors.phone) == 1
    assert factors.phone[0].phone == "14155552671"
    assert len(factors.totp) == 1
    assert factors.totp[0].phone is None
