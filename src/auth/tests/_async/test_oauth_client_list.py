from typing import Any

import pytest
from httpx import AsyncClient, MockTransport, Request, Response
from supabase_utils.http.adapters.httpx import AsyncHttpxSession

from supabase_auth import AsyncSupabaseAuthAdmin

CLIENT: dict[str, Any] = {
    "client_id": "5473f521-21e6-443f-9edf-f4668832d87f",
    "client_name": "Example app",
    "client_type": "confidential",
    "token_endpoint_auth_method": "client_secret_basic",
    "registration_type": "manual",
    "redirect_uris": ["https://example.com/callback"],
    "grant_types": ["authorization_code", "refresh_token"],
    "response_types": ["code"],
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-01T00:00:00Z",
}

NAMELESS_CLIENT: dict[str, Any] = {
    key: value for key, value in CLIENT.items() if key != "client_name"
}


def admin_client(
    body: dict[str, Any], requests: list[Request] | None = None
) -> AsyncSupabaseAuthAdmin:
    def handler(request: Request) -> Response:
        if requests is not None:
            requests.append(request)
        assert request.method == "GET"
        return Response(200, json=body)

    return AsyncSupabaseAuthAdmin(
        url="https://example.supabase.co/auth/v1",
        http_session=AsyncHttpxSession(
            client=AsyncClient(transport=MockTransport(handler))
        ),
    )


@pytest.mark.parametrize("body", [{}, {"clients": []}])
async def test_list_oauth_clients_when_none_are_registered(
    body: dict[str, Any],
) -> None:
    response = await admin_client(body).oauth.list_clients()

    assert response.clients == []
    assert response.next_page is None
    assert response.last_page == 0
    assert response.total == 0


async def test_list_oauth_clients_preserves_registered_clients() -> None:
    requests: list[Request] = []

    response = await admin_client({"clients": [CLIENT]}, requests).oauth.list_clients()

    assert [request.url.path for request in requests] == [
        "/auth/v1/admin/oauth/clients"
    ]
    assert len(response.clients) == 1
    assert response.clients[0].client_id == CLIENT["client_id"]
    assert response.clients[0].client_name == CLIENT["client_name"]


async def test_list_oauth_clients_accepts_a_client_without_a_name() -> None:
    response = await admin_client(
        {"clients": [CLIENT, NAMELESS_CLIENT]}
    ).oauth.list_clients()

    assert [client.client_name for client in response.clients] == [
        "Example app",
        None,
    ]


async def test_get_oauth_client_accepts_a_client_without_a_name() -> None:
    requests: list[Request] = []

    response = await admin_client(NAMELESS_CLIENT, requests).oauth.get_client(
        CLIENT["client_id"]
    )

    assert [request.url.path for request in requests] == [
        f"/auth/v1/admin/oauth/clients/{CLIENT['client_id']}"
    ]
    assert response.client is not None
    assert response.client.client_id == CLIENT["client_id"]
    assert response.client.client_name is None
