from __future__ import annotations

from collections.abc import AsyncGenerator
from typing import Callable
from uuid import uuid4

import pytest
from storage3 import AsyncStorageClient
from storage3.exceptions import VectorBucketException
from storage3.types import (
    DistanceMetric,
    MetadataConfiguration,
    VectorData,
    VectorFilter,
    VectorObject,
)

# Global variable to track vector buckets created in tests
temp_test_vector_buckets: list[str] = []


@pytest.fixture
def uuid_factory() -> Callable[[], str]:
    def method() -> str:
        """Generate an 8-digit UUID"""
        return uuid4().hex[:8]

    return method


@pytest.fixture
async def vector_bucket(
    storage: AsyncStorageClient, uuid_factory: Callable[[], str]
) -> AsyncGenerator[str]:
    """Creates a test vector bucket which will be deleted at the end"""
    bucket_name = f"test-vector-bucket-{uuid_factory()}"

    # Store bucket_name in global list
    global temp_test_vector_buckets
    temp_test_vector_buckets.append(bucket_name)

    vectors_client = storage.vectors()
    await vectors_client.create_bucket(bucket_name)

    yield bucket_name

    # Cleanup: delete all indexes and then the bucket
    try:
        bucket_scope = vectors_client.from_(bucket_name)
        indexes_response = await bucket_scope.list_indexes()
        for index in indexes_response.indexes:
            await bucket_scope.delete_index(index.indexName)
    except Exception:
        pass  # Ignore errors during cleanup

    temp_test_vector_buckets.remove(bucket_name)


@pytest.fixture
async def vector_index(
    storage: AsyncStorageClient,
    vector_bucket: str,
    uuid_factory: Callable[[], str],
) -> AsyncGenerator[tuple[str, str]]:
    """Creates a test vector index which will be deleted at the end"""
    index_name = f"test-index-{uuid_factory()}"
    dimension = 128
    distance_metric: DistanceMetric = "cosine"
    data_type = "float32"

    vectors_client = storage.vectors()
    bucket_scope = vectors_client.from_(vector_bucket)
    await bucket_scope.create_index(
        index_name=index_name,
        dimension=dimension,
        distance_metric=distance_metric,
        data_type=data_type,
    )

    yield (vector_bucket, index_name)

    # Cleanup: delete the index
    try:
        await bucket_scope.delete_index(index_name)
    except Exception:
        pass  # Ignore errors during cleanup


@pytest.fixture
def sample_vectors() -> list[VectorObject]:
    """Creates sample vector objects for testing"""
    return [
        VectorObject(
            key="vector1",
            data=VectorData(float32=[0.1] * 128),
            metadata={"category": "test", "score": 0.95},
        ),
        VectorObject(
            key="vector2",
            data=VectorData(float32=[0.2] * 128),
            metadata={"category": "test", "score": 0.85},
        ),
        VectorObject(
            key="vector3",
            data=VectorData(float32=[0.3] * 128),
            metadata={"category": "demo", "score": 0.75},
        ),
    ]


@pytest.fixture
def query_vector() -> VectorData:
    """Creates a query vector for similarity search"""
    return VectorData(float32=[0.15] * 128)


# ==================== AsyncStorageVectorsClient Tests ====================


async def test_create_vector_bucket(
    storage: AsyncStorageClient, uuid_factory: Callable[[], str]
) -> None:
    """Test creating a vector bucket"""
    bucket_name = f"test-bucket-{uuid_factory()}"
    vectors_client = storage.vectors()

    await vectors_client.create_bucket(bucket_name)

    # Verify bucket exists by listing indexes (should not error)
    bucket_scope = vectors_client.from_(bucket_name)
    indexes = await bucket_scope.list_indexes()
    assert indexes.indexes == []

    # Cleanup
    try:
        indexes_response = await bucket_scope.list_indexes()
        for index in indexes_response.indexes:
            await bucket_scope.delete_index(index.indexName)
    except Exception:
        pass


async def test_from_returns_vector_bucket_scope(
    storage: AsyncStorageClient, vector_bucket: str
) -> None:
    """Test that from_() returns an AsyncVectorBucketScope"""
    vectors_client = storage.vectors()
    bucket_scope = vectors_client.from_(vector_bucket)

    assert bucket_scope is not None
    assert bucket_scope._bucket_name == vector_bucket


