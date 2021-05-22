from supabase_py.lib.storage.storage_bucket_api import StorageBucketAPI
from supabase_py.lib.storage.storage_file_api import StorageFileApi


class SupabaseStorageClient(StorageBucketAPI):
    """
    Manage the storage bucket and files

    Examples
    --------
    >>> url = storage_file.create_signed_url("poll3o/test2.txt", 80)  # signed url
    >>> loop.run_until_complete(storage_file.download("poll3o/test2.txt")) #upload or download
    >>> loop.run_until_complete(storage_file.upload("poll3o/test2.txt","path_file_upload"))
    >>> list_buckets = storage.list_buckets()
    >>> list_files = storage_file.list("pollo")
    """

    def __init__(self, url, headers):
        super().__init__(url, headers)

    def StorageFileApi(self, id_, replace=False):
        return StorageFileApi(self.url, self.headers, id_, replace)
    
    def StorageBucketAPI(self):
        return StorageBucketAPI(self.url, self.headers)

