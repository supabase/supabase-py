from postgrest import APIError as PostgrestAPIError
from postgrest import APIResponse as PostgrestAPIResponse
from storage3.utils import StorageException

# Async Client
from ._async.auth_client import AsyncSupabaseAuthClient
from ._async.client import AsyncClient
from ._async.client import AsyncStorageClient as AsyncSupabaseStorageClient
from ._async.client import create_client as create_async_client

# Sync Client
from ._sync.auth_client import SyncSupabaseAuthClient as SupabaseAuthClient
from ._sync.client import SyncClient as Client
from ._sync.client import SyncStorageClient as SupabaseStorageClient
from ._sync.client import create_client

# Lib
from .lib.client_options import ClientOptions

# Version
from .version import __version__

__all__ = [
    "AsyncSupabaseAuthClient",
    "create_async_client",
    "AsyncClient",
    "AsyncSupabaseStorageClient",
    "SupabaseAuthClient",
    "create_client",
    "Client",
    "ClientOptions",
    "SupabaseStorageClient",
    "PostgrestAPIError",
    "PostgrestAPIResponse",
    "StorageException",
    "__version__",
]
