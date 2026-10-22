import pytest
from httpx import Client, MockTransport, Request, Response
from supabase_auth import SyncGoTrueAdminAPI


@pytest.mark.parametrize("body", [{}, {"clients": []}])
def test_list_oauth_clients_when_none_are_registered(body: dict) -> None:
    def handler(request: Request) -> Response:
        assert request.method == "GET"
        assert request.url.path == "/auth/v1/admin/oauth/clients"
        return Response(200, json=body)

    with Client(transport=MockTransport(handler)) as http_client:
        admin = SyncGoTrueAdminAPI(
            url="https://example.supabase.co/auth/v1", http_client=http_client
        )
        response = admin.oauth.list_clients()

    assert response.clients == []
    assert response.next_page is None
    assert response.last_page == 0
    assert response.total == 0


def test_list_oauth_clients_preserves_registered_clients() -> None:
    client = {
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

    def handler(request: Request) -> Response:
        return Response(200, json={"clients": [client]})

    with Client(transport=MockTransport(handler)) as http_client:
        admin = SyncGoTrueAdminAPI(
            url="https://example.supabase.co/auth/v1", http_client=http_client
        )
        response = admin.oauth.list_clients()

    assert len(response.clients) == 1
    assert response.clients[0].client_id == client["client_id"]
    assert response.clients[0].client_name == client["client_name"]
