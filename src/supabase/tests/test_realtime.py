import asyncio
from unittest.mock import AsyncMock, MagicMock

import supabase


def test_realtime_client_initialization() -> None:
    ref = "ooqqmozurnggtljmjkii"
    url = f"https://{ref}.supabase.co"
    # Sample JWT Key
    key = "xxxxxxxxxxxxxx.xxxxxxxxxxxxxxx.xxxxxxxxxxxxxxx"
    sp = supabase.Client(url, key)
    assert str(sp.realtime_url) == f"wss://{ref}.supabase.co/realtime/v1"

    url = "http://localhost:54322"
    sp_local = supabase.Client(url, key)
    assert str(sp_local.realtime_url) == "ws://localhost:54322/realtime/v1"


async def test_auth_events_keep_the_realtime_set_auth_task_until_it_finishes() -> None:
    client = supabase.AsyncClient("http://localhost:54321", "key")
    client.realtime = AsyncMock()

    client._listen_to_auth_events("SIGNED_IN", MagicMock(access_token="userjwt"))

    assert len(client._background_tasks) == 1
    await asyncio.gather(*client._background_tasks)
    await asyncio.sleep(0)

    client.realtime.set_auth.assert_awaited_once_with("userjwt")
    assert client._background_tasks == set()
