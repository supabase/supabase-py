import inspect
from collections.abc import Callable
from typing import Any

import pytest
from httpx import AsyncClient, Client, MockTransport, Request, Response

from postgrest import APIError, AsyncPostgrestClient, SyncPostgrestClient

URL = "https://example.supabase.co/rest/v1"


class Server:
    def __init__(self, *responses: Response) -> None:
        self.responses = list(responses)
        self.requests: list[Request] = []

    def __call__(self, request: Request) -> Response:
        self.requests.append(request)
        return self.responses[min(len(self.requests), len(self.responses)) - 1]


async def execute(
    use_async: bool,
    server: Server,
    build: Callable[[Any], Any],
) -> Any:
    transport = MockTransport(server)
    if use_async:
        async with AsyncPostgrestClient(
            URL, http_client=AsyncClient(transport=transport)
        ) as client:
            return await build(client).execute()
    with SyncPostgrestClient(URL, http_client=Client(transport=transport)) as client:
        result = build(client).execute()
        assert not inspect.isawaitable(result)
        return result


parametrize_clients = pytest.mark.parametrize(
    "use_async", [False, True], ids=["sync", "async"]
)

POSTGREST_ERROR = {
    "message": "permission denied for table countries",
    "code": "42501",
    "hint": "Grant the select privilege",
    "details": None,
}

BUILDERS: dict[str, Callable[[Any], Any]] = {
    "select": lambda c: c.table("countries").select("*"),
    "single": lambda c: c.table("countries").select("*").single(),
    "maybe_single": lambda c: c.table("countries").select("*").maybe_single(),
    "explain": lambda c: c.table("countries").select("*").explain(),
}


@parametrize_clients
@pytest.mark.parametrize("builder", BUILDERS.keys())
async def test_postgrest_errors_are_raised_as_api_error(
    use_async: bool, builder: str
) -> None:
    server = Server(Response(403, json=POSTGREST_ERROR))

    with pytest.raises(APIError) as exc_info:
        await execute(use_async, server, BUILDERS[builder])

    assert exc_info.value.code == "42501"
    assert exc_info.value.message == "permission denied for table countries"
    assert exc_info.value.hint == "Grant the select privilege"


@parametrize_clients
@pytest.mark.parametrize("builder", BUILDERS.keys())
async def test_non_json_errors_fall_back_to_status(
    use_async: bool, builder: str
) -> None:
    server = Server(Response(502, text="<html>Bad gateway</html>"))

    with pytest.raises(APIError) as exc_info:
        await execute(use_async, server, BUILDERS[builder])

    assert exc_info.value.code == "502"
    assert exc_info.value.message == "Bad Gateway"
    assert exc_info.value.details == "<html>Bad gateway</html>"


@parametrize_clients
async def test_single_returns_object(use_async: bool) -> None:
    server = Server(Response(200, json={"id": 1, "name": "Sweden"}))

    response = await execute(use_async, server, BUILDERS["single"])

    assert server.requests[0].headers["Accept"] == "application/vnd.pgrst.object+json"
    assert response.data == {"id": 1, "name": "Sweden"}


@parametrize_clients
@pytest.mark.parametrize(
    ("rows", "expected"),
    [([], None), ([{"id": 1}], {"id": 1})],
    ids=["no rows", "one row"],
)
async def test_maybe_single_returns_none_or_row(
    use_async: bool, rows: list[dict[str, int]], expected: Any
) -> None:
    server = Server(Response(200, json=rows))

    response = await execute(use_async, server, BUILDERS["maybe_single"])

    if expected is None:
        assert response is None
    else:
        assert response.data == expected


@parametrize_clients
async def test_maybe_single_rejects_multiple_rows(use_async: bool) -> None:
    server = Server(Response(200, json=[{"id": 1}, {"id": 2}]))

    with pytest.raises(APIError) as exc_info:
        await execute(use_async, server, BUILDERS["maybe_single"])

    assert exc_info.value.code == "406"
    assert exc_info.value.details == "The result contains more than one row."


@parametrize_clients
async def test_explain_returns_plan_text(use_async: bool) -> None:
    plan = "Seq Scan on countries  (cost=0.00..1.01 rows=1 width=36)"
    server = Server(Response(200, text=plan))

    response = await execute(use_async, server, BUILDERS["explain"])

    assert (
        server.requests[0]
        .headers["Accept"]
        .startswith("application/vnd.pgrst.plan+text")
    )
    assert response == plan


@parametrize_clients
async def test_csv_returns_text(use_async: bool) -> None:
    server = Server(Response(200, text="id,name\n1,Sweden\n"))

    response = await execute(
        use_async, server, lambda c: c.table("countries").select("*").csv()
    )

    assert server.requests[0].headers["Accept"] == "text/csv"
    assert response.data == "id,name\n1,Sweden\n"


@parametrize_clients
@pytest.mark.parametrize("builder", BUILDERS.keys())
async def test_retry_can_be_disabled(use_async: bool, builder: str) -> None:
    server = Server(Response(503, json=POSTGREST_ERROR))

    with pytest.raises(APIError):
        await execute(use_async, server, lambda c: BUILDERS[builder](c).retry(False))

    assert len(server.requests) == 1


@parametrize_clients
async def test_select_after_insert_requests_representation(use_async: bool) -> None:
    server = Server(Response(201, json=[{"id": 1}]))

    response = await execute(
        use_async,
        server,
        lambda c: c.table("countries").insert({"name": "Sweden"}).select("id"),
    )

    request = server.requests[0]
    assert request.url.params["select"] == "id"
    assert "return=representation" in request.headers["Prefer"]
    assert response.data == [{"id": 1}]


def test_api_error_repr_lists_present_fields() -> None:
    error = APIError({"message": "boom", "code": "500", "hint": None})

    assert repr(error) == "Error 500:\nMessage: boom"


def test_api_error_repr_without_fields() -> None:
    assert repr(APIError({})) == "Empty error"
