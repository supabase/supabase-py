import json
import sys
import warnings
from collections.abc import Callable
from typing import Any

import pytest
from httpx import AsyncClient, Client, MockTransport, Request, Response
from storage3 import AsyncStorageClient, SyncStorageClient, create_client
from storage3.exceptions import StorageApiError, VectorBucketException
from storage3.types import MetadataConfiguration, VectorData, VectorObject

BASE_URL = "https://example.supabase.co/storage/v1/"


class Recorder:
    def __init__(self, status: int = 200, body: Any = None) -> None:
        self.status = status
        self.body = {} if body is None else body
        self.requests: list[Request] = []

    def __call__(self, request: Request) -> Response:
        self.requests.append(request)
        return Response(self.status, json=self.body, request=request)

    @property
    def last_path(self) -> str:
        return self.requests[-1].url.path

    @property
    def last_json(self) -> Any:
        return json.loads(self.requests[-1].content)


async def run(
    use_async: bool,
    recorder: Recorder,
    operation: Callable[[Any], Any],
) -> Any:
    transport = MockTransport(recorder)
    if use_async:
        async with AsyncClient(transport=transport) as http:
            return await operation(AsyncStorageClient(BASE_URL, {}, http_client=http))
    with Client(transport=transport) as sync_http:
        return operation(SyncStorageClient(BASE_URL, {}, http_client=sync_http))


parametrize_clients = pytest.mark.parametrize(
    "use_async", [False, True], ids=["sync", "async"]
)


@parametrize_clients
async def test_create_bucket_sends_bucket_name(use_async: bool) -> None:
    recorder = Recorder()
    await run(use_async, recorder, lambda c: c.vectors().create_bucket("embeddings"))

    assert recorder.last_path == "/storage/v1/vector/CreateVectorBucket"
    assert recorder.last_json == {"vectorBucketName": "embeddings"}


@parametrize_clients
async def test_get_bucket_parses_response(use_async: bool) -> None:
    recorder = Recorder(
        body={
            "vectorBucket": {
                "vectorBucketName": "embeddings",
                "creationTime": 1735689600,
                "encryptionConfiguration": {"sseType": "AES256"},
            }
        }
    )
    result = await run(
        use_async, recorder, lambda c: c.vectors().get_bucket("embeddings")
    )

    assert recorder.last_path == "/storage/v1/vector/GetVectorBucket"
    assert result.vectorBucket.vectorBucketName == "embeddings"
    assert result.vectorBucket.encryptionConfiguration.sseType == "AES256"


@parametrize_clients
async def test_get_bucket_returns_none_on_api_error(use_async: bool) -> None:
    recorder = Recorder(
        status=404,
        body={"statusCode": "404", "error": "Not Found", "message": "missing"},
    )
    result = await run(use_async, recorder, lambda c: c.vectors().get_bucket("nope"))

    assert result is None


@parametrize_clients
async def test_list_buckets_omits_unset_options(use_async: bool) -> None:
    recorder = Recorder(body={"vectorBuckets": [{"vectorBucketName": "a"}]})
    result = await run(use_async, recorder, lambda c: c.vectors().list_buckets())

    assert recorder.last_path == "/storage/v1/vector/ListVectorBuckets"
    assert recorder.last_json == {}
    assert [b.vectorBucketName for b in result.vectorBuckets] == ["a"]
    assert result.nextToken is None


@parametrize_clients
async def test_list_buckets_sends_options(use_async: bool) -> None:
    recorder = Recorder(body={"vectorBuckets": [], "nextToken": "next"})
    result = await run(
        use_async,
        recorder,
        lambda c: c.vectors().list_buckets(
            prefix="emb", max_results=10, next_token="token"
        ),
    )

    assert recorder.last_json == {
        "prefix": "emb",
        "maxResults": 10,
        "nextToken": "token",
    }
    assert result.nextToken == "next"


@parametrize_clients
async def test_list_buckets_raises_storage_api_error(use_async: bool) -> None:
    recorder = Recorder(
        status=500,
        body={
            "statusCode": "500",
            "error": "Internal",
            "message": "boom",
            "code": "InternalError",
        },
    )
    with pytest.raises(StorageApiError) as exc_info:
        await run(use_async, recorder, lambda c: c.vectors().list_buckets())

    assert exc_info.value.message == "boom"
    assert exc_info.value.code == "InternalError"
    assert exc_info.value.status == "500"


@parametrize_clients
async def test_delete_bucket_sends_bucket_name(use_async: bool) -> None:
    recorder = Recorder()
    await run(use_async, recorder, lambda c: c.vectors().delete_bucket("embeddings"))

    assert recorder.last_path == "/storage/v1/vector/DeleteVectorBucket"
    assert recorder.last_json == {"vectorBucketName": "embeddings"}


