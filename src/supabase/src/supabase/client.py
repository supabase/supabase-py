from gotrue.errors import (
    AuthApiError,
    AuthError,
    AuthImplicitGrantRedirectError,
    AuthInvalidCredentialsError,
    AuthRetryableError,
    AuthSessionMissingError,
    AuthUnknownError,
    AuthWeakPasswordError,
)
from postgrest import APIError as PostgrestAPIError
from postgrest import APIResponse as PostgrestAPIResponse
from realtime import AuthorizationError, NotConnectedError
from storage3.utils import StorageException
from supafunc.errors import FunctionsError, FunctionsHttpError, FunctionsRelayError

# Async Client
from ._async.auth_client import AsyncSupabaseAuthClient
from ._async.client import AsyncClient
from ._async.client import AsyncStorageClient as AsyncSupabaseStorageClient
from ._async.client import create_client as acreate_client
from ._async.client import create_client as create_async_client

# Sync Client
from ._sync.auth_client import SyncSupabaseAuthClient as SupabaseAuthClient
from ._sync.client import SyncClient as Client
from ._sync.client import SyncStorageClient as SupabaseStorageClient
from ._sync.client import create_client

# Lib
from .lib.client_options import AsyncClientOptions
from .lib.client_options import AsyncClientOptions as AClientOptions
from .lib.client_options import SyncClientOptions as ClientOptions

# Version
from .version import __version__

__all__ = [
    "AsyncSupabaseAuthClient",
    "acreate_client",
    "create_async_client",
    "AClientOptions",
    "AsyncClient",
    "AsyncClientOptions",
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
    "AuthApiError",
    "AuthError",
    "AuthImplicitGrantRedirectError",
    "AuthInvalidCredentialsError",
    "AuthRetryableError",
    "AuthSessionMissingError",
    "AuthWeakPasswordError",
    "AuthUnknownError",
    "FunctionsHttpError",
    "FunctionsRelayError",
    "FunctionsError",
    "AuthorizationError",
    "NotConnectedError",
]
