import json
from datetime import datetime, timezone
from typing import Any

from httpx import Request, Response

from .utils import call_with_client, use_async


@use_async
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

    result = await call_with_client(
        use_async,
        handler,
        lambda client: client.vectors().from_("catalog").get_index("products"),
    )

    assert result is not None
    assert result.index.creation_time == datetime(2025, 1, 1, tzinfo=timezone.utc)


@use_async
async def test_list_indexes_sends_camel_case_pagination(use_async: bool) -> None:
    captured: dict[str, Any] = {}

    def handler(request: Request) -> Response:
        captured["url"] = str(request.url)
        captured["body"] = json.loads(request.content)
        return Response(200, json={"indexes": [], "nextToken": None})

    await call_with_client(
        use_async,
        handler,
        lambda client: client.vectors()
        .from_("my-bucket")
        .list_indexes(next_token="cursor-1", max_results=10, prefix="idx-"),
    )

    assert captured["url"].endswith("/vector/ListIndexes")
    assert captured["body"] == {
        "vectorBucketName": "my-bucket",
        "nextToken": "cursor-1",
        "maxResults": 10,
        "prefix": "idx-",
    }
