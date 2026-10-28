import json

from httpx import Request, Response
from supabase_utils.types import JSON

from storage3.types import VectorData, VectorObject

from .utils import call_with_client, use_async


@use_async
async def test_put_vectors_preserves_array_metadata(use_async: bool) -> None:
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

    await call_with_client(
        use_async,
        handle_request,
        lambda client: client.vectors()
        .from_("catalog")
        .index("products")
        .put([vector]),
    )

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