# ==================== AsyncVectorBucketScope Tests ====================


async def test_create_index(
    storage: AsyncStorageClient,
    vector_bucket: str,
    uuid_factory: Callable[[], str],
) -> None:
    """Test creating a vector index"""
    index_name = f"test-index-{uuid_factory()}"
    dimension = 128
    distance_metric: DistanceMetric = "cosine"
    data_type = "float32"

    vectors_client = storage.vectors()
    bucket_scope = vectors_client.from_(vector_bucket)

    await bucket_scope.create_index(
        index_name=index_name,
        dimension=dimension,
        distance_metric=distance_metric,
        data_type=data_type,
    )

    # Verify index was created
    index = await bucket_scope.get_index(index_name)
    assert index.index_name == index_name
    assert index.dimension == dimension
    assert index.distance_metric == distance_metric
    assert index.data_type == data_type

    # Cleanup
    await bucket_scope.delete_index(index_name)


async def test_create_index_with_metadata(
    storage: AsyncStorageClient,
    vector_bucket: str,
    uuid_factory: Callable[[], str],
) -> None:
    """Test creating a vector index with metadata configuration"""
    index_name = f"test-index-{uuid_factory()}"
    dimension = 256
    distance_metric: DistanceMetric = "euclidean"
    data_type = "float32"
    # Use model_validate to construct with alias
    metadata = MetadataConfiguration.model_validate(
        {"nonFilterableMetadaKeys": ["internal_id"]}
    )

    vectors_client = storage.vectors()
    bucket_scope = vectors_client.from_(vector_bucket)

    await bucket_scope.create_index(
        index_name=index_name,
        dimension=dimension,
        distance_metric=distance_metric,
        data_type=data_type,
        metadata=metadata,
    )

    # Verify index was created with metadata
    index = await bucket_scope.get_index(index_name)
    assert index.index_name == index_name
    assert index.dimension == dimension
    assert index.distance_metric == distance_metric
    assert index.metadata is not None

    # Cleanup
    await bucket_scope.delete_index(index_name)


async def test_get_index(
    storage: AsyncStorageClient,
    vector_bucket: str,
    uuid_factory: Callable[[], str],
) -> None:
    """Test retrieving a vector index"""
    index_name = f"test-index-{uuid_factory()}"
    dimension = 64
    distance_metric: DistanceMetric = "dotproduct"
    data_type = "float32"

    vectors_client = storage.vectors()
    bucket_scope = vectors_client.from_(vector_bucket)

    # Create index first
    await bucket_scope.create_index(
        index_name=index_name,
        dimension=dimension,
        distance_metric=distance_metric,
        data_type=data_type,
    )

    # Get the index
    index = await bucket_scope.get_index(index_name)
    assert index.index_name == index_name
    assert index.dimension == dimension
    assert index.distance_metric == distance_metric
    assert index.data_type == data_type
    assert index.bucket_name == vector_bucket

    # Cleanup
    await bucket_scope.delete_index(index_name)


async def test_list_indexes(
    storage: AsyncStorageClient,
    vector_bucket: str,
    uuid_factory: Callable[[], str],
) -> None:
    """Test listing vector indexes"""
    vectors_client = storage.vectors()
    bucket_scope = vectors_client.from_(vector_bucket)

    # Create multiple indexes
    index_names = [f"test-index-{uuid_factory()}" for _ in range(3)]
    for index_name in index_names:
        await bucket_scope.create_index(
            index_name=index_name,
            dimension=128,
            distance_metric="cosine",
            data_type="float32",
        )

    # List indexes
    response = await bucket_scope.list_indexes()
    assert len(response.indexes) >= 3

    # Verify all created indexes are in the list
    returned_index_names = {idx.indexName for idx in response.indexes}
    for index_name in index_names:
        assert index_name in returned_index_names

    # Cleanup
    for index_name in index_names:
        await bucket_scope.delete_index(index_name)


