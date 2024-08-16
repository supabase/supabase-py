from postgrest import APIError as PostgrestAPIError
from postgrest import APIResponse as PostgrestAPIResponse
from storage3.utils import StorageException

# Async Client
from ._async.auth_client import AsyncSupabaseAuthClient as ASupabaseAuthClient
from ._async.client import AsyncClient as AClient
from ._async.client import AsyncStorageClient as ASupabaseStorageClient
from ._async.client import ClientOptions as AClientOptions
from ._async.client import create_client as acreate_client

# Sync Client
from ._sync.auth_client import SyncSupabaseAuthClient as SupabaseAuthClient
from ._sync.client import ClientOptions
from ._sync.client import SyncClient as Client
from ._sync.client import SyncStorageClient as SupabaseStorageClient
from ._sync.client import create_client

# Version
from .version import __version__

__all__ = [
    "acreate_client",
    "AClient",
    "ASupabaseAuthClient",
    "ASupabaseStorageClient",
    "create_client",
    "Client",
    "SupabaseAuthClient",
    "SupabaseStorageClient",
    "PostgrestAPIError",
    "PostgrestAPIResponse",
    "StorageException",
    "version",
]
