import pytest
from httpx import AsyncClient, BasicAuth, Client, MockTransport, Request, Response
from supabase_utils.http.adapters.httpx import AsyncHttpxSession, HttpxSession

from supabase_functions import AsyncFunctionsClient, SyncFunctionsClient

AUTH_CASES = [
    (None, "Basic dHJhbnNwb3J0OnNlY3JldA=="),
    ("user-jwt", "Bearer user-jwt"),
]


@pytest.mark.parametrize("token, expected_authorization", AUTH_CASES)
def test_sync_injected_client_auth(
    token: str | None, expected_authorization: str
) -> None:
    requests: list[Request] = []

    def handler(request: Request) -> Response:
        requests.append(request)
        return Response(200, json={"ok": True})

    with Client(
        auth=BasicAuth("transport", "secret"), transport=MockTransport(handler)
    ) as http:
        client = SyncFunctionsClient(
            url="https://example.com",
            headers={},
            http_session=HttpxSession(client=http),
        )
        if token is not None:
            client.set_auth(token)
        client.invoke("hello")

    assert len(requests) == 1
    assert requests[0].headers.get_list("Authorization") == [expected_authorization]


@pytest.mark.parametrize("token, expected_authorization", AUTH_CASES)
async def test_async_injected_client_auth(
    token: str | None, expected_authorization: str
) -> None:
    requests: list[Request] = []

    def handler(request: Request) -> Response:
        requests.append(request)
        return Response(200, json={"ok": True})

    async with AsyncClient(
        auth=BasicAuth("transport", "secret"), transport=MockTransport(handler)
    ) as http:
        client = AsyncFunctionsClient(
            url="https://example.com",
            headers={},
            http_session=AsyncHttpxSession(client=http),
        )
        if token is not None:
            client.set_auth(token)
        await client.invoke("hello")

    assert len(requests) == 1
    assert requests[0].headers.get_list("Authorization") == [expected_authorization]
