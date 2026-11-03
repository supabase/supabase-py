import inspect
from collections.abc import AsyncIterator

import pytest
from httpx import AsyncClient, Client, MockTransport, Request, Response

from postgrest import AsyncPostgrestClient, SyncPostgrestClient

ERROR = r"strip_nulls\(\) cannot be used with csv\(\)"


@pytest.fixture
def accept_headers() -> list[str]:
    return []


@pytest.fixture(params=["sync", "async"])
async def client(
    request, accept_headers: list[str]
) -> AsyncIterator[SyncPostgrestClient | AsyncPostgrestClient]:
    def handler(http_request: Request) -> Response:
        accept_headers.append(http_request.headers["Accept"])
        if http_request.headers["Accept"] == "text/csv":
            return Response(200, text="id,name\n1,Luke")
        return Response(200, json=[{"id": 1}])

    transport = MockTransport(handler)
    if request.param == "sync":
        with (
            Client(transport=transport) as http,
            SyncPostgrestClient("https://example.com", http_client=http) as client,
        ):
            yield client
    else:
        async with (
            AsyncClient(transport=transport) as async_http,
            AsyncPostgrestClient(
                "https://example.com", http_client=async_http
            ) as async_client,
        ):
            yield async_client


async def execute(query) -> None:
    result = query.execute()
    if inspect.isawaitable(result):
        await result


def test_csv_after_strip_nulls_is_rejected(client) -> None:
    query = client.from_("users").select("*").strip_nulls()
    with pytest.raises(ValueError, match=ERROR):
        query.csv()


def test_strip_nulls_after_csv_is_unavailable_on_select(client) -> None:
    query = client.from_("users").select("*").csv()
    with pytest.raises(AttributeError):
        query.strip_nulls()


def test_rpc_csv_after_strip_nulls_is_rejected(client) -> None:
    query = client.rpc("get_users", {}).strip_nulls()
    with pytest.raises(ValueError, match=ERROR):
        query.csv()


def test_rpc_strip_nulls_after_csv_is_rejected(client) -> None:
    query = client.rpc("get_users", {}).csv()
    with pytest.raises(ValueError, match=ERROR):
        query.strip_nulls()


async def test_csv_alone_requests_csv(client, accept_headers: list[str]) -> None:
    await execute(client.from_("users").select("*").csv())
    assert accept_headers == ["text/csv"]


async def test_strip_nulls_alone_requests_stripped_json(
    client, accept_headers: list[str]
) -> None:
    await execute(client.from_("users").select("*").strip_nulls())
    assert accept_headers == ["application/vnd.pgrst.array+json;nulls=stripped"]
