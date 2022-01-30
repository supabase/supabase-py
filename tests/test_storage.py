from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from supabase import Client
    from typing import List, Dict, Any


def test_client_upload_file(supabase: Client) -> None:
    """Ensure we can upload files to a bucket"""

    TEST_BUCKET_NAME = "atestbucket"

    storage = supabase.storage()
    storage_file = storage.StorageFileAPI(TEST_BUCKET_NAME)

    filename = "test_image.svg"
    filepath = f"tests/{filename}"
    mimetype = "image/svg+xml"
    options = {"content-type": mimetype}

    storage_file.upload(filename, filepath, options)
    files: List[Dict[str, Any]] = storage_file.list()

    image_info = None
    for item in files:
        if item.get("name") == filename:
            image_info = item
            break

    assert files
    assert image_info is not None
    assert image_info.get("metadata", {}).get("mimetype") == mimetype

    storage_file.remove([filename])
