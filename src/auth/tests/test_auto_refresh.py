import asyncio
import json
import time
from typing import Optional

import pytest
from httpx import AsyncClient, MockTransport, Request, Response
from supabase_auth import AsyncGoTrueClient
from supabase_auth._async.storage import AsyncMemoryStorage
from supabase_auth.timer import Timer
from supabase_auth.types import Session


async def test_auto_refresh_persists_rotated_session_with_async_storage(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    real_sleep = asyncio.sleep

    class AsyncIOStorage(AsyncMemoryStorage):
        async def set_item(self, key: str, value: str) -> None:
            # A database or file-backed storage write yields to the event loop.
            await real_sleep(0)
            await super().set_item(key, value)

    tick = asyncio.Event()
    refresh_started = asyncio.Event()
    refresh_task: Optional[asyncio.Task] = None
    sleeps = 0

    async def timer_sleep(delay: float) -> None:
        nonlocal sleeps
        sleeps += 1
        if sleeps == 1:
            await tick.wait()
        else:
            await asyncio.Future()

    monkeypatch.setattr("supabase_auth.timer.asyncio.sleep", timer_sleep)

    def handler(request: Request) -> Response:
        nonlocal refresh_task
        grant = request.url.params["grant_type"]
        assert request.url.path == "/token"
        if grant == "refresh_token":
            assert json.loads(request.content) == {"refresh_token": "old-refresh"}
            refresh_task = asyncio.current_task()
            refresh_started.set()
        else:
            assert grant == "password"
        return Response(
            200,
            json={
                "access_token": "new-access"
                if grant == "refresh_token"
                else "old-access",
                "refresh_token": "new-refresh"
                if grant == "refresh_token"
                else "old-refresh",
                "token_type": "bearer",
                "expires_in": 3600,
                "expires_at": round(time.time()) + 3600,
                "user": {
                    "id": "00000000-0000-4000-8000-000000000001",
                    "aud": "authenticated",
                    "app_metadata": {},
                    "user_metadata": {},
                    "created_at": "2024-01-01T00:00:00Z",
                },
            },
        )

    storage = AsyncIOStorage()
    events = []
    async with AsyncGoTrueClient(
        url="http://auth.test",
        storage=storage,
        storage_key="test-session",
        http_client=AsyncClient(transport=MockTransport(handler)),
    ) as client:
        client.on_auth_state_change(lambda event, session: events.append(event))
        try:
            await client.sign_in_with_password(
                {"email": "user@example.com", "password": "password"}
            )
            tick.set()
            await asyncio.wait_for(refresh_started.wait(), 1)
            assert refresh_task is not None
            await asyncio.gather(refresh_task, return_exceptions=True)

            stored = await storage.get_item("test-session")
            assert stored is not None
            session = Session.model_validate_json(stored)
            assert session.refresh_token == "new-refresh"
            assert session.access_token == "new-access"
            assert events == ["SIGNED_IN", "TOKEN_REFRESHED"]
        finally:
            if client._refresh_token_timer:
                client._refresh_token_timer.cancel()
            await real_sleep(0)


async def test_timer_cancel_stops_callback_from_another_task() -> None:
    started = asyncio.Event()
    task: Optional[asyncio.Task] = None
    completed = False

    async def callback() -> None:
        nonlocal task, completed
        task = asyncio.current_task()
        started.set()
        await asyncio.Future()
        completed = True

    timer = Timer(0, callback)
    timer.start()
    try:
        await asyncio.wait_for(started.wait(), 1)
        assert task is not None
        timer.cancel()
        await asyncio.gather(task, return_exceptions=True)
        assert task.cancelled()
        assert not completed
    finally:
        timer.cancel()
