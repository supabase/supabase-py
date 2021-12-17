from typing import Dict

from supabase.lib.storage.storage_bucket_api import StorageBucketAPI
from supabase.lib.storage.storage_file_api import StorageFileAPI


class SupabaseStorageClient(StorageBucketAPI):
    """
    Manage the storage bucket and files
    Examples
    --------
    >>> url = storage_file.create_signed_url("something/test2.txt", 80)  # signed url
    >>> loop.run_until_complete(storage_file.download("something/test2.txt")) # upload or download
    >>> loop.run_until_complete(storage_file.upload("something/test2.txt","path_file_upload"))
    >>> list_buckets = storage.list_buckets()
    >>> list_files = storage_file.list("something")
    """

    def __init__(self, url: str, headers: Dict[str, str]):
        super().__init__(url, headers)

    def StorageFileAPI(self, id_: str) -> StorageFileAPI:
        return StorageFileAPI(self.url, self.headers, id_)
