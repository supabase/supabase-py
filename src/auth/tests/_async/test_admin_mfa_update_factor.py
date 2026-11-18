import json

import pytest
from httpx import AsyncClient, MockTransport, Request, Response
from supabase_utils.http.adapters.httpx import AsyncHttpxSession

from supabase_auth import AsyncSupabaseAuthAdmin
from supabase_auth.errors import AuthApiError

USER_ID = "8c5e1b8a-3c0e-4f4c-9b6a-2d8f2f6c1a11"
FACTOR_ID = "0f6b7f3e-6a51-4d3e-8b8e-5f1b2a9c7d22"

FACTOR = {
    "id": FACTOR_ID,
    "friendly_name": "work phone",
    "factor_type": "phone",
    "status": "verified",
    "phone": "15550001111",
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-02T00:00:00Z",
}


def admin_client(
    response: Response,
) -> tuple[AsyncSupabaseAuthAdmin, list[Request]]:
    requests: list[Request] = []

    def handler(request: Request) -> Response:
        requests.append(request)
        return response

    client = AsyncSupabaseAuthAdmin(
        url="https://example.supabase.co/auth/v1",
        default_headers={"Authorization": "Bearer service-role-key"},
        http_session=AsyncHttpxSession(
            client=AsyncClient(transport=MockTransport(handler))
        ),
    )
    return client, requests


async def test_update_factor_sends_the_given_fields() -> None:
    client, requests = admin_client(Response(200, json=FACTOR))

    factor = await client.mfa.update_factor(
        USER_ID, FACTOR_ID, friendly_name="work phone", phone="+15550001111"
    )

    [request] = requests
    assert request.method == "PUT"
    assert request.url.path == f"/auth/v1/admin/users/{USER_ID}/factors/{FACTOR_ID}"
    assert json.loads(request.content) == {
        "friendly_name": "work phone",
        "phone": "+15550001111",
    }
    assert factor.id == FACTOR_ID
    assert factor.friendly_name == "work phone"
    assert factor.factor_type == "phone"


async def test_update_factor_leaves_out_fields_that_are_not_given() -> None:
    client, requests = admin_client(Response(200, json=FACTOR))

    await client.mfa.update_factor(USER_ID, FACTOR_ID, friendly_name="renamed")

    [request] = requests
    assert json.loads(request.content) == {"friendly_name": "renamed"}


async def test_update_factor_raises_the_api_error() -> None:
    client, _ = admin_client(
        Response(
            404,
            json={
                "code": 404,
                "error_code": "mfa_factor_not_found",
                "msg": "Factor not found",
            },
        )
    )

    with pytest.raises(AuthApiError) as error:
        await client.mfa.update_factor(USER_ID, FACTOR_ID, friendly_name="renamed")

    assert error.value.code == "mfa_factor_not_found"


@pytest.mark.parametrize(
    ("user_id", "factor_id"), [("not-a-uuid", FACTOR_ID), (USER_ID, "not-a-uuid")]
)
async def test_update_factor_rejects_invalid_ids(user_id: str, factor_id: str) -> None:
    client, requests = admin_client(Response(200, json=FACTOR))

    with pytest.raises(ValueError, match="Invalid id"):
        await client.mfa.update_factor(user_id, factor_id, friendly_name="renamed")

    assert requests == []