@parametrize_clients
async def test_create_index_without_metadata(use_async: bool) -> None:
    recorder = Recorder()
    await run(
        use_async,
        recorder,
        lambda c: c.vectors()
        .from_("embeddings")
        .create_index("docs", 3, "cosine", "float32"),
    )

    assert recorder.last_path == "/storage/v1/vector/CreateIndex"
    assert recorder.last_json == {
        "vectorBucketName": "embeddings",
        "indexName": "docs",
        "dimension": 3,
        "distanceMetric": "cosine",
        "dataType": "float32",
    }


@parametrize_clients
async def test_create_index_with_metadata_uses_aliases(use_async: bool) -> None:
    recorder = Recorder()
    metadata = MetadataConfiguration.model_validate(
        {"nonFilterableMetadataKeys": ["body"]}
    )
    await run(
        use_async,
        recorder,
        lambda c: c.vectors()
        .from_("embeddings")
        .create_index("docs", 3, "euclidean", "float32", metadata=metadata),
    )

    assert recorder.last_json["metadataConfiguration"] == {
        "nonFilterableMetadataKeys": ["body"]
    }


@parametrize_clients
async def test_get_index_returns_none_on_api_error(use_async: bool) -> None:
    recorder = Recorder(
        status=404,
        body={"statusCode": 404, "error": "Not Found", "message": "missing"},
    )
    result = await run(
        use_async,
        recorder,
        lambda c: c.vectors().from_("embeddings").get_index("docs"),
    )

    assert recorder.last_json == {"vectorBucketName": "embeddings", "indexName": "docs"}
    assert result is None


@parametrize_clients
async def test_list_indexes_sends_options(use_async: bool) -> None:
    recorder = Recorder(body={"indexes": [{"indexName": "docs"}], "nextToken": "n"})
    result = await run(
        use_async,
        recorder,
        lambda c: c.vectors()
        .from_("embeddings")
        .list_indexes(next_token="t", max_results=5, prefix="d"),
    )

    assert recorder.last_path == "/storage/v1/vector/ListIndexes"
    assert recorder.last_json == {
        "vectorBucketName": "embeddings",
        "nextToken": "t",
        "maxResults": 5,
        "prefix": "d",
    }
    assert [i.indexName for i in result.indexes] == ["docs"]
    assert result.nextToken == "n"


@parametrize_clients
async def test_delete_index_sends_names(use_async: bool) -> None:
    recorder = Recorder()
    await run(
        use_async,
        recorder,
        lambda c: c.vectors().from_("embeddings").delete_index("docs"),
    )

    assert recorder.last_path == "/storage/v1/vector/DeleteIndex"
    assert recorder.last_json == {"vectorBucketName": "embeddings", "indexName": "docs"}


@parametrize_clients
async def test_get_vectors_sends_keys_as_list(use_async: bool) -> None:
    recorder = Recorder(
        body={
            "vectors": [
                {"key": "a", "data": {"float32": [1.0, 2.0]}, "metadata": {"x": 1}}
            ]
        }
    )
    result = await run(
        use_async,
        recorder,
        lambda c: c.vectors()
        .from_("embeddings")
        .index("docs")
        .get("a", "b", return_data=False),
    )

    assert recorder.last_path == "/storage/v1/vector/GetVectors"
    assert recorder.last_json == {
        "vectorBucketName": "embeddings",
        "indexName": "docs",
        "keys": ["a", "b"],
        "returnData": False,
        "returnMetadata": True,
    }
    assert result.vectors[0].data.float32 == [1.0, 2.0]
    assert result.vectors[0].metadata == {"x": 1}


@parametrize_clients
async def test_list_vectors_sends_segments(use_async: bool) -> None:
    recorder = Recorder(body={"vectors": [{"key": "a"}], "nextToken": "n"})
    result = await run(
        use_async,
        recorder,
        lambda c: c.vectors()
        .from_("embeddings")
        .index("docs")
        .list(max_results=2, segment_count=4, segment_index=1),
    )

    assert recorder.last_path == "/storage/v1/vector/ListVectors"
    assert recorder.last_json == {
        "vectorBucketName": "embeddings",
        "indexName": "docs",
        "maxResults": 2,
        "returnData": True,
        "returnMetadata": True,
        "segmentCount": 4,
        "segmentIndex": 1,
    }
    assert result.vectors[0].key == "a"
    assert result.vectors[0].data is None
    assert result.nextToken == "n"


