import pytest
from httpx import AsyncClient, BasicAuth, Client, MockTransport, Request, Response
from supabase_utils.http.adapters.httpx import AsyncHttpxSession, HttpxSession

from postgrest import AsyncPostgrestClient, SyncPostgrestClient

ENDPOINTS = ["table", "rpc"]
AUTH_CASES = [
    (None, "Basic dHJhbnNwb3J0OnNlY3JldA=="),
    ("bearer", "Bearer user-jwt"),
    ("header", "Bearer header-jwt"),
    ("basic", "Basic c2RrOnBhc3N3b3Jk"),
]


def client_headers(sdk_auth: str | None) -> dict[str, str]:
    return {"Authorization": "Bearer header-jwt"} if sdk_auth == "header" else {}


@pytest.mark.parametrize("endpoint", ENDPOINTS)
@pytest.mark.parametrize("sdk_auth, expected_authorization", AUTH_CASES)
def test_sync_injected_client_auth(
    endpoint: str, sdk_auth: str | None, expected_authorization: str
) -> None:
    requests: list[Request] = []

    def handler(request: Request) -> Response:
        requests.append(request)
        return Response(200, json=[{"id": 1}])

    with Client(
        auth=BasicAuth("transport", "secret"), transport=MockTransport(handler)
    ) as http:
        client = SyncPostgrestClient(
            "https://example.com",
            http_session=HttpxSession(client=http),
            headers=client_headers(sdk_auth),
        )
        if sdk_auth == "bearer":
            client.set_auth("user-jwt")
        elif sdk_auth == "basic":
            client.set_auth_with_password("sdk", "password")

        if endpoint == "table":
            response = client.table("items").select("id").execute()
        else:
            response = client.rpc("get_items", {}).execute()

    assert response.data == [{"id": 1}]
    assert len(requests) == 1
    assert requests[0].headers.get_list("Authorization") == [expected_authorization]


@pytest.mark.parametrize("endpoint", ENDPOINTS)
@pytest.mark.parametrize("sdk_auth, expected_authorization", AUTH_CASES)
async def test_async_injected_client_auth(
    endpoint: str, sdk_auth: str | None, expected_authorization: str
) -> None:
    requests: list[Request] = []

    def handler(request: Request) -> Response:
        requests.append(request)
        return Response(200, json=[{"id": 1}])

    async with AsyncClient(
        auth=BasicAuth("transport", "secret"), transport=MockTransport(handler)
    ) as http:
        client = AsyncPostgrestClient(
            "https://example.com",
            http_session=AsyncHttpxSession(client=http),
            headers=client_headers(sdk_auth),
        )
        if sdk_auth == "bearer":
            client.set_auth("user-jwt")
        elif sdk_auth == "basic":
            client.set_auth_with_password("sdk", "password")

        if endpoint == "table":
            response = await client.table("items").select("id").execute()
        else:
            response = await client.rpc("get_items", {}).execute()

    assert response.data == [{"id": 1}]
    assert len(requests) == 1
    assert requests[0].headers.get_list("Authorization") == [expected_authorization]
