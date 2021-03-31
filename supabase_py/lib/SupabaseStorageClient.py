from supabase_py.lib.Storage.StorageBucketApi import StorageBucketApi
from supabase_py.lib.Storage.StorageFileApi import StorageFileApi


class SupabaseStorageClient(StorageBucketApi):
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

    def StorageFileApi(self, id_):
        return StorageFileApi(self.url, self.headers, id_)
