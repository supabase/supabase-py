from __future__ import annotations

from typing import TYPE_CHECKING
from uuid import uuid4

import pytest

if TYPE_CHECKING:
    from typing import Any, Dict, List

    from supabase import Client


@pytest.fixture(scope="module")
def bucket(supabase: Client) -> str:
    """Creates a test bucket and yields its name, deleting the bucket when ended"""
    bucket_id = f"pytest-{uuid4().hex[:8]}"
    storage_client = supabase.storage()
    storage_client.create_bucket(id=bucket_id)

    yield bucket_id

    storage_client.empty_bucket(bucket_id)
    storage_client.delete_bucket(bucket_id)


@pytest.fixture(scope="module", autouse=True)
def delete_left_buckets(request, supabase: Client):
    """Ensures no test buckets are left"""

    def finalizer(supabase: Client = supabase):
        storage_client = supabase.storage()
        buckets_list = storage_client.list_buckets()
        if not buckets_list:
            return
        test_buckets = [
            bucket.id for bucket in buckets_list if bucket.id.startswith("pytest-")
        ]
        for bucket_id in test_buckets:
            storage_client.empty_bucket(bucket_id)
            storage_client.delete_bucket(bucket_id)

    request.addfinalizer(finalizer)


@pytest.fixture
def folder() -> str:
    return uuid4().hex[:8]


def test_client_upload_file(supabase: Client, bucket: str, folder: str) -> None:
    """Ensure we can upload files to a bucket"""
    storage = supabase.storage()
    storage_file = storage.StorageFileAPI(bucket)

    file_name = "test_image.svg"
    file_path = f"tests/{file_name}"
    bucket_file_path = f"{folder}/{file_name}"
    mime_type = "image/svg+xml"
    options = {"content-type": mime_type}

    storage_file.upload(bucket_file_path, file_path, options)
    files: List[Dict[str, Any]] = storage_file.list(folder)
    image_info = None
    for item in files:
        if item.get("name") == file_name:
            image_info = item
            break

    assert files
    assert image_info is not None
    assert image_info.get("metadata", {}).get("mimetype") == mime_type
