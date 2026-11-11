from collections.abc import Mapping

from httpx import AsyncClient as AsyncHttpxClient
from httpx import Client as SyncHttpxClient
from supabase_auth import AsyncSupportedStorage, SyncSupportedStorage
from supabase_utils.http.adapters.httpx import AsyncHttpxSession, HttpxSession
from supabase_utils.http.request import validate_request_timeout
from supabase_utils.http.retry import RetryPolicy

from .client import AsyncClient, Client
from .types import (
    AuthClientOptions,
    FunctionsClientOptions,
    PostgrestClientOptions,
    RealtimeClientOptions,
    StorageClientOptions,
)


def create_client(
    supabase_url: str,
    supabase_key: str,
    *,
    http_client: SyncHttpxClient | None = None,
    headers: Mapping[str, str] | None = None,
    request_timeout: float | None = None,
    retry: RetryPolicy | None = None,
    postgrest: PostgrestClientOptions | None = None,
    auth: AuthClientOptions[SyncSupportedStorage] | None = None,
    storage: StorageClientOptions | None = None,
    functions: FunctionsClientOptions | None = None,
) -> Client:
    """Create a sync client that sends its requests with httpx.

    `http_client` defaults to a new httpx client. See `Client` for the other
    arguments.
    """
    validate_request_timeout(request_timeout)
    client = http_client or SyncHttpxClient(
        http2=True,
        verify=True,
        follow_redirects=True,
    )
    return Client(
        supabase_url,
        supabase_key,
        HttpxSession(client=client),
        headers=headers,
        request_timeout=request_timeout,
        retry=retry,
        postgrest=postgrest,
        auth=auth,
        storage=storage,
        functions=functions,
    )


def create_async_client(
    supabase_url: str,
    supabase_key: str,
    *,
    http_client: AsyncHttpxClient | None = None,
    headers: Mapping[str, str] | None = None,
    request_timeout: float | None = None,
    retry: RetryPolicy | None = None,
    postgrest: PostgrestClientOptions | None = None,
    auth: AuthClientOptions[AsyncSupportedStorage] | None = None,
    storage: StorageClientOptions | None = None,
    functions: FunctionsClientOptions | None = None,
    realtime: RealtimeClientOptions | None = None,
) -> AsyncClient:
    """Create an async client that sends its requests with httpx.

    `http_client` defaults to a new httpx client. See `AsyncClient` for the
    other arguments.
    """
    validate_request_timeout(request_timeout)
    client = http_client or AsyncHttpxClient(
        http2=True,
        verify=True,
        follow_redirects=True,
    )
    return AsyncClient(
        supabase_url,
        supabase_key,
        AsyncHttpxSession(client=client),
        headers=headers,
        request_timeout=request_timeout,
        retry=retry,
        postgrest=postgrest,
        auth=auth,
        storage=storage,
        functions=functions,
        realtime=realtime,
    )
