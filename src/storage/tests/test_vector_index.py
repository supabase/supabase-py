import json
from datetime import datetime, timezone
from typing import Any

import pytest
from httpx import AsyncClient, Client, MockTransport, Request, Response
from supabase_utils.http.adapters.httpx import AsyncHttpxSession, HttpxSession

from storage3 import AsyncStorageClient, SyncStorageClient

URL = "https://example.supabase.co/storage/v1/"


@pytest.mark.parametrize("use_async", [False, True], ids=["sync", "async"])
async def test_get_index_preserves_creation_time(use_async: bool) -> None:
    def handler(request: Request) -> Response:
        return Response(
            200,
            json={
                "index": {
                    "indexName": "products",
                    "vectorBucketName": "catalog",
                    "dataType": "float32",
                    "dimension": 2,
                    "distanceMetric": "cosine",
                    "creationTime": 1735689600,
                }
            },
            request=request,
        )

    transport = MockTransport(handler)
    if use_async:
        async with AsyncStorageClient(
            URL, {}, http_session=AsyncHttpxSession(AsyncClient(transport=transport))
        ) as client:
            result = await client.vectors().from_("catalog").get_index("products")
    else:
        with SyncStorageClient(
            URL, {}, http_session=HttpxSession(Client(transport=transport))
        ) as sync_client:
            result = sync_client.vectors().from_("catalog").get_index("products")

    assert result is not None
    assert result.index.creation_time == datetime(2025, 1, 1, tzinfo=timezone.utc)


@pytest.mark.parametrize("use_async", [False, True], ids=["sync", "async"])
async def test_list_indexes_sends_camel_case_pagination(use_async: bool) -> None:
    captured: dict[str, Any] = {}

    def handler(request: Request) -> Response:
        captured["url"] = str(request.url)
        captured["body"] = json.loads(request.content)
        return Response(200, json={"indexes": [], "nextToken": None})

    transport = MockTransport(handler)
    if use_async:
        async with AsyncStorageClient(
            URL, {}, http_session=AsyncHttpxSession(AsyncClient(transport=transport))
        ) as client:
            await (
                client.vectors()
                .from_("my-bucket")
                .list_indexes(next_token="cursor-1", max_results=10, prefix="idx-")
            )
    else:
        with SyncStorageClient(
            URL, {}, http_session=HttpxSession(Client(transport=transport))
        ) as sync_client:
            sync_client.vectors().from_("my-bucket").list_indexes(
                next_token="cursor-1", max_results=10, prefix="idx-"
            )

    assert captured["url"].endswith("/vector/ListIndexes")
    assert captured["body"] == {
        "vectorBucketName": "my-bucket",
        "nextToken": "cursor-1",
        "maxResults": 10,
        "prefix": "idx-",
    }
