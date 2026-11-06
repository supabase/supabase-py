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

from .client import AsyncClient, Client, SupabaseException

# Lib
from .lib.client_options import AsyncClientOptions, ClientOptions
from .types import RealtimeClientOptions

# Version
from .version import __version__

__all__ = [
    "AsyncClient",
    "AsyncClientOptions",
    "AuthApiError",
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
    "ClientOptions",
    "CustomAuthError",
    "FunctionsError",
    "FunctionsHttpError",
    "FunctionsRelayError",
    "NotConnectedError",
    "PostgrestAPIError",
    "PostgrestAPIResponse",
    "RealtimeClientOptions",
    "StorageApiError",
    "StorageException",
    "SupabaseException",
    "UserDoesNotExistError",
    "VectorBucketException",
    "__version__",
]