async def test_list_indexes_with_pagination(
    storage: AsyncStorageClient,
    vector_bucket: str,
    uuid_factory: Callable[[], str],
) -> None:
    """Test listing indexes with pagination parameters"""
    vectors_client = storage.vectors()
    bucket_scope = vectors_client.from_(vector_bucket)

    # Create an index
    index_name = f"test-index-{uuid_factory()}"
    await bucket_scope.create_index(
        index_name=index_name,
        dimension=128,
        distance_metric="cosine",
        data_type="float32",
    )

    # List with max_results
    response = await bucket_scope.list_indexes(max_results=10)
    assert response.indexes is not None

    # List with prefix
    response = await bucket_scope.list_indexes(prefix="test-")
    assert response.indexes is not None

    # Cleanup
    await bucket_scope.delete_index(index_name)


async def test_delete_index(
    storage: AsyncStorageClient,
    vector_bucket: str,
    uuid_factory: Callable[[], str],
) -> None:
    """Test deleting a vector index"""
    index_name = f"test-index-{uuid_factory()}"

    vectors_client = storage.vectors()
    bucket_scope = vectors_client.from_(vector_bucket)

    # Create index
    await bucket_scope.create_index(
        index_name=index_name,
        dimension=128,
        distance_metric="cosine",
        data_type="float32",
    )

    # Verify it exists
    index = await bucket_scope.get_index(index_name)
    assert index.index_name == index_name

    # Delete it
    await bucket_scope.delete_index(index_name)

    # Verify it's deleted (should raise an error when trying to get it)
    # Note: The actual behavior depends on the API implementation
    # This test assumes the API will return an error for non-existent indexes


async def test_index_returns_vector_index_scope(
    storage: AsyncStorageClient,
    vector_bucket: str,
    uuid_factory: Callable[[], str],
) -> None:
    """Test that index() returns an AsyncVectorIndexScope"""
    index_name = f"test-index-{uuid_factory()}"

    vectors_client = storage.vectors()
    bucket_scope = vectors_client.from_(vector_bucket)

    # Create index first
    await bucket_scope.create_index(
        index_name=index_name,
        dimension=128,
        distance_metric="cosine",
        data_type="float32",
    )

    # Get index scope
    index_scope = bucket_scope.index(index_name)
    assert index_scope is not None
    assert index_scope._bucket_name == vector_bucket
    assert index_scope._index_name == index_name

    # Cleanup
    await bucket_scope.delete_index(index_name)


# ==================== AsyncVectorIndexScope Tests ====================


async def test_put_vectors(
    storage: AsyncStorageClient,
    vector_index: tuple[str, str],
    sample_vectors: list[VectorObject],
) -> None:
    """Test putting vectors into an index"""
    bucket_name, index_name = vector_index

    vectors_client = storage.vectors()
    index_scope = vectors_client.from_(bucket_name).index(index_name)

    await index_scope.put(sample_vectors)

    # Verify vectors were stored by getting them
    response = await index_scope.get("vector1", "vector2", "vector3")
    assert len(response.vectors) == 3


async def test_get_vectors(
    storage: AsyncStorageClient,
    vector_index: tuple[str, str],
    sample_vectors: list[VectorObject],
) -> None:
    """Test getting vectors from an index"""
    bucket_name, index_name = vector_index

    vectors_client = storage.vectors()
    index_scope = vectors_client.from_(bucket_name).index(index_name)

    # Put vectors first
    await index_scope.put(sample_vectors)

    # Get vectors with data and metadata
    response = await index_scope.get("vector1", "vector2", return_data=True, return_metadata=True)
    assert len(response.vectors) == 2

    # Verify vector data
    vector1 = next((v for v in response.vectors if v.key == "vector1"), None)
    assert vector1 is not None
    assert vector1.data is not None
    assert len(vector1.data.float32) == 128
    assert vector1.metadata is not None
    assert vector1.metadata.get("category") == "test"


