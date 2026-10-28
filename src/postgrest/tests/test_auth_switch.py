from typing import List, Optional

import pytest
from httpx import AsyncClient, Client, MockTransport, Request, Response

from postgrest import AsyncPostgrestClient, SyncPostgrestClient

from .credentials import (
    BASIC_AUTHORIZATION,
    BEARER_AUTHORIZATION,
    PASSWORD,
    TOKEN,
    USERNAME,
)


def recording_transport(requests: List[Request]) -> MockTransport:
    def respond(request: Request) -> Response:
        requests.append(request)
        return Response(200, json=[])

    return MockTransport(respond)


@pytest.mark.parametrize(
    "username", [None, "bob"], ids=["token-only", "token-preferred"]
)
def test_sync_auth_switches_from_basic_to_bearer(username: Optional[str]) -> None:
    requests: List[Request] = []
    with Client(transport=recording_transport(requests)) as http_client:
        with SyncPostgrestClient(
            "https://example.com", http_client=http_client
        ) as client:
            client.auth(None, username=USERNAME, password=PASSWORD)
            client.table("countries").select("*").execute()
            client.auth(TOKEN, username=username, password=PASSWORD)
            client.table("countries").select("*").execute()
            client.auth(None, username=USERNAME, password=PASSWORD)
            client.table("countries").select("*").execute()
            client.auth(TOKEN)
            client.table("countries").select("*").execute()

    assert [request.headers["Authorization"] for request in requests] == [
        BASIC_AUTHORIZATION,
        BEARER_AUTHORIZATION,
        BASIC_AUTHORIZATION,
        BEARER_AUTHORIZATION,
    ]


@pytest.mark.parametrize(
    "username", [None, "bob"], ids=["token-only", "token-preferred"]
)
async def test_async_auth_switches_from_basic_to_bearer(
    username: Optional[str],
) -> None:
    requests: List[Request] = []
    async with AsyncClient(transport=recording_transport(requests)) as http_client:
        async with AsyncPostgrestClient(
            "https://example.com", http_client=http_client
        ) as client:
            client.auth(None, username=USERNAME, password=PASSWORD)
            await client.table("countries").select("*").execute()
            client.auth(TOKEN, username=username, password=PASSWORD)
            await client.table("countries").select("*").execute()
            client.auth(None, username=USERNAME, password=PASSWORD)
            await client.table("countries").select("*").execute()
            client.auth(TOKEN)
            await client.table("countries").select("*").execute()

    assert [request.headers["Authorization"] for request in requests] == [
        BASIC_AUTHORIZATION,
        BEARER_AUTHORIZATION,
        BASIC_AUTHORIZATION,
        BEARER_AUTHORIZATION,
    ]
