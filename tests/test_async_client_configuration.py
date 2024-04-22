from __future__ import annotations

from typing import Any

import pytest


def test_async_configuration():
    import httpcore
    import asyncio
    import os
    from supabase._async.client import create_client

    url: str = os.environ.get("SUPABASE_URL")
    key: str = os.environ.get("SUPABASE_KEY")

    client = asyncio.run(create_client(url, key))
    data   = [{"item": value} for value in range(0, 100000)]

    asyncio.run(client.table("sample").insert(data).execute())
