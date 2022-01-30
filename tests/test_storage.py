from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

if TYPE_CHECKING:
    from supabase import Client


@pytest.mark.skip(reason="missing permissions on test instance")
def test_client_upload_file(supabase: Client) -> None:
    """Ensure we can upload files to a bucket"""

    TEST_BUCKET_NAME = "atestbucket"

    storage = supabase.storage()
    storage_file = storage.StorageFileAPI(TEST_BUCKET_NAME)

    filename = "test.jpeg"
    filepath = f"tests/{filename}"
    mimetype = "image/jpeg"
    options = {"contentType": mimetype}

    storage_file.upload(filename, filepath, options)
    files = storage_file.list()
    assert files

    image_info = None
    for item in files:
        if item.get("name") == filename:
            image_info = item
            break

    assert image_info is not None
    assert image_info.get("metadata", {}).get("mimetype") == mimetype

    storage_file.remove([filename])
