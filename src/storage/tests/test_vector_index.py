from datetime import datetime, timezone

import pytest
from httpx import AsyncClient, Client, MockTransport, Request, Response
from storage3 import AsyncStorageClient, SyncStorageClient
from storage3.types import VectorIndex


@pytest.mark.asyncio
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
    url = "https://example.supabase.co/storage/v1/"
    if use_async:
        async with AsyncClient(transport=transport) as http:
            client = AsyncStorageClient(url, {}, http_client=http)
            result = await client.vectors().from_("catalog").get_index("products")
    else:
        with Client(transport=transport) as sync_http:
            sync_client = SyncStorageClient(url, {}, http_client=sync_http)
            result = sync_client.vectors().from_("catalog").get_index("products")

    assert result is not None
    assert result.index.creation_time == datetime(2025, 1, 1, tzinfo=timezone.utc)


@pytest.mark.parametrize(
    "timestamp", [{}, {"creationTime": None}, {"creation_time": None}]
)
def test_vector_index_creation_time_remains_optional(timestamp: dict) -> None:
    index = VectorIndex.model_validate(
        {
            "indexName": "products",
            "vectorBucketName": "catalog",
            "dataType": "float32",
            "dimension": 2,
            "distanceMetric": "cosine",
            **timestamp,
        }
    )
    assert index.creation_time is None


def test_vector_index_preserves_snake_case_creation_time() -> None:
    created_at = datetime(2025, 1, 1, tzinfo=timezone.utc)
    index = VectorIndex(
        indexName="products",
        vectorBucketName="catalog",
        dataType="float32",
        dimension=2,
        distanceMetric="cosine",
        creation_time=created_at,
    )
    assert index.creation_time == created_at
    assert index.model_dump(by_alias=True)["creation_time"] == created_at