@parametrize_clients
async def test_query_vectors_sends_query_and_parses_distance(use_async: bool) -> None:
    recorder = Recorder(body={"vectors": [{"key": "a", "distance": 0.25}]})
    result = await run(
        use_async,
        recorder,
        lambda c: c.vectors()
        .from_("embeddings")
        .index("docs")
        .query(
            VectorData(float32=[0.1, 0.2]),
            topK=3,
            filter={"category": "news"},
            return_metadata=False,
        ),
    )

    assert recorder.last_path == "/storage/v1/vector/QueryVectors"
    assert recorder.last_json == {
        "vectorBucketName": "embeddings",
        "indexName": "docs",
        "queryVector": {"float32": [0.1, 0.2]},
        "topK": 3,
        "filter": {"category": "news"},
        "returnDistance": True,
        "returnMetadata": False,
    }
    assert result.vectors[0].distance == 0.25


@parametrize_clients
async def test_put_vectors_omits_missing_metadata(use_async: bool) -> None:
    recorder = Recorder()
    vector = VectorObject(key="a", data=VectorData(float32=[1.0]))
    await run(
        use_async,
        recorder,
        lambda c: c.vectors().from_("embeddings").index("docs").put([vector]),
    )

    assert recorder.last_json["vectors"] == [{"key": "a", "data": {"float32": [1.0]}}]


@parametrize_clients
async def test_delete_vectors_sends_keys(use_async: bool) -> None:
    recorder = Recorder()
    keys = [str(i) for i in range(500)]
    await run(
        use_async,
        recorder,
        lambda c: c.vectors().from_("embeddings").index("docs").delete(keys),
    )

    assert recorder.last_path == "/storage/v1/vector/DeleteVectors"
    assert recorder.last_json["keys"] == keys


@parametrize_clients
@pytest.mark.parametrize("count", [0, 501])
async def test_delete_vectors_rejects_invalid_batch_size(
    use_async: bool, count: int
) -> None:
    recorder = Recorder()
    keys = [str(i) for i in range(count)]

    with pytest.raises(VectorBucketException) as exc_info:
        await run(
            use_async,
            recorder,
            lambda c: c.vectors().from_("embeddings").index("docs").delete(keys),
        )

    assert exc_info.value.msg == "Keys batch size must be between 1 and 500."
    assert recorder.requests == []


@parametrize_clients
async def test_analytics_create_bucket(use_async: bool) -> None:
    recorder = Recorder(
        body={
            "name": "warehouse",
            "type": "ANALYTICS",
            "created_at": "2025-01-01T00:00:00Z",
            "updated_at": "2025-01-01T00:00:00Z",
        }
    )
    result = await run(use_async, recorder, lambda c: c.analytics().create("warehouse"))

    assert recorder.requests[-1].method == "POST"
    assert recorder.last_path == "/storage/v1/iceberg/bucket"
    assert recorder.last_json == {"name": "warehouse"}
    assert result.name == "warehouse"
    assert result.type == "ANALYTICS"


@parametrize_clients
async def test_analytics_list_buckets_sends_only_set_params(use_async: bool) -> None:
    recorder = Recorder(
        body=[
            {
                "name": "warehouse",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z",
            }
        ]
    )
    result = await run(
        use_async,
        recorder,
        lambda c: c.analytics().list(limit=10, sort_column="name", sort_order="asc"),
    )

    request = recorder.requests[-1]
    assert request.method == "GET"
    assert recorder.last_path == "/storage/v1/iceberg/bucket"
    assert dict(request.url.params) == {
        "limit": "10",
        "sortColumn": "name",
        "sortOrder": "asc",
    }
    assert [b.name for b in result] == ["warehouse"]


@parametrize_clients
async def test_analytics_delete_bucket(use_async: bool) -> None:
    recorder = Recorder(body={"message": "Successfully deleted"})
    result = await run(use_async, recorder, lambda c: c.analytics().delete("warehouse"))

    assert recorder.requests[-1].method == "DELETE"
    assert recorder.last_path == "/storage/v1/iceberg/bucket/warehouse"
    assert result.message == "Successfully deleted"


@pytest.mark.parametrize("client_class", [SyncStorageClient, AsyncStorageClient])
def test_analytics_catalog_requires_pyiceberg(
    client_class: type[SyncStorageClient] | type[AsyncStorageClient],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setitem(sys.modules, "pyiceberg.catalog.rest", None)
    client = client_class(BASE_URL, {"apiKey": "service-key"})

    with pytest.raises(Exception, match="pyiceberg is required"):
        client.analytics().catalog("warehouse", "id", "secret")


def test_create_client_does_not_emit_deprecation_warning() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("error", DeprecationWarning)
        create_client(BASE_URL, {}, is_async=False)


def test_metadata_configuration_accepts_field_name() -> None:
    metadata = MetadataConfiguration(non_filterable_metadata_keys=["body"])

    assert metadata.non_filterable_metadata_keys == ["body"]
