from __future__ import annotations
from pathlib import Path

from typing import TYPE_CHECKING
from uuid import uuid4

import pytest

if TYPE_CHECKING:
    from typing import Any, Dict, List

    from supabase import Client


@pytest.fixture(scope="module", autouse=True)
def delete_left_buckets(request, supabase: Client):
    """Ensures no test buckets are left"""

    def finalizer(supabase: Client = supabase):
        storage_client = supabase.storage()
        for bucket in storage_client.list_buckets():
            if bucket.id.startswith("pytest-"):
                storage_client.empty_bucket(bucket.id)
                storage_client.delete_bucket(bucket.id)

    request.addfinalizer(finalizer)


@pytest.fixture(scope="module")
def bucket(supabase: Client) -> str:
    """Creates a test bucket which will be used in the whole storage tests run and deleted at the end"""
    bucket_id = f"pytest-{uuid4().hex[:8]}"
    storage_client = supabase.storage()
    storage_client.create_bucket(id=bucket_id)

    yield bucket_id

    storage_client.empty_bucket(bucket_id)
    storage_client.delete_bucket(bucket_id)


@pytest.fixture
def file(tmp_path: Path) -> Dict[str, str]:
    """Creates a different test file (same content but different path) for each test"""
    file_name = "test_image.svg"
    file_content = (
        b'<svg width="109" height="113" viewBox="0 0 109 113" fill="none" xmlns="http://www.w3.org/2000/svg"> '
        b'<path d="M63.7076 110.284C60.8481 113.885 55.0502 111.912 54.9813 107.314L53.9738 40.0627L99.1935 '
        b'40.0627C107.384 40.0627 111.952 49.5228 106.859 55.9374L63.7076 110.284Z" fill="url(#paint0_linear)"/> '
        b'<path d="M63.7076 110.284C60.8481 113.885 55.0502 111.912 54.9813 107.314L53.9738 40.0627L99.1935 '
        b'40.0627C107.384 40.0627 111.952 49.5228 106.859 55.9374L63.7076 110.284Z" fill="url(#paint1_linear)" '
        b'fill-opacity="0.2"/> <path d="M45.317 2.07103C48.1765 -1.53037 53.9745 0.442937 54.0434 5.041L54.4849 '
        b'72.2922H9.83113C1.64038 72.2922 -2.92775 62.8321 2.1655 56.4175L45.317 2.07103Z" fill="#3ECF8E"/> <defs>'
        b'<linearGradient id="paint0_linear" x1="53.9738" y1="54.974" x2="94.1635" y2="71.8295"'
        b'gradientUnits="userSpaceOnUse"> <stop stop-color="#249361"/> <stop offset="1" stop-color="#3ECF8E"/> '
        b'</linearGradient> <linearGradient id="paint1_linear" x1="36.1558" y1="30.578" x2="54.4844" y2="65.0806" '
        b'gradientUnits="userSpaceOnUse"> <stop/> <stop offset="1" stop-opacity="0"/> </linearGradient> </defs> </svg>'
    )
    bucket_folder = uuid4().hex[:8]
    bucket_path = f"{bucket_folder}/{file_name}"
    file_path = tmp_path / file_name
    with open(file_path, "wb") as f:
        f.write(file_content)

    return {
        "name": file_name,
        "local_path": str(file_path),
        "bucket_folder": bucket_folder,
        "bucket_path": bucket_path,
        "mime_type": "image/svg+xml",
    }


# TODO: Test create_bucket, delete_bucket, empty_bucket, list_buckets, fileAPI.list before upload test


def test_client_upload_file(
    supabase: Client, bucket: str, file: Dict[str, str]
) -> None:
    """Ensure we can upload files to a bucket"""
    storage = supabase.storage()
    storage_file = storage.StorageFileAPI(bucket)

    file_name = file["name"]
    file_path = file["local_path"]
    mime_type = file["mime_type"]
    bucket_file_path = file["bucket_path"]
    bucket_folder = file["bucket_folder"]
    options = {"content-type": mime_type}

    storage_file.upload(bucket_file_path, file_path, options)
    files: List[Dict[str, Any]] = storage_file.list(bucket_folder)
    image_info = next((f for f in files if f.get("name") == file_name), None)

    assert files
    assert image_info is not None
    assert image_info.get("metadata", {}).get("mimetype") == mime_type
