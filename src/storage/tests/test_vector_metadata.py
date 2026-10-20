import json

import pytest
from httpx import AsyncClient, Client, MockTransport, Request, Response
from supabase_utils.http.adapters.httpx import AsyncHttpxSession, HttpxSession
from supabase_utils.types import JSON

from storage3 import AsyncStorageClient, SyncStorageClient
from storage3.types import VectorData, VectorObject

URL = "https://example.com/storage/v1/"


@pytest.mark.parametrize("asynchronous", [False, True])
async def test_put_vectors_preserves_array_metadata(asynchronous: bool) -> None:
    metadata: dict[str, JSON] = {
        "category": "electronics",
        "price": 299.99,
        "available": True,
        "tags": ["laptop", "portable"],
        "ratings": [4.5, 5.0],
        "in_stock": [True, False],
        "product_ids": [1, 2],
    }
    vector = VectorObject(
        key="product-001",
        data=VectorData(float32=[0.1, 0.2]),
        metadata=metadata,
    )
    requests: list[Request] = []

    def handle_request(request: Request) -> Response:
        requests.append(request)
        return Response(200, json={})

    transport = MockTransport(handle_request)
    if asynchronous:
        async with AsyncStorageClient(
            URL, {}, http_session=AsyncHttpxSession(AsyncClient(transport=transport))
        ) as client:
            await client.vectors().from_("catalog").index("products").put([vector])
    else:
        with SyncStorageClient(
            URL, {}, http_session=HttpxSession(Client(transport=transport))
        ) as sync_client:
            sync_client.vectors().from_("catalog").index("products").put([vector])

    assert len(requests) == 1
    assert requests[0].url.path.endswith("/PutVectors")
    body = json.loads(requests[0].content)
    assert body == {
        "vectorBucketName": "catalog",
        "indexName": "products",
        "vectors": [
            {
                "key": "product-001",
                "data": {"float32": [0.1, 0.2]},
                "metadata": metadata,
            }
        ],
    }
    assert all(
        isinstance(value, int)
        for value in body["vectors"][0]["metadata"]["product_ids"]
    )
