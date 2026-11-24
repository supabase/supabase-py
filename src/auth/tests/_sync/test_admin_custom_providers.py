import json
from collections.abc import Callable
from datetime import UTC, datetime
from typing import Any

import pytest
from httpx import Client, MockTransport, Request, Response
from supabase_utils.http.adapters.httpx import HttpxSession
from yarl import URL

from supabase_auth import (
    CreateCustomProviderParams,
    SyncSupabaseAuthAdmin,
    SyncSupabaseAuthClient,
    UpdateCustomProviderParams,
)
from supabase_auth.errors import AuthApiError

AUTH_URL = "https://example.supabase.co/auth/v1"

PROVIDER: dict[str, Any] = {
    "id": "5473f521-21e6-443f-9edf-f4668832d87f",
    "provider_type": "oidc",
    "identifier": "custom:mycompany",
    "name": "My Company",
    "client_id": "client-id",
    "custom_claims_allowlist": ["groups", "org_id"],
    "attribute_mapping": {"email": "mail"},
    "authorization_params": {"prompt": "consent"},
    "issuer": "https://id.example.com",
    "discovery_document": {
        "issuer": "https://id.example.com",
        "authorization_endpoint": "https://id.example.com/authorize",
        "token_endpoint": "https://id.example.com/token",
        "jwks_uri": "https://id.example.com/jwks",
        "scopes_supported": ["openid", "email"],
    },
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-02T00:00:00Z",
}


def admin_client(
    requests: list[Request],
    respond: Callable[[Request], Response] = lambda _: Response(200, json=PROVIDER),
) -> SyncSupabaseAuthAdmin:
    def handler(request: Request) -> Response:
        requests.append(request)
        return respond(request)

    return SyncSupabaseAuthAdmin(
        url=AUTH_URL,
        http_session=HttpxSession(client=Client(transport=MockTransport(handler))),
    )


def test_list_providers() -> None:
    requests: list[Request] = []
    client = admin_client(
        requests, lambda _: Response(200, json={"providers": [PROVIDER]})
    )

    providers = client.custom_providers.list_providers()

    assert requests[0].method == "GET"
    assert requests[0].url.path == "/auth/v1/admin/custom-providers"
    assert requests[0].url.query == b""
    assert [provider.identifier for provider in providers] == ["custom:mycompany"]


def test_list_providers_filters_by_type() -> None:
    requests: list[Request] = []
    client = admin_client(requests, lambda _: Response(200, json={"providers": []}))

    providers = client.custom_providers.list_providers(provider_type="oauth2")

    assert requests[0].url.params["type"] == "oauth2"
    assert providers == []


def test_list_providers_without_providers_key() -> None:
    client = admin_client([], lambda _: Response(200, json={}))

    assert client.custom_providers.list_providers() == []


def test_create_provider_sends_only_set_fields() -> None:
    requests: list[Request] = []

    provider = admin_client(requests).custom_providers.create_provider(
        CreateCustomProviderParams(
            provider_type="oidc",
            identifier="custom:mycompany",
            name="My Company",
            client_id="client-id",
            client_secret="client-secret",
            issuer="https://id.example.com",
            custom_claims_allowlist=["groups", "org_id"],
        )
    )

    assert requests[0].method == "POST"
    assert requests[0].url.path == "/auth/v1/admin/custom-providers"
    assert json.loads(requests[0].content) == {
        "provider_type": "oidc",
        "identifier": "custom:mycompany",
        "name": "My Company",
        "client_id": "client-id",
        "client_secret": "client-secret",
        "issuer": "https://id.example.com",
        "custom_claims_allowlist": ["groups", "org_id"],
    }
    assert provider.provider_type == "oidc"
    assert provider.custom_claims_allowlist == ["groups", "org_id"]
    assert provider.attribute_mapping == {"email": "mail"}
    assert provider.authorization_params == {"prompt": "consent"}
    assert provider.discovery_document is not None
    assert provider.discovery_document.scopes_supported == ["openid", "email"]
    assert provider.created_at == datetime(2026, 1, 1, tzinfo=UTC)


