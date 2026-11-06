from postgrest import APIError as PostgrestAPIError
from postgrest import APIResponse as PostgrestAPIResponse
from realtime import AuthorizationError, NotConnectedError
from storage3 import StorageApiError, StorageException, VectorBucketException
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
from supabase_utils.http.errors import RequestTimeoutError

from .client import AsyncClient, Client, SupabaseException
from .types import (
    AuthClientOptions,
    FunctionsClientOptions,
    PostgrestClientOptions,
    RealtimeClientOptions,
    StorageClientOptions,
)

# Version
from .version import __version__

__all__ = [
    "AsyncClient",
    "AuthApiError",
    "AuthClientOptions",
    "AuthError",
    "AuthImplicitGrantRedirectError",
    "AuthInvalidCredentialsError",
    "AuthInvalidJwtError",
    "AuthRetryableError",
    "AuthSessionMissingError",
    "AuthUnknownError",
    "AuthWeakPasswordError",
    "AuthorizationError",
    "Client",
    "CustomAuthError",
    "FunctionsClientOptions",
    "FunctionsError",
    "FunctionsHttpError",
    "FunctionsRelayError",
    "NotConnectedError",
    "PostgrestAPIError",
    "PostgrestAPIResponse",
    "PostgrestClientOptions",
    "RealtimeClientOptions",
    "RequestTimeoutError",
    "StorageApiError",
    "StorageClientOptions",
    "StorageException",
    "SupabaseException",
    "UserDoesNotExistError",
    "VectorBucketException",
    "__version__",
]
