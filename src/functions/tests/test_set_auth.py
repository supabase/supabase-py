import pytest
from httpx import AsyncClient, Client, MockTransport, Request, Response
from supabase_functions import AsyncFunctionsClient, SyncFunctionsClient


@pytest.mark.parametrize("asynchronous", [False, True])
@pytest.mark.parametrize(
    "header_name", ["authorization", "aUtHoRiZaTiOn", "Authorization"]
)
async def test_set_auth_replaces_authorization_on_requests(
    asynchronous: bool, header_name: str
) -> None:
    requests: list[Request] = []

    def handle_request(request: Request) -> Response:
        requests.append(request)
        return Response(200, json={})

    headers = {header_name: "Bearer old-token", "apikey": "project-key"}
    transport = MockTransport(handle_request)
    if asynchronous:
        async with AsyncClient(transport=transport) as http_client:
            client = AsyncFunctionsClient(
                "https://example.com/functions/v1", headers, http_client=http_client
            )
            client.set_auth("new-token")
            await client.invoke("hello")
    else:
        with Client(transport=transport) as sync_http_client:
            sync_client = SyncFunctionsClient(
                "https://example.com/functions/v1",
                headers,
                http_client=sync_http_client,
            )
            sync_client.set_auth("new-token")
            sync_client.invoke("hello")

    assert requests[0].headers.get_list("authorization") == ["Bearer new-token"]
    assert requests[0].headers["apikey"] == "project-key"
    assert headers == {header_name: "Bearer old-token", "apikey": "project-key"}
