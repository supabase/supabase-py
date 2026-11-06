from collections.abc import Mapping

from aiohttp import ClientSession
from supabase_auth import AsyncSupportedStorage
from supabase_utils.http.adapters.aiohttp import AsyncAiohttpSession
from supabase_utils.http.request import validate_request_timeout

from .client import AsyncClient
from .types import (
    AuthClientOptions,
    FunctionsClientOptions,
    PostgrestClientOptions,
    RealtimeClientOptions,
    StorageClientOptions,
)


def create_async_client(
    supabase_url: str,
    supabase_key: str,
    *,
    http_client: ClientSession | None = None,
    headers: Mapping[str, str] | None = None,
    request_timeout: float | None = None,
    postgrest: PostgrestClientOptions | None = None,
    auth: AuthClientOptions[AsyncSupportedStorage] | None = None,
    storage: StorageClientOptions | None = None,
    functions: FunctionsClientOptions | None = None,
    realtime: RealtimeClientOptions | None = None,
) -> AsyncClient:
    """Create an async client that sends its requests with aiohttp.

    `http_client` defaults to a new aiohttp client. See `AsyncClient` for the
    other arguments.
    """
    validate_request_timeout(request_timeout)
    client = http_client or ClientSession()
    return AsyncClient(
        supabase_url,
        supabase_key,
        AsyncAiohttpSession(client=client),
        headers=headers,
        request_timeout=request_timeout,
        postgrest=postgrest,
        auth=auth,
        storage=storage,
        functions=functions,
        realtime=realtime,
    )
