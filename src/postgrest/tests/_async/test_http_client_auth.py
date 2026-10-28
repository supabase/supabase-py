from __future__ import annotations

import pytest
from httpx import AsyncClient, BasicAuth, MockTransport, Request, Response

from postgrest import AsyncPostgrestClient


@pytest.mark.parametrize("endpoint", ["table", "rpc"])
@pytest.mark.parametrize(
    "sdk_auth, expected_authorization",
    [
        (None, "Basic dHJhbnNwb3J0OnNlY3JldA=="),
        ("bearer", "Bearer sdk-token"),
        ("header", "Bearer sdk-header"),
        ("basic", "Basic c2RrOnBhc3N3b3Jk"),
    ],
)
async def test_injected_client_auth(
    endpoint: str, sdk_auth: str | None, expected_authorization: str
):
    requests = []

    def handle_request(request: Request) -> Response:
        requests.append(request)
        return Response(200, json=[{"id": 1}])

    async with AsyncClient(
        auth=BasicAuth("transport", "secret"),
        transport=MockTransport(handle_request),
    ) as http_client:
        headers = {"Authorization": "Bearer sdk-header"} if sdk_auth == "header" else {}
        client = AsyncPostgrestClient(
            "https://example.com", headers=headers, http_client=http_client
        )
        if sdk_auth == "bearer":
            client.auth("sdk-token")
        elif sdk_auth == "basic":
            client.auth(None, username="sdk", password="password")

        if endpoint == "table":
            response = await client.table("items").select("id").execute()
        else:
            response = await client.rpc("get_items", {}).execute()

    assert response.data == [{"id": 1}]
    assert len(requests) == 1
    assert requests[0].headers["Authorization"] == expected_authorization