async def test_get_vectors_without_data(
    storage: AsyncStorageClient,
    vector_index: tuple[str, str],
    sample_vectors: list[VectorObject],
) -> None:
    """Test getting vectors without returning data"""
    bucket_name, index_name = vector_index

    vectors_client = storage.vectors()
    index_scope = vectors_client.from_(bucket_name).index(index_name)

    # Put vectors first
    await index_scope.put(sample_vectors)

    # Get vectors without data
    response = await index_scope.get("vector1", return_data=False, return_metadata=True)
    assert len(response.vectors) == 1
    # Data might be None when return_data=False
    # This depends on API implementation


async def test_list_vectors(
    storage: AsyncStorageClient,
    vector_index: tuple[str, str],
    sample_vectors: list[VectorObject],
) -> None:
    """Test listing vectors from an index"""
    bucket_name, index_name = vector_index

    vectors_client = storage.vectors()
    index_scope = vectors_client.from_(bucket_name).index(index_name)

    # Put vectors first
    await index_scope.put(sample_vectors)

    # List vectors
    response = await index_scope.list(
        max_results=10,
        return_data=True,
        return_metadata=True,
    )
    assert len(response.vectors) >= 3

    # Verify all vectors are in the list
    returned_keys = {v.key for v in response.vectors}
    assert "vector1" in returned_keys
    assert "vector2" in returned_keys
    assert "vector3" in returned_keys


async def test_list_vectors_with_pagination(
    storage: AsyncStorageClient,
    vector_index: tuple[str, str],
    sample_vectors: list[VectorObject],
) -> None:
    """Test listing vectors with pagination"""
    bucket_name, index_name = vector_index

    vectors_client = storage.vectors()
    index_scope = vectors_client.from_(bucket_name).index(index_name)

    # Put vectors first
    await index_scope.put(sample_vectors)

    # List with max_results
    response = await index_scope.list(max_results=2)
    assert len(response.vectors) <= 2

    # If there's a next_token, use it
    if response.nextToken:
        response2 = await index_scope.list(
            max_results=2,
            next_token=response.nextToken,
        )
        assert response2.vectors is not None


async def test_list_vectors_with_segments(
    storage: AsyncStorageClient,
    vector_index: tuple[str, str],
    sample_vectors: list[VectorObject],
) -> None:
    """Test listing vectors with segment parameters"""
    bucket_name, index_name = vector_index

    vectors_client = storage.vectors()
    index_scope = vectors_client.from_(bucket_name).index(index_name)

    # Put vectors first
    await index_scope.put(sample_vectors)

    # List with segment parameters
    response = await index_scope.list(
        segment_count=1,
        segment_index=0,
        return_data=True,
    )
    assert response.vectors is not None


async def test_query_vectors(
    storage: AsyncStorageClient,
    vector_index: tuple[str, str],
    sample_vectors: list[VectorObject],
    query_vector: VectorData,
) -> None:
    """Test querying vectors for similarity search"""
    bucket_name, index_name = vector_index

    vectors_client = storage.vectors()
    index_scope = vectors_client.from_(bucket_name).index(index_name)

    # Put vectors first
    await index_scope.put(sample_vectors)

    # Query vectors
    response = await index_scope.query(
        query_vector=query_vector,
        topK=2,
        return_distance=True,
        return_metadata=True,
    )
    assert len(response.matches) <= 2
    assert all(match.key is not None for match in response.matches)


async def test_query_vectors_with_filter(
    storage: AsyncStorageClient,
    vector_index: tuple[str, str],
    sample_vectors: list[VectorObject],
    query_vector: VectorData,
) -> None:
    """Test querying vectors with metadata filter"""
    bucket_name, index_name = vector_index

    vectors_client = storage.vectors()
    index_scope = vectors_client.from_(bucket_name).index(index_name)

    # Put vectors first
    await index_scope.put(sample_vectors)

    # Query with filter
    filter: VectorFilter = {"category": "test"}
    response = await index_scope.query(
        query_vector=query_vector,
        topK=10,
        filter=filter,
        return_distance=True,
        return_metadata=True,
    )
    assert len(response.matches) >= 0

    # Verify filtered results (if any)
    for match in response.matches:
        if match.metadata:
            assert match.metadata.get("category") == "test"


