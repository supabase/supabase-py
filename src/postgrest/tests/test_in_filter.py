import pytest
from httpx import AsyncClient, Client, MockTransport, Request, Response

from postgrest import AsyncPostgrestClient, SyncPostgrestClient


@pytest.mark.parametrize("use_async", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize(
    "values, expected",
    [
        (
            ['ACME, "Pro"', r"C:\Reports,2026"],
            r'in.("ACME, \"Pro\"","C:\\Reports,2026")',
        ),
        (['"Pro"'], r'in.("\"Pro\"")'),
        ([r"folder\report"], r'in.("folder\\report")'),
        ([r"folder\"report"], r'in.("folder\\\"report")'),
        (
            ["normal", "a,b", "a:b", "a(b)", "table.column"],
            'in.(normal,"a,b","a:b","a(b)",table.column)',
        ),
    ],
)
async def test_in_filter_escapes_quoted_values(
    use_async: bool, values: list[str], expected: str
) -> None:
    def handler(request: Request) -> Response:
        assert request.url.params["name"] == expected
        return Response(200, json=[])

    url = "https://example.com"
    transport = MockTransport(handler)
    if use_async:
        async with AsyncClient(transport=transport) as http:
            client = AsyncPostgrestClient(url, http_client=http)
            await client.from_("products").select("*").in_("name", values).execute()
    else:
        with Client(transport=transport) as sync_http:
            sync_client = SyncPostgrestClient(url, http_client=sync_http)
            sync_client.from_("products").select("*").in_("name", values).execute()
