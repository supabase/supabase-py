from __future__ import annotations

import pytest
from httpx import AsyncClient, BasicAuth, MockTransport, Request, Response

from postgrest import AsyncPostgrestClient

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
async def test_injected_client_auth(
    endpoint: str, sdk_auth: str | None, expected_authorization: str
) -> None:
    requests = []

    def handle_request(request: Request) -> Response:
        requests.append(request)
        return Response(200, json=[{"id": 1}])

    async with AsyncClient(
        auth=BasicAuth(TRANSPORT_USERNAME, TRANSPORT_PASSWORD),
        transport=MockTransport(handle_request),
    ) as http_client:
        headers = (
            {"Authorization": BEARER_AUTHORIZATION} if sdk_auth == "header" else {}
        )
        client = AsyncPostgrestClient(
            "https://example.com", headers=headers, http_client=http_client
        )
        if sdk_auth == "bearer":
            client.auth(TOKEN)
        elif sdk_auth == "basic":
            client.auth(None, username=USERNAME, password=PASSWORD)

        if endpoint == "table":
            response = await client.table("items").select("id").execute()
        else:
            response = await client.rpc("get_items", {}).execute()

    assert response.data == [{"id": 1}]
    assert len(requests) == 1
    assert requests[0].headers["Authorization"] == expected_authorization