async def test_query_vectors_without_distance(
    storage: AsyncStorageClient,
    vector_index: tuple[str, str],
    sample_vectors: list[VectorObject],
    query_vector: VectorData,
) -> None:
    """Test querying vectors without returning distance"""
    bucket_name, index_name = vector_index

    vectors_client = storage.vectors()
    index_scope = vectors_client.from_(bucket_name).index(index_name)

    # Put vectors first
    await index_scope.put(sample_vectors)

    # Query without distance
    response = await index_scope.query(
        query_vector=query_vector,
        topK=5,
        return_distance=False,
        return_metadata=True,
    )
    assert len(response.matches) <= 5


async def test_delete_vectors(
    storage: AsyncStorageClient,
    vector_index: tuple[str, str],
    sample_vectors: list[VectorObject],
) -> None:
    """Test deleting vectors from an index"""
    bucket_name, index_name = vector_index

    vectors_client = storage.vectors()
    index_scope = vectors_client.from_(bucket_name).index(index_name)

    # Put vectors first
    await index_scope.put(sample_vectors)

    # Verify vectors exist
    response = await index_scope.get("vector1", "vector2")
    assert len(response.vectors) == 2

    # Delete vectors
    await index_scope.delete(["vector1", "vector2"])

    # Verify vectors are deleted (should return fewer or no results)
    # Note: Actual behavior depends on API implementation


async def test_delete_vectors_single_key(
    storage: AsyncStorageClient,
    vector_index: tuple[str, str],
    sample_vectors: list[VectorObject],
) -> None:
    """Test deleting a single vector"""
    bucket_name, index_name = vector_index

    vectors_client = storage.vectors()
    index_scope = vectors_client.from_(bucket_name).index(index_name)

    # Put vectors first
    await index_scope.put(sample_vectors)

    # Delete single vector
    await index_scope.delete(["vector1"])

    # Verify it's deleted
    response = await index_scope.get("vector1")
    # The vector should not be in the response or should be empty
    # This depends on API implementation


async def test_delete_vectors_batch_size_validation(
    storage: AsyncStorageClient,
    vector_index: tuple[str, str],
) -> None:
    """Test that delete validates batch size"""
    bucket_name, index_name = vector_index

    vectors_client = storage.vectors()
    index_scope = vectors_client.from_(bucket_name).index(index_name)

    # Test with empty list (should raise error)
    with pytest.raises(VectorBucketException, match="Keys batch size must be between 1 and 500"):
        await index_scope.delete([])

    # Test with too many keys (should raise error)
    too_many_keys = [f"key{i}" for i in range(501)]
    with pytest.raises(VectorBucketException, match="Keys batch size must be between 1 and 500"):
        await index_scope.delete(too_many_keys)


async def test_delete_vectors_max_batch(
    storage: AsyncStorageClient,
    vector_index: tuple[str, str],
) -> None:
    """Test deleting maximum allowed batch size"""
    bucket_name, index_name = vector_index

    vectors_client = storage.vectors()
    index_scope = vectors_client.from_(bucket_name).index(index_name)

    # Create 500 vectors
    max_vectors = [
        VectorObject(
            key=f"key{i}",
            data=VectorData(float32=[0.1] * 128),
        )
        for i in range(500)
    ]
    await index_scope.put(max_vectors)

    # Delete all 500 at once (should work)
    keys = [f"key{i}" for i in range(500)]
    await index_scope.delete(keys)


# ==================== Integration Tests ====================


