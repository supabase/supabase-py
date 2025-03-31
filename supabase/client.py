# client.py actualizado y mejorado
from __future__ import annotations

# Excepciones y errores (agrupados por fuente)
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
from postgrest import (
    APIError as PostgrestAPIError,
    APIResponse as PostgrestAPIResponse,
)
from realtime import AuthorizationError, NotConnectedError
from storage3.utils import StorageException
from supafunc.errors import FunctionsError, FunctionsHttpError, FunctionsRelayError

# Clientes Asíncronos
from ._async.auth_client import AsyncSupabaseAuthClient
from ._async.client import (
    AsyncClient,
    AsyncStorageClient as AsyncSupabaseStorageClient,
    create_client as acreate_client,
)

# Clientes Síncronos
from ._sync.auth_client import SyncSupabaseAuthClient
from ._sync.client import (
    SyncClient,
    SyncStorageClient as SyncSupabaseStorageClient,
    create_client,
)

# Configuraciones
from .lib.client_options import (
    AsyncClientOptions,
    SyncClientOptions,
)

# Metadata
from .version import __version__

__all__ = [
    # Factories principales
    "create_client",
    "acreate_client",
    
    # Clientes síncronos
    "SyncClient",
    "SyncSupabaseAuthClient",
    "SyncSupabaseStorageClient",
    
    # Clientes asíncronos
    "AsyncClient",
    "AsyncSupabaseAuthClient",
    "AsyncSupabaseStorageClient",
    
    # Opciones de configuración
    "SyncClientOptions",
    "AsyncClientOptions",
    
    # Errores y respuestas
    "PostgrestAPIError",
    "PostgrestAPIResponse",
    "StorageException",
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
    
    # Metadata
    "__version__",
]

"""Módulo principal del cliente Python de Supabase.

Provee interfaces tanto síncronas como asíncronas para interactuar con:
- Auth
- Storage
- Realtime
- PostgREST
"""

# Validación de parámetros para el caso de uso específico
if __debug__:
    # Ejemplo de uso válido para el nuevo feature
    _ = SyncClientOptions(httpx_options={"verify": False})
    _ = AsyncClientOptions(httpx_options={"verify": False})