import inspect
from collections.abc import AsyncIterator

import pytest
from httpx import AsyncClient, Client, MockTransport, Request, Response

from postgrest import AsyncPostgrestClient, SyncPostgrestClient


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


@pytest.mark.parametrize(
    "single, expected",
    [
        (False, "application/vnd.pgrst.array+json;nulls=stripped"),
        (True, "application/vnd.pgrst.object+json;nulls=stripped"),
    ],
)
async def test_strip_nulls_sets_accept_header(
    client, accept_headers: list[str], single: bool, expected: str
) -> None:
    query = client.from_("users").select("*").strip_nulls()
    await execute(query.single() if single else query)
    assert accept_headers == [expected]


async def test_csv_without_strip_nulls_requests_csv(
    client, accept_headers: list[str]
) -> None:
    await execute(client.from_("users").select("*").csv())
    assert accept_headers == ["text/csv"]


@pytest.mark.parametrize("method", ["csv", "explain"])
def test_format_after_strip_nulls_is_rejected(client, method: str) -> None:
    query = client.from_("users").select("*").strip_nulls()
    with pytest.raises(
        ValueError, match=rf"strip_nulls\(\) cannot be used with {method}"
    ):
        getattr(query, method)()


def test_strip_nulls_after_csv_is_rejected(client) -> None:
    query = client.from_("users").select("*").csv()
    with pytest.raises((AttributeError, ValueError)):
        query.strip_nulls()


def test_rpc_csv_after_strip_nulls_is_rejected(client) -> None:
    query = client.rpc("get_users", {}).strip_nulls()
    with pytest.raises(ValueError, match=r"strip_nulls\(\) cannot be used with csv"):
        query.csv()


def test_rpc_strip_nulls_after_csv_is_rejected(client) -> None:
    query = client.rpc("get_users", {}).csv()
    with pytest.raises(ValueError, match=r"strip_nulls\(\) cannot be used with csv"):
        query.strip_nulls()
