from typing import List, Optional

import pytest
from httpx import AsyncClient, Client, MockTransport, Request, Response

from postgrest import AsyncPostgrestClient, SyncPostgrestClient


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
            client.auth(None, username="alice", password="password")
            client.table("countries").select("*").execute()
            client.auth("new-token", username=username, password="ignored")
            client.table("countries").select("*").execute()
            client.auth(None, username="alice", password="password")
            client.table("countries").select("*").execute()
            client.auth("renewed-token")
            client.table("countries").select("*").execute()

    assert requests[0].headers["Authorization"] == "Basic YWxpY2U6cGFzc3dvcmQ="
    assert requests[1].headers["Authorization"] == "Bearer new-token"
    assert requests[2].headers["Authorization"] == requests[0].headers["Authorization"]
    assert requests[3].headers["Authorization"] == "Bearer renewed-token"


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
            client.auth(None, username="alice", password="password")
            await client.table("countries").select("*").execute()
            client.auth("new-token", username=username, password="ignored")
            await client.table("countries").select("*").execute()
            client.auth(None, username="alice", password="password")
            await client.table("countries").select("*").execute()
            client.auth("renewed-token")
            await client.table("countries").select("*").execute()

    assert requests[0].headers["Authorization"] == "Basic YWxpY2U6cGFzc3dvcmQ="
    assert requests[1].headers["Authorization"] == "Bearer new-token"
    assert requests[2].headers["Authorization"] == requests[0].headers["Authorization"]
    assert requests[3].headers["Authorization"] == "Bearer renewed-token"
