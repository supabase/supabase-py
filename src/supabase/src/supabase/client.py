from postgrest import APIError as PostgrestAPIError
from postgrest import APIResponse as PostgrestAPIResponse
from realtime import AuthorizationError, NotConnectedError
from storage3 import AsyncStorageClient as AsyncSupabaseStorageClient
from storage3 import StorageApiError, StorageException, VectorBucketException

# Sync Client
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

# Lib
from .lib.client_options import AsyncClientOptions
from .lib.client_options import AsyncClientOptions as AClientOptions
from .lib.client_options import SyncClientOptions as ClientOptions

# Version
from .version import __version__

__all__ = [
    "AClientOptions",
    "AsyncClient",
    "AsyncClientOptions",
    "AsyncSupabaseStorageClient",
    "ClientOptions",
    "SupabaseStorageClient",
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
]
