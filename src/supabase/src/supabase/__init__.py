from postgrest import APIError as PostgrestAPIError
from postgrest import APIResponse as PostgrestAPIResponse
from realtime import AuthorizationError, NotConnectedError
from storage3.utils import StorageException
from supabase_auth.errors import (
    AuthApiError,
    AuthError,
    AuthImplicitGrantRedirectError,
    AuthInvalidCredentialsError,
    AuthRetryableError,
    AuthSessionMissingError,
    AuthUnknownError,
    AuthWeakPasswordError,
)
from supabase_functions.errors import (
    FunctionsError,
    FunctionsHttpError,
    FunctionsRelayError,
)

# Async Client
from ._async.auth_client import AsyncSupabaseAuthClient as ASupabaseAuthClient
from ._async.client import AsyncClient
from ._async.client import AsyncClient as AClient
from ._async.client import AsyncStorageClient as ASupabaseStorageClient
from ._async.client import SupabaseException as ASupabaseException
from ._async.client import SupabaseException as AsyncSupabaseException
from ._async.client import create_client as acreate_client
from ._async.client import create_client as create_async_client

# Sync Client
from ._sync.auth_client import SyncSupabaseAuthClient as SupabaseAuthClient
from ._sync.client import Client, SupabaseException, create_client
from ._sync.client import SupabaseException as SyncSupabaseException
from ._sync.client import SyncStorageClient as SupabaseStorageClient

# Lib
from .lib.client_options import AsyncClientOptions
from .lib.client_options import AsyncClientOptions as AClientOptions
from .lib.client_options import SyncClientOptions as ClientOptions

# Version
from .version import __version__

__all__ = (
    "acreate_client",
    "create_async_client",
    "AClient",
    "ASupabaseAuthClient",
    "ASupabaseStorageClient",
    "AClientOptions",
    "AsyncClient",
    "AsyncClientOptions",
    "create_client",
    "Client",
    "SupabaseAuthClient",
    "SupabaseStorageClient",
    "ClientOptions",
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
    "SupabaseException",
    "ASupabaseException",
    "AsyncSupabaseException",
    "SyncSupabaseException",
)
