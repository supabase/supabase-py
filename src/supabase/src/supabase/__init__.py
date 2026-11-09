from postgrest import APIError as PostgrestAPIError
from postgrest import APIResponse as PostgrestAPIResponse
from realtime import (
    AuthorizationError,
    MaxRetriesExceeded,
    NotConnectedError,
    RealtimeError,
)
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
    UserDoesNotExistError,
)
from supabase_functions import (
    FunctionsError,
    FunctionsHttpError,
    FunctionsRelayError,
)
from supabase_utils.errors import SupabaseError
from supabase_utils.http.errors import (
    RequestTimeoutError,
    SupabaseAPIError,
    SupabaseTransportError,
)

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
    "FunctionsClientOptions",
    "FunctionsError",
    "FunctionsHttpError",
    "FunctionsRelayError",
    "MaxRetriesExceeded",
    "NotConnectedError",
    "PostgrestAPIError",
    "PostgrestAPIResponse",
    "PostgrestClientOptions",
    "RealtimeClientOptions",
    "RealtimeError",
    "RequestTimeoutError",
    "StorageApiError",
    "StorageClientOptions",
    "StorageException",
    "SupabaseAPIError",
    "SupabaseError",
    "SupabaseException",
    "SupabaseTransportError",
    "UserDoesNotExistError",
    "VectorBucketException",
    "__version__",
]
