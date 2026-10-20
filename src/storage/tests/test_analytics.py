from typing import Any

import pytest
from httpx import AsyncClient, Client, MockTransport, Request, Response
from supabase_utils.http.adapters.httpx import AsyncHttpxSession, HttpxSession

from storage3 import AsyncStorageClient, SyncStorageClient

URL = "https://example.supabase.co/storage/v1/"


@pytest.mark.parametrize("use_async", [False, True], ids=["sync", "async"])
async def test_analytics_list_sends_camel_case_sort_params(use_async: bool) -> None:
    captured: dict[str, Any] = {}

    def handler(request: Request) -> Response:
        captured["url"] = request.url
        return Response(200, json=[])

    transport = MockTransport(handler)
    if use_async:
        async with AsyncStorageClient(
            URL, {}, http_session=AsyncHttpxSession(AsyncClient(transport=transport))
        ) as client:
            await client.analytics().list(
                limit=5,
                offset=10,
                sort_column="created_at",
                sort_order="desc",
                search="logs",
            )
    else:
        with SyncStorageClient(
            URL, {}, http_session=HttpxSession(Client(transport=transport))
        ) as sync_client:
            sync_client.analytics().list(
                limit=5,
                offset=10,
                sort_column="created_at",
                sort_order="desc",
                search="logs",
            )

    assert captured["url"].path.endswith("/iceberg/bucket")
    assert dict(captured["url"].params) == {
        "limit": "5",
        "offset": "10",
        "sortColumn": "created_at",
        "sortOrder": "desc",
        "search": "logs",
    }
