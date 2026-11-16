import json
from datetime import UTC, datetime
from typing import Any

import pytest
from httpx import Request, Response
from pydantic import ValidationError

from storage3.types import MetadataConfiguration, VectorData, VectorIndex

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
    assert result.index.creation_time == datetime(2025, 1, 1, tzinfo=UTC)


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


def test_metadata_configuration_accepts_the_field_name() -> None:
    config = MetadataConfiguration(non_filterable_metadata_keys=["body"])
    assert config.non_filterable_metadata_keys == ["body"]


def test_metadata_configuration_accepts_the_alias() -> None:
    config = MetadataConfiguration(nonFilterableMetadataKeys=["body"])
    assert config.non_filterable_metadata_keys == ["body"]


def test_metadata_configuration_defaults_to_none() -> None:
    assert MetadataConfiguration().non_filterable_metadata_keys is None


def test_metadata_configuration_rejects_a_non_list() -> None:
    with pytest.raises(ValidationError):
        MetadataConfiguration.model_validate({"nonFilterableMetadataKeys": "body"})


def test_vector_index_parses_metadata_configuration() -> None:
    index = VectorIndex.model_validate(
        {
            "indexName": "products",
            "vectorBucketName": "catalog",
            "dataType": "float32",
            "dimension": 2,
            "distanceMetric": "cosine",
            "metadataConfiguration": {"nonFilterableMetadataKeys": ["body"]},
        }
    )
    assert index.metadata is not None
    assert index.metadata.non_filterable_metadata_keys == ["body"]


async def _create_index(
    use_async: bool, metadata: MetadataConfiguration | None
) -> dict[str, Any]:
    bodies: list[dict[str, Any]] = []

    def handler(request: Request) -> Response:
        bodies.append(json.loads(request.content))
        return Response(200, json={}, request=request)

    await call_with_client(
        use_async,
        handler,
        lambda client: client.vectors()
        .from_("catalog")
        .create_index("products", 2, "cosine", "float32", metadata=metadata),
    )

    assert len(bodies) == 1
    return bodies[0]


@use_async
@pytest.mark.parametrize(
    "metadata",
    [
        MetadataConfiguration(non_filterable_metadata_keys=["body"]),
        MetadataConfiguration(nonFilterableMetadataKeys=["body"]),
    ],
    ids=["field_name", "alias"],
)
async def test_create_index_sends_metadata_configuration(
    use_async: bool, metadata: MetadataConfiguration
) -> None:
    body = await _create_index(use_async, metadata)

    assert body == {
        "vectorBucketName": "catalog",
        "indexName": "products",
        "dimension": 2,
        "distanceMetric": "cosine",
        "dataType": "float32",
        "metadataConfiguration": {"nonFilterableMetadataKeys": ["body"]},
    }


@use_async
@pytest.mark.parametrize(
    "metadata", [None, MetadataConfiguration()], ids=["none", "empty"]
)
async def test_create_index_omits_empty_metadata_configuration(
    use_async: bool, metadata: MetadataConfiguration | None
) -> None:
    body = await _create_index(use_async, metadata)

    assert "metadataConfiguration" not in body


@use_async
async def test_create_index_sends_an_empty_key_list(use_async: bool) -> None:
    body = await _create_index(
        use_async, MetadataConfiguration(non_filterable_metadata_keys=[])
    )

    assert body["metadataConfiguration"] == {"nonFilterableMetadataKeys": []}


@use_async
async def test_query_vectors_sends_top_k(use_async: bool) -> None:
    captured: dict[str, Any] = {}

    def handler(request: Request) -> Response:
        captured["url"] = str(request.url)
        captured["body"] = json.loads(request.content)
        return Response(
            200,
            json={
                "vectors": [
                    {"key": "doc-1", "data": {"float32": [0.1, 0.2]}, "distance": 0.25}
                ]
            },
            request=request,
        )

    result = await call_with_client(
        use_async,
        handler,
        lambda client: client.vectors()
        .from_("embeddings")
        .index("docs")
        .query(VectorData(float32=[0.1, 0.2]), topK=3),
    )

    assert captured["url"].endswith("/vector/QueryVectors")
    assert captured["body"] == {
        "vectorBucketName": "embeddings",
        "indexName": "docs",
        "queryVector": {"float32": [0.1, 0.2]},
        "topK": 3,
        "returnDistance": True,
        "returnMetadata": True,
    }
    assert result.vectors[0].distance == 0.25


@use_async
async def test_query_vectors_requires_top_k(use_async: bool) -> None:
    requests: list[Request] = []

    def handler(request: Request) -> Response:
        requests.append(request)
        return Response(200, json={"vectors": []}, request=request)

    with pytest.raises(TypeError, match="topK"):
        await call_with_client(
            use_async,
            handler,
            lambda client: client.vectors()
            .from_("embeddings")
            .index("docs")
            .query(VectorData(float32=[0.1, 0.2])),
        )

    assert requests == []
