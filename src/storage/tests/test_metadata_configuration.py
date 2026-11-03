import json

import pytest
from httpx import AsyncClient, Client, MockTransport, Request, Response
from storage3 import AsyncStorageClient, SyncStorageClient
from storage3.types import JSON, MetadataConfiguration, VectorIndex


def test_construct_by_field_name() -> None:
    config = MetadataConfiguration(non_filterable_metadata_keys=["body"])

    assert config.non_filterable_metadata_keys == ["body"]


def test_construct_by_alias() -> None:
    config = MetadataConfiguration(nonFilterableMetadataKeys=["body"])  # type: ignore[call-arg]

    assert config.non_filterable_metadata_keys == ["body"]


def test_validate_by_alias() -> None:
    config = MetadataConfiguration.model_validate(
        {"nonFilterableMetadataKeys": ["body"]}
    )

    assert config.non_filterable_metadata_keys == ["body"]


def test_parses_vector_index_response() -> None:
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


def test_defaults_to_none() -> None:
    assert MetadataConfiguration().non_filterable_metadata_keys is None


async def _create_index(
    use_async: bool, metadata: MetadataConfiguration | None
) -> dict[str, JSON]:
    bodies: list[dict[str, JSON]] = []

    def handler(request: Request) -> Response:
        bodies.append(json.loads(request.content))
        return Response(200, json={}, request=request)

    transport = MockTransport(handler)
    url = "https://example.supabase.co/storage/v1/"
    if use_async:
        async with AsyncClient(transport=transport) as http:
            client = AsyncStorageClient(url, {}, http_client=http)
            await (
                client.vectors()
                .from_("catalog")
                .create_index("products", 2, "cosine", "float32", metadata=metadata)
            )
    else:
        with Client(transport=transport) as sync_http:
            sync_client = SyncStorageClient(url, {}, http_client=sync_http)
            sync_client.vectors().from_("catalog").create_index(
                "products", 2, "cosine", "float32", metadata=metadata
            )

    assert len(bodies) == 1
    return bodies[0]


@pytest.mark.asyncio
@pytest.mark.parametrize("use_async", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize(
    "metadata",
    [
        MetadataConfiguration(non_filterable_metadata_keys=["body"]),
        MetadataConfiguration(nonFilterableMetadataKeys=["body"]),  # type: ignore[call-arg]
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


@pytest.mark.asyncio
@pytest.mark.parametrize("use_async", [False, True], ids=["sync", "async"])
@pytest.mark.parametrize(
    "metadata",
    [None, MetadataConfiguration()],
    ids=["none", "empty"],
)
async def test_create_index_omits_empty_metadata_configuration(
    use_async: bool, metadata: MetadataConfiguration | None
) -> None:
    body = await _create_index(use_async, metadata)

    assert "metadataConfiguration" not in body


@pytest.mark.asyncio
@pytest.mark.parametrize("use_async", [False, True], ids=["sync", "async"])
async def test_create_index_sends_empty_key_list(use_async: bool) -> None:
    body = await _create_index(
        use_async, MetadataConfiguration(non_filterable_metadata_keys=[])
    )

    assert body["metadataConfiguration"] == {"nonFilterableMetadataKeys": []}