def test_get_provider() -> None:
    requests: list[Request] = []

    provider = admin_client(requests).custom_providers.get_provider("custom:mycompany")

    assert requests[0].method == "GET"
    assert requests[0].url.path == "/auth/v1/admin/custom-providers/custom:mycompany"
    assert provider.name == "My Company"


def test_update_provider_sends_only_set_fields() -> None:
    requests: list[Request] = []

    admin_client(requests).custom_providers.update_provider(
        "custom:mycompany",
        UpdateCustomProviderParams(enabled=False, custom_claims_allowlist=[]),
    )

    assert requests[0].method == "PUT"
    assert requests[0].url.path == "/auth/v1/admin/custom-providers/custom:mycompany"
    assert json.loads(requests[0].content) == {
        "enabled": False,
        "custom_claims_allowlist": [],
    }


def test_delete_provider() -> None:
    requests: list[Request] = []
    client = admin_client(requests, lambda _: Response(204))

    client.custom_providers.delete_provider("custom:mycompany")

    assert requests[0].method == "DELETE"
    assert requests[0].url.path == "/auth/v1/admin/custom-providers/custom:mycompany"


def test_delete_provider_raises_on_error() -> None:
    client = admin_client(
        [],
        lambda _: Response(
            404, json={"code": 404, "error_code": "not_found", "msg": "Not found"}
        ),
    )

    with pytest.raises(AuthApiError):
        client.custom_providers.delete_provider("custom:missing")


def test_provider_accepts_an_unknown_type() -> None:
    client = admin_client(
        [], lambda _: Response(200, json={**PROVIDER, "provider_type": "saml"})
    )

    provider = client.custom_providers.get_provider("custom:mycompany")

    assert provider.provider_type == "saml"


@pytest.mark.parametrize("identifier", ["", ".", "..", "custom:a/b"])
def test_rejects_identifiers_that_change_the_path(identifier: str) -> None:
    requests: list[Request] = []
    client = admin_client(requests)

    with pytest.raises(ValueError, match="Invalid custom provider identifier"):
        client.custom_providers.get_provider(identifier)
    with pytest.raises(ValueError, match="Invalid custom provider identifier"):
        client.custom_providers.update_provider(
            identifier, UpdateCustomProviderParams(name="x")
        )
    with pytest.raises(ValueError, match="Invalid custom provider identifier"):
        client.custom_providers.delete_provider(identifier)
    assert requests == []


def test_sign_in_with_oauth_accepts_a_custom_provider() -> None:
    client = SyncSupabaseAuthClient(
        url=AUTH_URL,
        auto_refresh_token=False,
        http_session=HttpxSession(
            client=Client(transport=MockTransport(lambda _: Response(500)))
        ),
    )

    response = client.sign_in_with_oauth("custom:mycompany")

    assert response.provider == "custom:mycompany"
    assert URL(response.url).query["provider"] == "custom:mycompany"


def test_sign_in_with_id_token_accepts_a_custom_provider() -> None:
    requests: list[Request] = []

    def handler(request: Request) -> Response:
        requests.append(request)
        return Response(
            200,
            json={
                "access_token": "access-token",
                "refresh_token": "refresh-token",
                "expires_in": 3600,
                "token_type": "bearer",
                "user": {
                    "id": "11111111-1111-1111-1111-111111111111",
                    "aud": "authenticated",
                    "app_metadata": {},
                    "user_metadata": {},
                    "created_at": "2020-01-01T00:00:00Z",
                },
            },
        )

    client = SyncSupabaseAuthClient(
        url=AUTH_URL,
        auto_refresh_token=False,
        http_session=HttpxSession(client=Client(transport=MockTransport(handler))),
    )

    client.sign_in_with_id_token("custom:mycompany", "id-token")

    assert requests[0].url.params["grant_type"] == "id_token"
    assert json.loads(requests[0].content)["provider"] == "custom:mycompany"
