from unittest.mock import Mock

import pytest
from httpx import Client, Response
from storage3 import SyncStorageClient
from storage3.types import Bucket, MessageResponse


@pytest.fixture
def mock_client() -> Mock:
    return Mock()


@pytest.fixture
def headers() -> dict[str, str]:
    return {}


@pytest.fixture
def storage_api(mock_client: Client, headers: dict[str, str]) -> SyncStorageClient:
    return SyncStorageClient(http_client=mock_client, url="", headers=headers)


@pytest.fixture
def mock_response() -> Mock:
    response = Mock(spec=Response)
    response.raise_for_status = Mock()
    return response


def test_list_buckets(
    storage_api: SyncStorageClient, mock_client: Mock, mock_response: Mock
) -> None:
    # Mock response data
    mock_response.content = b"""[
        {
            "id": "bucket1",
            "name": "Bucket 1",
            "public": true,
            "owner": "test-owner",
            "created_at": "2024-01-01",
            "updated_at": "2024-01-01",
            "file_size_limit": 1000000,
            "allowed_mime_types": ["image/*"]
        },
        {
            "id": "bucket2",
            "name": "Bucket 2",
            "public": true,
            "owner": "test-owner",
            "created_at": "2024-01-01",
            "updated_at": "2024-01-01",
            "file_size_limit": 1000000,
            "allowed_mime_types": ["image/*"]
        }
    ]
    """
    mock_client.send.return_value = mock_response

    buckets = storage_api.list_buckets()

    assert len(buckets) == 2
    assert all(isinstance(bucket, Bucket) for bucket in buckets)
    assert buckets[0].id == "bucket1"
    assert buckets[1].id == "bucket2"

    mock_client.send.assert_called_once()


def test_get_bucket(storage_api, mock_client, mock_response) -> None:
    bucket_id = "test-bucket"
    mock_response.content = f'''{{
        "id": "{bucket_id}",
        "name": "Test Bucket",
        "public": true,
        "owner": "test-owner",
        "created_at": "2024-01-01",
        "updated_at": "2024-01-01",
        "file_size_limit": 1000000,
        "allowed_mime_types": ["image/*"]
    }}'''.encode()
    mock_client.send.return_value = mock_response

    bucket = storage_api.get_bucket(bucket_id)

    assert isinstance(bucket, Bucket)
    assert bucket.id == bucket_id
    assert bucket.name == "Test Bucket"
    assert bucket.public is True
    assert bucket.owner == "test-owner"

    mock_client.send.assert_called_once()


def test_create_bucket(storage_api, mock_client, mock_response) -> None:
    bucket_id = "new-bucket"
    bucket_name = "New Bucket"

    mock_response.content = f'{{"name": "{bucket_name}"}}'.encode()
    mock_client.send.return_value = mock_response

    result = storage_api.create_bucket(
        bucket_id,
        bucket_name,
        public=True,
        file_size_limit=1000000,
        allowed_mime_types=["image/*"],
    )

    assert result.name == bucket_name
    mock_client.send.assert_called_once()


def test_create_bucket_minimal(storage_api, mock_client, mock_response) -> None:
    bucket_id = "minimal-bucket"
    mock_response.content = f'{{"name": "{bucket_id}"}}'
    mock_client.send.return_value = mock_response

    result = storage_api.create_bucket(bucket_id)

    assert result.name == bucket_id
    mock_client.send.assert_called_once()


def test_update_bucket(storage_api, mock_client, mock_response) -> None:
    bucket_id = "update-bucket"

    mock_response.content = b'{"message": "Bucket updated successfully"}'
    mock_client.send.return_value = mock_response

    result = storage_api.update_bucket(bucket_id, public=False, file_size_limit=2000000)

    assert result == MessageResponse(message="Bucket updated successfully")
    mock_client.send.assert_called_once()


def test_empty_bucket(storage_api, mock_client, mock_response) -> None:
    bucket_id = "empty-bucket"
    mock_response.content = b'{"message": "Bucket emptied successfully"}'
    mock_client.send.return_value = mock_response

    result = storage_api.empty_bucket(bucket_id)

    assert result == MessageResponse(message="Bucket emptied successfully")
    mock_client.send.assert_called_once()


def test_delete_bucket(storage_api, mock_client, mock_response) -> None:
    bucket_id = "delete-bucket"
    mock_response.content = b'{"message": "Bucket deleted successfully"}'
    mock_client.send.return_value = mock_response

    result = storage_api.delete_bucket(bucket_id)

    assert result == MessageResponse(message="Bucket deleted successfully")
    mock_client.send.assert_called_once()
