from postgrest import APIError as PostgrestAPIError
from postgrest import APIResponse as PostgrestAPIResponse
from realtime import AuthorizationError, NotConnectedError
from storage3 import AsyncStorageClient as ASupabaseStorageClient
from storage3 import StorageApiError, StorageException, VectorBucketException
from storage3 import SyncStorageClient as SupabaseStorageClient
from supabase_auth import (
    AuthApiError,
    AuthError,
    AuthImplicitGrantRedirectError,
    AuthInvalidCredentialsError,
    AuthInvalidJwtError,
    AuthRetryableError,
    AuthSessionMissingError,
    AuthUnknownError,
    AuthWeakPasswordError,
    CustomAuthError,
    UserDoesNotExistError,
)
from supabase_functions import (
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

__all__ = [
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
    "StorageApiError",
    "StorageException",
    "VectorBucketException",
    "__version__",
    "AuthApiError",
    "AuthError",
    "AuthImplicitGrantRedirectError",
    "AuthInvalidCredentialsError",
    "AuthInvalidJwtError",
    "AuthRetryableError",
    "AuthSessionMissingError",
    "AuthWeakPasswordError",
    "AuthUnknownError",
    "CustomAuthError",
    "UserDoesNotExistError",
    "FunctionsHttpError",
    "FunctionsRelayError",
    "FunctionsError",
    "AuthorizationError",
    "NotConnectedError",
    "ASupabaseException",
    "AsyncSupabaseException",
    "SyncSupabaseException",
]
