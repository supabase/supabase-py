from httpx import AsyncClient as AsyncHttpxClient
from httpx import Client as SyncHttpxClient
from supabase_utils.http.adapters.httpx import AsyncHttpxSession, HttpxSession

from ._async.client import AsyncClient
from ._sync.client import Client
from .lib.client_options import AsyncClientOptions, SyncClientOptions


def create_client(
    supabase_url: str,
    supabase_key: str,
    http_client: SyncHttpxClient | None = None,
    options: SyncClientOptions | None = None,
) -> Client:
    client = http_client or SyncHttpxClient(
        http2=True,
        verify=True,
    )
    return Client(
        supabase_url=supabase_url,
        supabase_key=supabase_key,
        http_session=HttpxSession(client=client),
        options=options,
    )


def create_aclient(
    supabase_url: str,
    supabase_key: str,
    http_client: AsyncHttpxClient | None = None,
    options: AsyncClientOptions | None = None,
) -> AsyncClient:
    client = http_client or AsyncHttpxClient(
        http2=True,
        verify=True,
    )
    return AsyncClient(
        supabase_url=supabase_url,
        supabase_key=supabase_key,
        http_session=AsyncHttpxSession(client=client),
        options=options,
    )
