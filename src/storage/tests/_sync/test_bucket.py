from unittest.mock import Mock

import pytest
from httpx import Client, Headers, HTTPStatusError, Response

from storage3 import SyncBucket, SyncStorageBucketAPI
from storage3.exceptions import StorageApiError
from storage3.types import CreateOrUpdateBucketOptions

from ..test_client import valid_url


@pytest.fixture
def mock_client():
    return Mock()


@pytest.fixture
def headers() -> Headers:
    return Headers()


@pytest.fixture
def storage_api(mock_client: Client, headers: Headers) -> SyncStorageBucketAPI:
    return SyncStorageBucketAPI(mock_client, "", headers)


@pytest.fixture
def mock_response():
    response = Mock(spec=Response)
    response.raise_for_status = Mock()
    return response


def test_list_buckets(storage_api, mock_client, mock_response):
    # Mock response data
    mock_response.json.return_value = [
        {
            "id": "bucket1",
            "name": "Bucket 1",
            "public": True,
            "owner": "test-owner",
            "created_at": "2024-01-01",
            "updated_at": "2024-01-01",
            "file_size_limit": 1000000,
            "allowed_mime_types": ["image/*"],
        },
        {
            "id": "bucket2",
            "name": "Bucket 2",
            "public": True,
            "owner": "test-owner",
            "created_at": "2024-01-01",
            "updated_at": "2024-01-01",
            "file_size_limit": 1000000,
            "allowed_mime_types": ["image/*"],
        },
    ]
    mock_client.request.return_value = mock_response

    buckets = storage_api.list_buckets()

    assert len(buckets) == 2
    assert all(isinstance(bucket, SyncBucket) for bucket in buckets)
    assert buckets[0].id == "bucket1"
    assert buckets[1].id == "bucket2"

    mock_client.request.assert_called_once_with("GET", "bucket", json=None, headers={})


def test_get_bucket(storage_api, mock_client, mock_response):
    bucket_id = "test-bucket"
    mock_response.json.return_value = {
        "id": bucket_id,
        "name": "Test Bucket",
        "public": True,
        "owner": "test-owner",
        "created_at": "2024-01-01",
        "updated_at": "2024-01-01",
        "file_size_limit": 1000000,
        "allowed_mime_types": ["image/*"],
    }
    mock_client.request.return_value = mock_response

    bucket = storage_api.get_bucket(bucket_id)

    assert isinstance(bucket, SyncBucket)
    assert bucket.id == bucket_id
    assert bucket.name == "Test Bucket"
    assert bucket.public is True
    assert bucket.owner == "test-owner"

    mock_client.request.assert_called_once_with(
        "GET", f"bucket/{bucket_id}", json=None, headers={}
    )


def test_create_bucket(storage_api, mock_client, mock_response):
    bucket_id = "new-bucket"
    bucket_name = "New Bucket"
    options = CreateOrUpdateBucketOptions(
        public=True, file_size_limit=1000000, allowed_mime_types=["image/*"]
    )

    mock_response.json.return_value = {"message": "Bucket created successfully"}
    mock_client.request.return_value = mock_response

    result = storage_api.create_bucket(bucket_id, bucket_name, options)

    assert result == {"message": "Bucket created successfully"}
    mock_client.request.assert_called_once_with(
        "POST",
        "bucket",
        json={
            "id": bucket_id,
            "name": bucket_name,
            "public": True,
            "file_size_limit": 1000000,
            "allowed_mime_types": ["image/*"],
        },
        headers={},
    )


def test_create_bucket_minimal(storage_api, mock_client, mock_response):
    bucket_id = "minimal-bucket"
    mock_response.json.return_value = {"message": "Bucket created successfully"}
    mock_client.request.return_value = mock_response

    result = storage_api.create_bucket(bucket_id)

    assert result == {"message": "Bucket created successfully"}
    mock_client.request.assert_called_once_with(
        "POST", "bucket", json={"id": bucket_id, "name": bucket_id}, headers={}
    )


def test_update_bucket(storage_api, mock_client, mock_response):
    bucket_id = "update-bucket"
    options = CreateOrUpdateBucketOptions(public=False, file_size_limit=2000000)

    mock_response.json.return_value = {"message": "Bucket updated successfully"}
    mock_client.request.return_value = mock_response

    result = storage_api.update_bucket(bucket_id, options)

    assert result == {"message": "Bucket updated successfully"}
    mock_client.request.assert_called_once_with(
        "PUT",
        f"bucket/{bucket_id}",
        json={
            "id": bucket_id,
            "name": bucket_id,
            "public": False,
            "file_size_limit": 2000000,
        },
        headers={},
    )


def test_empty_bucket(storage_api, mock_client, mock_response):
    bucket_id = "empty-bucket"
    mock_response.json.return_value = {"message": "Bucket emptied successfully"}
    mock_client.request.return_value = mock_response

    result = storage_api.empty_bucket(bucket_id)

    assert result == {"message": "Bucket emptied successfully"}
    mock_client.request.assert_called_once_with(
        "POST", f"bucket/{bucket_id}/empty", json={}, headers={}
    )


def test_delete_bucket(storage_api, mock_client, mock_response):
    bucket_id = "delete-bucket"
    mock_response.json.return_value = {"message": "Bucket deleted successfully"}
    mock_client.request.return_value = mock_response

    result = storage_api.delete_bucket(bucket_id)

    assert result == {"message": "Bucket deleted successfully"}
    mock_client.request.assert_called_once_with(
        "DELETE", f"bucket/{bucket_id}", json={}, headers={}
    )


def test_request_error_handling(storage_api, mock_client):
    error_response = Mock(spec=Response)
    error_response.json.return_value = {
        "message": "Test error message",
        "error": "Test error",
        "statusCode": 400,
    }

    exc = HTTPStatusError("HTTP Error", request=Mock(), response=error_response)
    mock_client.request.side_effect = exc

    with pytest.raises(StorageApiError) as exc_info:
        storage_api._request("GET", ["test"])

    assert exc_info.value.message == "Test error message"


@pytest.mark.parametrize(
    "method,path,json_data",
    [
        ("GET", "test", None),
        ("POST", "test", {"key": "value"}),
        ("PUT", "test", {"id": "123"}),
        ("DELETE", "test", {}),
    ],
)
def test_request_methods(
    storage_api, mock_client, mock_response, method, path, json_data
):
    mock_client.request.return_value = mock_response
    storage_api._request(method, [path], json_data)
    mock_client.request.assert_called_once_with(
        method, path, json=json_data, headers={}
    )
