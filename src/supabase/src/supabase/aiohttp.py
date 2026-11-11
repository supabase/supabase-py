from collections.abc import Mapping

from aiohttp import ClientSession
from supabase_auth import AsyncSupportedStorage
from supabase_utils.http.adapters.aiohttp import AsyncAiohttpSession
from supabase_utils.http.request import validate_request_timeout
from supabase_utils.http.retry import RetryPolicy

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
    retry: RetryPolicy | None = None,
    postgrest: PostgrestClientOptions | None = None,
    auth: AuthClientOptions[AsyncSupportedStorage] | None = None,
    storage: StorageClientOptions | None = None,
    functions: FunctionsClientOptions | None = None,
    realtime: RealtimeClientOptions | None = None,
) -> AsyncClient:
    """Create an async client that sends its requests with aiohttp.

    `http_client` defaults to a new aiohttp client, which is closed with the
    client. An `http_client` passed in is left open. See `AsyncClient` for the
    other arguments.
    """
    validate_request_timeout(request_timeout)
    client = AsyncClient(
        supabase_url,
        supabase_key,
        AsyncAiohttpSession(client=http_client or ClientSession()),
        headers=headers,
        request_timeout=request_timeout,
        retry=retry,
        postgrest=postgrest,
        auth=auth,
        storage=storage,
        functions=functions,
        realtime=realtime,
    )
    client._owns_http_session = http_client is None
    return client
