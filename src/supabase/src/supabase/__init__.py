from postgrest import APIError as PostgrestAPIError
from postgrest import APIResponse as PostgrestAPIResponse
from realtime import AuthorizationError, NotConnectedError
from storage3 import AsyncStorageClient as ASupabaseStorageClient
from storage3 import SyncStorageClient as SupabaseStorageClient
from storage3.exceptions import StorageException
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
from ._async.client import AsyncClient
from ._async.client import AsyncClient as AClient
from ._async.client import SupabaseException as ASupabaseException
from ._async.client import SupabaseException as AsyncSupabaseException
from ._sync.client import Client
from ._sync.client import SupabaseException as SyncSupabaseException

# Lib
from .lib.client_options import AsyncClientOptions
from .lib.client_options import AsyncClientOptions as AClientOptions
from .lib.client_options import SyncClientOptions as ClientOptions

# Version
from .version import __version__

__all__ = (
    "AClient",
    "ASupabaseStorageClient",
    "AClientOptions",
    "AsyncClient",
    "AsyncClientOptions",
    "Client",
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
    "ASupabaseException",
    "AsyncSupabaseException",
    "SyncSupabaseException",
)
