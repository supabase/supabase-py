import json
from typing import Any

import pytest
from httpx import Client, MockTransport, Request, Response
from supabase_utils.http.adapters.httpx import HttpxSession

from supabase_auth import (
    CreateSSOProviderParams,
    SAMLAttribute,
    SAMLAttributeMapping,
    SAMLNameIDFormat,
    SyncSupabaseAuthAdmin,
    UpdateSSOProviderParams,
)

PROVIDER: dict[str, Any] = {
    "id": "6f9df04a-7e61-4b36-a67c-de4d5044e04e",
    "resource_id": "acme",
    "disabled": None,
    "saml": {
        "entity_id": "https://idp.example.com/metadata",
        "metadata_url": "https://idp.example.com/metadata",
        "attribute_mapping": {"keys": {"email": {"name": "mail"}}},
        "name_id_format": "urn:oasis:names:tc:SAML:2.0:nameid-format:persistent",
    },
    "domains": [{"domain": "acme.com"}],
    "created_at": "2026-01-01T00:00:00Z",
    "updated_at": "2026-01-02T00:00:00Z",
}


def admin_client(
    requests: list[Request], status: int = 200, body: object = PROVIDER
) -> SyncSupabaseAuthAdmin:
    def handler(request: Request) -> Response:
        requests.append(request)
        return Response(status, json=body)

    return SyncSupabaseAuthAdmin(
        url="https://example.supabase.co/auth/v1",
        http_session=HttpxSession(client=Client(transport=MockTransport(handler))),
    )


def test_list_providers_sends_only_the_given_filters() -> None:
    requests: list[Request] = []

    providers = admin_client(requests, body={"items": [PROVIDER]}).sso.list_providers(
        resource_id_prefix="ac"
    )

    assert requests[0].method == "GET"
    assert requests[0].url.path == "/auth/v1/admin/sso/providers"
    assert dict(requests[0].url.params) == {"resource_id_prefix": "ac"}
    assert [provider.id for provider in providers] == [PROVIDER["id"]]


def test_list_providers_without_providers() -> None:
    requests: list[Request] = []

    providers = admin_client(requests, body={"items": []}).sso.list_providers()

    assert not requests[0].url.params
    assert providers == []


def test_create_provider_sends_a_saml_provider_and_accepts_201() -> None:
    requests: list[Request] = []

    provider = admin_client(requests, status=201).sso.create_provider(
        CreateSSOProviderParams(
            metadata_url="https://idp.example.com/metadata",
            domains=["acme.com"],
            attribute_mapping=SAMLAttributeMapping(
                keys={"email": SAMLAttribute(name="mail")}
            ),
            name_id_format=SAMLNameIDFormat.PERSISTENT,
            resource_id="acme",
        )
    )

    assert requests[0].method == "POST"
    assert requests[0].url.path == "/auth/v1/admin/sso/providers"
    assert json.loads(requests[0].content) == {
        "type": "saml",
        "metadata_url": "https://idp.example.com/metadata",
        "domains": ["acme.com"],
        "attribute_mapping": {"keys": {"email": {"name": "mail", "array": False}}},
        "name_id_format": "urn:oasis:names:tc:SAML:2.0:nameid-format:persistent",
        "resource_id": "acme",
    }
    assert provider.id == PROVIDER["id"]
    assert provider.resource_id == "acme"
    assert provider.disabled is False
    assert provider.domains == ["acme.com"]
    assert provider.saml is not None
    assert provider.saml.name_id_format is SAMLNameIDFormat.PERSISTENT
    assert provider.saml.attribute_mapping == SAMLAttributeMapping(
        keys={"email": SAMLAttribute(name="mail")}
    )


def test_get_provider_by_resource_id() -> None:
    requests: list[Request] = []

    admin_client(requests).sso.get_provider("resource_acme")

    assert requests[0].method == "GET"
    assert requests[0].url.path == "/auth/v1/admin/sso/providers/resource_acme"


def test_update_provider_keeps_empty_domains_and_mapping() -> None:
    requests: list[Request] = []

    admin_client(requests).sso.update_provider(
        PROVIDER["id"],
        UpdateSSOProviderParams(
            name_id_format=None,
            domains=[],
            attribute_mapping=SAMLAttributeMapping(),
        ),
    )

    assert requests[0].method == "PUT"
    assert requests[0].url.path == f"/auth/v1/admin/sso/providers/{PROVIDER['id']}"
    assert json.loads(requests[0].content) == {
        "domains": [],
        "attribute_mapping": {"keys": {}},
    }


def test_delete_provider() -> None:
    requests: list[Request] = []

    admin_client(requests).sso.delete_provider(PROVIDER["id"])

    assert requests[0].method == "DELETE"
    assert requests[0].url.path == f"/auth/v1/admin/sso/providers/{PROVIDER['id']}"


@pytest.mark.parametrize("provider_id", ["", ".", "..", "../../users/1"])
def test_provider_id_must_be_one_path_segment(provider_id: str) -> None:
    requests: list[Request] = []

    with pytest.raises(ValueError, match="provider_id"):
        admin_client(requests).sso.delete_provider(provider_id)

    assert requests == []


def test_provider_decodes_an_unknown_name_id_format() -> None:
    requests: list[Request] = []
    body = {**PROVIDER, "saml": {**PROVIDER["saml"], "name_id_format": "urn:new"}}

    provider = admin_client(requests, body=body).sso.get_provider(PROVIDER["id"])

    assert provider.saml is not None
    assert provider.saml.name_id_format == "urn:new"
