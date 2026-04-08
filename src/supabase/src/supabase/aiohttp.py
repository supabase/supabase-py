from aiohttp import ClientSession
from supabase_utils.http.adapters.aiohttp import AsyncAiohttpSession

from ._async.client import AsyncClient
from .lib.client_options import AsyncClientOptions


def create_aclient(
    supabase_url: str,
    supabase_key: str,
    http_client: ClientSession | None = None,
    options: AsyncClientOptions | None = None,
) -> AsyncClient:
    client = http_client or ClientSession()
    return AsyncClient(
        supabase_url=supabase_url,
        supabase_key=supabase_key,
        http_session=AsyncAiohttpSession(client=client),
        options=options,
    )