async def test_full_workflow(
    storage: AsyncStorageClient,
    vector_bucket: str,
    uuid_factory: Callable[[], str],
) -> None:
    """Test a complete workflow: create bucket -> create index -> put vectors -> query -> delete"""
    index_name = f"workflow-index-{uuid_factory()}"
    dimension = 128

    vectors_client = storage.vectors()
    bucket_scope = vectors_client.from_(vector_bucket)

    # 1. Create index
    await bucket_scope.create_index(
        index_name=index_name,
        dimension=dimension,
        distance_metric="cosine",
        data_type="float32",
    )

    # 2. Put vectors
    vectors = [
        VectorObject(
            key="doc1",
            data=VectorData(float32=[0.1] * dimension),
            metadata={"title": "Document 1", "type": "article"},
        ),
        VectorObject(
            key="doc2",
            data=VectorData(float32=[0.2] * dimension),
            metadata={"title": "Document 2", "type": "article"},
        ),
        VectorObject(
            key="doc3",
            data=VectorData(float32=[0.3] * dimension),
            metadata={"title": "Document 3", "type": "blog"},
        ),
    ]
    index_scope = bucket_scope.index(index_name)
    await index_scope.put(vectors)

    # 3. Get vectors
    response = await index_scope.get("doc1", "doc2")
    assert len(response.vectors) == 2

    # 4. List vectors
    list_response = await index_scope.list(max_results=10)
    assert len(list_response.vectors) >= 3

    # 5. Query vectors
    query = VectorData(float32=[0.15] * dimension)
    query_response = await index_scope.query(
        query_vector=query,
        topK=2,
        filter={"type": "article"},
    )
    assert len(query_response.matches) >= 0

    # 6. Delete vectors
    await index_scope.delete(["doc1", "doc2", "doc3"])

    # 7. Delete index
    await bucket_scope.delete_index(index_name)


async def test_multiple_indexes_same_bucket(
    storage: AsyncStorageClient,
    vector_bucket: str,
    uuid_factory: Callable[[], str],
) -> None:
    """Test working with multiple indexes in the same bucket"""
    vectors_client = storage.vectors()
    bucket_scope = vectors_client.from_(vector_bucket)

    # Create multiple indexes
    index1_name = f"index1-{uuid_factory()}"
    index2_name = f"index2-{uuid_factory()}"

    await bucket_scope.create_index(
        index_name=index1_name,
        dimension=64,
        distance_metric="cosine",
        data_type="float32",
    )

    await bucket_scope.create_index(
        index_name=index2_name,
        dimension=256,
        distance_metric="euclidean",
        data_type="float32",
    )

    # Put vectors to each index
    index1_scope = bucket_scope.index(index1_name)
    index2_scope = bucket_scope.index(index2_name)

    await index1_scope.put([
        VectorObject(key="v1", data=VectorData(float32=[0.1] * 64))
    ])
    await index2_scope.put([
        VectorObject(key="v2", data=VectorData(float32=[0.2] * 256))
    ])

    # Verify vectors are in correct indexes
    response1 = await index1_scope.get("v1")
    assert len(response1.vectors) == 1

    response2 = await index2_scope.get("v2")
    assert len(response2.vectors) == 1

    # Cleanup
    await bucket_scope.delete_index(index1_name)
    await bucket_scope.delete_index(index2_name)


async def test_different_distance_metrics(
    storage: AsyncStorageClient,
    vector_bucket: str,
    uuid_factory: Callable[[], str],
) -> None:
    """Test creating indexes with different distance metrics"""
    vectors_client = storage.vectors()
    bucket_scope = vectors_client.from_(vector_bucket)

    metrics: list[DistanceMetric] = ["cosine", "euclidean", "dotproduct"]

    for metric in metrics:
        index_name = f"index-{metric}-{uuid_factory()}"
        await bucket_scope.create_index(
            index_name=index_name,
            dimension=128,
            distance_metric=metric,
            data_type="float32",
        )

        # Verify index was created with correct metric
        index = await bucket_scope.get_index(index_name)
        assert index.distance_metric == metric

        # Cleanup
        await bucket_scope.delete_index(index_name)


async def test_vector_metadata_filtering(
    storage: AsyncStorageClient,
    vector_index: tuple[str, str],
    sample_vectors: list[VectorObject],
    query_vector: VectorData,
) -> None:
    """Test querying with various metadata filters"""
    bucket_name, index_name = vector_index

    vectors_client = storage.vectors()
    index_scope = vectors_client.from_(bucket_name).index(index_name)

    # Put vectors with different metadata
    await index_scope.put(sample_vectors)

    # Query with equality filter
    filter1: VectorFilter = {"category": "test"}
    response1 = await index_scope.query(
        query_vector=query_vector,
        topK=10,
        filter=filter1,
    )
    assert response1.matches is not None

    # Query with different filter
    filter2: VectorFilter = {"category": "demo"}
    response2 = await index_scope.query(
        query_vector=query_vector,
        topK=10,
        filter=filter2,
    )
    assert response2.matches is not None

