from collections.abc import Mapping

from aiohttp import ClientSession, ClientTimeout
from supabase_auth import AsyncSupportedStorage
from supabase_utils.http.adapters.aiohttp import AsyncAiohttpSession
from supabase_utils.http.request import validate_request_timeout
from supabase_utils.http.retry import RetryPolicy

from ._defaults import DEFAULT_REQUEST_TIMEOUT
from ._keys import _validate_string_argument
from .client import AsyncClient, _parse_supabase_url
from .types import (
    AuthClientOptions,
    FunctionsClientOptions,
    PostgrestClientOptions,
    RealtimeClientOptions,
    StorageClientOptions,
)


def _default_session() -> ClientSession:
    return ClientSession(
        timeout=ClientTimeout(
            total=None,
            connect=DEFAULT_REQUEST_TIMEOUT,
            sock_connect=DEFAULT_REQUEST_TIMEOUT,
            sock_read=DEFAULT_REQUEST_TIMEOUT,
        )
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
    allow_insecure_http: bool = False,
) -> AsyncClient:
    """Create an async client that sends its requests with aiohttp.

    `http_client` defaults to a new aiohttp client with a 60 second timeout,
    which is closed with the client. An `http_client` passed in keeps its own
    timeout and is left open. See `AsyncClient` for the other arguments.
    """
    _parse_supabase_url(supabase_url, allow_insecure_http=allow_insecure_http)
    _validate_string_argument("supabase_key", supabase_key)
    validate_request_timeout(request_timeout)
    client = AsyncClient(
        supabase_url,
        supabase_key,
        AsyncAiohttpSession(
            client=http_client or _default_session(), owns_client=http_client is None
        ),
        headers=headers,
        request_timeout=request_timeout,
        retry=retry,
        postgrest=postgrest,
        auth=auth,
        storage=storage,
        functions=functions,
        realtime=realtime,
        allow_insecure_http=allow_insecure_http,
    )
    client._owns_http_session = http_client is None
    return client
