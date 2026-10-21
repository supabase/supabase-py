import asyncio
from typing import Any, Callable, Coroutine

import pytest
from httpx import AsyncClient, Client, MockTransport, Request, Response
from supabase_utils.http.adapters.httpx import AsyncHttpxSession, HttpxSession

from storage3 import AsyncStorageClient, SyncStorageClient


class AsyncFinalizerFactory:
    def __init__(self, finalizer: Callable[[], Coroutine[Any, Any, None]]) -> None:
        def func() -> Any:
            event_loop = asyncio.get_event_loop_policy().get_event_loop()
            return event_loop.run_until_complete(finalizer())

        self.finalizer = func


class SyncFinalizerFactory:
    def __init__(self, finalizer: Callable[[], None]) -> None:
        self.finalizer = finalizer


STORAGE_URL = "https://example.supabase.co/storage/v1/"

use_async = pytest.mark.parametrize("use_async", [False, True], ids=["sync", "async"])


async def call_with_client(
    use_async: bool,
    handler: Callable[[Request], Response],
    action: Callable[[Any], Any],
) -> Any:
    """Run action against a sync or async storage client backed by handler."""
    transport = MockTransport(handler)
    if use_async:
        async with AsyncStorageClient(
            STORAGE_URL,
            {},
            http_session=AsyncHttpxSession(AsyncClient(transport=transport)),
        ) as client:
            return await action(client)
    with SyncStorageClient(
        STORAGE_URL, {}, http_session=HttpxSession(Client(transport=transport))
    ) as sync_client:
        return action(sync_client)
