from fastapi import HTTPException, Request
from supabase import AsyncClientOptions, acreate_client
from supabase._async.client import AsyncClient

from config import settings


async def get_client(request: Request) -> AsyncClient:
    """
    Construct a fresh per-request AsyncClient using the caller's JWT.

    FRICTION NOTE: There is no built-in helper for this pattern. We must
    manually construct AsyncClientOptions with the Authorization header.
    Passing headers={} to AsyncClientOptions REPLACES the defaults (losing
    X-Client-Info), so we mutate the options object after construction.
    See friction_log.md -- "Per-request JWT injection is not ergonomic".
    """
    auth = request.headers.get("Authorization", "")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")

    token = auth.removeprefix("Bearer ")
    if not token:
        raise HTTPException(status_code=401, detail="Missing or invalid Authorization header")
    # Mutate after construction to preserve DEFAULT_HEADERS (X-Client-Info etc.)
    options = AsyncClientOptions()
    options.headers["Authorization"] = f"Bearer {token}"

    return await acreate_client(
        settings.supabase_url, settings.supabase_anon_key, options=options
    )
