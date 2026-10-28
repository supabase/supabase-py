from __future__ import annotations

import pytest
from httpx import BasicAuth, Client, MockTransport, Request, Response

from postgrest import SyncPostgrestClient

from ..credentials import (
    BASIC_AUTHORIZATION,
    BEARER_AUTHORIZATION,
    PASSWORD,
    TOKEN,
    USERNAME,
    basic_authorization,
)

TRANSPORT_USERNAME = "transport-user"
TRANSPORT_PASSWORD = "transport-password"


@pytest.mark.parametrize("endpoint", ["table", "rpc"])
@pytest.mark.parametrize(
    "sdk_auth, expected_authorization",
    [
        (None, basic_authorization(TRANSPORT_USERNAME, TRANSPORT_PASSWORD)),
        ("bearer", BEARER_AUTHORIZATION),
        ("header", BEARER_AUTHORIZATION),
        ("basic", BASIC_AUTHORIZATION),
    ],
)
def test_injected_client_auth(
    endpoint: str, sdk_auth: str | None, expected_authorization: str
):
    requests = []

    def handle_request(request: Request) -> Response:
        requests.append(request)
        return Response(200, json=[{"id": 1}])

    with Client(
        auth=BasicAuth(TRANSPORT_USERNAME, TRANSPORT_PASSWORD),
        transport=MockTransport(handle_request),
    ) as http_client:
        headers = (
            {"Authorization": BEARER_AUTHORIZATION} if sdk_auth == "header" else {}
        )
        client = SyncPostgrestClient(
            "https://example.com", headers=headers, http_client=http_client
        )
        if sdk_auth == "bearer":
            client.auth(TOKEN)
        elif sdk_auth == "basic":
            client.auth(None, username=USERNAME, password=PASSWORD)

        if endpoint == "table":
            response = client.table("items").select("id").execute()
        else:
            response = client.rpc("get_items", {}).execute()

    assert response.data == [{"id": 1}]
    assert len(requests) == 1
    assert requests[0].headers["Authorization"] == expected_authorization
