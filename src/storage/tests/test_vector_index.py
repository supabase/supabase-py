from datetime import datetime, timezone

import pytest
from httpx import AsyncClient, Client, MockTransport, Request, Response
from storage3 import AsyncStorageClient, SyncStorageClient
from storage3.exceptions import StorageApiError


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


@pytest.mark.asyncio
@pytest.mark.parametrize("use_async", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize("status", [401, 403, 429, 500])
async def test_get_bucket_and_index_raise_on_non_404_errors(
    use_async: bool, status: int
) -> None:
    def handler(request: Request) -> Response:
        return Response(
            status,
            json={"statusCode": str(status), "error": "Error", "message": "failed"},
            request=request,
        )

    transport = MockTransport(handler)
    url = "https://example.supabase.co/storage/v1/"
    if use_async:
        async with AsyncClient(transport=transport) as http:
            vectors = AsyncStorageClient(url, {}, http_client=http).vectors()
            with pytest.raises(StorageApiError) as bucket_err:
                await vectors.get_bucket("catalog")
            with pytest.raises(StorageApiError) as index_err:
                await vectors.from_("catalog").get_index("products")
    else:
        with Client(transport=transport) as sync_http:
            sync_vectors = SyncStorageClient(url, {}, http_client=sync_http).vectors()
            with pytest.raises(StorageApiError) as bucket_err:
                sync_vectors.get_bucket("catalog")
            with pytest.raises(StorageApiError) as index_err:
                sync_vectors.from_("catalog").get_index("products")

    assert str(bucket_err.value.status) == str(status)
    assert str(index_err.value.status) == str(status)


@pytest.mark.asyncio
@pytest.mark.parametrize("use_async", [False, True], ids=["sync", "async"])
async def test_get_bucket_and_index_return_none_when_not_found(
    use_async: bool,
) -> None:
    def handler(request: Request) -> Response:
        return Response(
            404,
            json={
                "statusCode": "404",
                "error": "NotFoundException",
                "message": 'resource "catalog" not found',
            },
            request=request,
        )

    transport = MockTransport(handler)
    url = "https://example.supabase.co/storage/v1/"
    if use_async:
        async with AsyncClient(transport=transport) as http:
            vectors = AsyncStorageClient(url, {}, http_client=http).vectors()
            assert await vectors.get_bucket("catalog") is None
            assert await vectors.from_("catalog").get_index("products") is None
    else:
        with Client(transport=transport) as sync_http:
            sync_vectors = SyncStorageClient(url, {}, http_client=sync_http).vectors()
            assert sync_vectors.get_bucket("catalog") is None
            assert sync_vectors.from_("catalog").get_index("products") is None
