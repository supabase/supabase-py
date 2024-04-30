import asyncio
import os

import pytest

from supabase._async.client import create_client

pytest_plugins = ("pytest_asyncio", )


@pytest.mark.asyncio
async def test_async_configuration():
    url: str = os.environ.get("SUPABASE_TEST_URL")
    key: str = os.environ.get("SUPABASE_TEST_KEY")

    """
    Initializing an AsynClient:
    Using asyncio.create_task instead of asyncio.run allows you to reuse
    the same client across different request, avoiding an event loop error.
    """

    client = await asyncio.create_task(create_client(url, key))
    data = [{"item": value} for value in range(0, 100000)]

    # insert
    await client.table("sample").insert(data).execute()
    # select
    await client.table("sample").select("*").execute()
    # delete
    await client.table("sample").delete().gt("item", 100).execute()
