from deprecation import deprecated
from storage3 import SyncStorageClient
from storage3._sync.file_api import SyncBucketProxy


class SupabaseStorageClient(SyncStorageClient):
    """Manage storage buckets and files."""

    @deprecated("0.5.4", "0.6.0", details="Use `.from_()` instead")
    def StorageFileAPI(self, id_: str) -> SyncBucketProxy:
        return super().from_(id_)
