from collections.abc import AsyncIterator, Callable
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import AsyncClient, Client, MockTransport, Request, Response

from postgrest import APIError, AsyncPostgrestClient, SyncPostgrestClient

URL = "https://example.supabase.co/rest/v1"


@pytest.fixture(params=["sync", "async"])
async def client(
    request: pytest.FixtureRequest,
) -> AsyncIterator[SyncPostgrestClient | AsyncPostgrestClient]:
    if request.param == "sync":
        with SyncPostgrestClient(URL) as sync_client:
            yield sync_client
    else:
        async with AsyncPostgrestClient(URL) as async_client:
            yield async_client


def params(builder: Any) -> dict[str, str]:
    return dict(builder.request.params)


@pytest.mark.parametrize(
    ("method", "operator"),
    [("fts", "fts"), ("plfts", "plfts"), ("phfts", "phfts"), ("wfts", "wfts")],
)
def test_text_search_shorthands(client: Any, method: str, operator: str) -> None:
    builder = getattr(client.table("posts").select("*"), method)("body", "cat & dog")

    assert params(builder)["body"] == f"{operator}.cat & dog"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("[1,5)", "cd.[1,5)"),
        (["a", "b c"], 'cd.{a,"b c"}'),
        ({"role": "admin"}, 'cd.{"role": "admin"}'),
    ],
    ids=["range", "array", "json"],
)
def test_contained_by_encodes_each_value_kind(
    client: Any, value: Any, expected: str
) -> None:
    builder = client.table("users").select("*").contained_by("tags", value)

    assert params(builder)["tags"] == expected


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("[1,5)", "ov.[1,5)"),
        (["a,b", "c"], 'ov.{"a,b",c}'),
        ({"a": 1}, 'ov.{"a": 1}'),
    ],
    ids=["range", "array", "json"],
)
def test_overlaps_encodes_each_value_kind(
    client: Any, value: Any, expected: str
) -> None:
    builder = client.table("users").select("*").ov("tags", value)

    assert params(builder)["tags"] == expected


def test_contains_with_json_object(client: Any) -> None:
    builder = client.table("users").select("*").contains("meta", {"role": "admin"})

    assert params(builder)["meta"] == 'cs.{"role": "admin"}'


def test_strictly_left_of_range(client: Any) -> None:
    builder = client.table("reservations").select("*").sl("during", (1, 10))

    assert params(builder)["during"] == "sl.(1,10)"


def test_match_requires_at_least_one_pair(client: Any) -> None:
    with pytest.raises(ValueError, match="at least one key-value pair"):
        client.table("users").select("*").match({})


def test_offset_and_range_on_referenced_table(client: Any) -> None:
    builder = (
        client.table("orders").select("*, items(*)").offset(5).range(0, 9, "items")
    )

    assert params(builder) == {
        "select": "*,items(*)",
        "offset": "5",
        "items.offset": "0",
        "items.limit": "10",
    }


def test_select_keeps_whitespace_inside_quoted_columns(client: Any) -> None:
    builder = client.table("users").select('id, "full name"')

    assert params(builder)["select"] == 'id,"full name"'


def test_upsert_sets_on_conflict_and_missing_default(client: Any) -> None:
    builder = client.table("users").upsert(
        [{"id": 1, "name": "a"}], on_conflict="id", default_to_null=False
    )

    assert params(builder)["on_conflict"] == "id"
    prefer = builder.request.headers.get_list("Prefer", split_commas=True)
    assert "missing=default" in prefer
    assert "resolution=merge-duplicates" in prefer


def test_auth_without_credentials_raises(client: Any) -> None:
    with pytest.raises(ValueError, match="Neither bearer token"):
        client.auth(None)


def test_from_table_is_deprecated(client: Any) -> None:
    with pytest.warns(DeprecationWarning):
        builder = client.from_table("users")

    assert builder.path.path.endswith("/users")


@pytest.mark.parametrize(
    "client_class", [SyncPostgrestClient, AsyncPostgrestClient], ids=["sync", "async"]
)
@pytest.mark.parametrize(
    "kwargs", [{"verify": False}, {"proxy": "http://proxy.local"}], ids=str
)
def test_deprecated_transport_options_warn(
    client_class: type[SyncPostgrestClient] | type[AsyncPostgrestClient],
    kwargs: dict[str, Any],
) -> None:
    with pytest.warns(DeprecationWarning, match=next(iter(kwargs))):
        client_class(URL, **kwargs)


def test_strip_nulls_after_csv_is_rejected(client: Any) -> None:
    builder = client.table("users").select("*")
    builder.request.headers["Accept"] = "text/csv"

    with pytest.raises(ValueError, match="cannot be used with csv"):
        builder.strip_nulls()


class Server:
    def __init__(self, *statuses: int) -> None:
        self.statuses = list(statuses)
        self.requests: list[Request] = []

    def __call__(self, request: Request) -> Response:
        self.requests.append(request)
        status = self.statuses[min(len(self.requests), len(self.statuses)) - 1]
        if status >= 400:
            return Response(status, json={"message": "unavailable", "code": "503"})
        return Response(status, json=[{"id": 1}])


async def execute(use_async: bool, server: Server, build: Callable[[Any], Any]) -> Any:
    transport = MockTransport(server)
    if use_async:
        async with AsyncPostgrestClient(
            URL, http_client=AsyncClient(transport=transport)
        ) as async_client:
            with patch(
                "postgrest._async.request_builder.asyncio.sleep", new=AsyncMock()
            ):
                return await build(async_client).execute()
    with SyncPostgrestClient(
        URL, http_client=Client(transport=transport)
    ) as sync_client:
        with patch("postgrest._sync.request_builder.time.sleep", new=MagicMock()):
            return build(sync_client).execute()


parametrize_clients = pytest.mark.parametrize(
    "use_async", [False, True], ids=["sync", "async"]
)


@parametrize_clients
async def test_get_is_retried_on_service_unavailable(use_async: bool) -> None:
    server = Server(503, 520, 200)

    response = await execute(use_async, server, lambda c: c.table("t").select("*"))

    assert response.data == [{"id": 1}]
    assert [r.headers.get("X-Retry-Count") for r in server.requests] == [
        None,
        "1",
        "2",
    ]


@parametrize_clients
async def test_writes_are_not_retried(use_async: bool) -> None:
    server = Server(503, 200)

    with pytest.raises(APIError):
        await execute(use_async, server, lambda c: c.table("t").insert({"id": 1}))

    assert len(server.requests) == 1


@parametrize_clients
async def test_retries_stop_after_the_limit(use_async: bool) -> None:
    server = Server(503)

    with pytest.raises(APIError):
        await execute(use_async, server, lambda c: c.table("t").select("*"))

    assert len(server.requests) == 4
