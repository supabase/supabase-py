import asyncio
import json
import threading
import time
from collections.abc import Callable
from typing import override

from httpx import AsyncClient, Client, MockTransport, Request, Response
from supabase_utils.http.adapters.httpx import AsyncHttpxSession, HttpxSession
from supabase_utils.types import JSON

from supabase_auth import (
    AsyncMemoryStorage,
    AsyncSupabaseAuthClient,
    SyncSupabaseAuthClient,
)
from supabase_auth.types import AuthChangeEvent, AuthStateChange, Session, User

USER: dict[str, JSON] = {
    "id": "11111111-1111-1111-1111-111111111111",
    "aud": "authenticated",
    "app_metadata": {},
    "user_metadata": {},
    "created_at": "2026-01-01T00:00:00Z",
}


def session_expiring_in(seconds: int) -> Session:
    return Session(
        access_token="old-access",
        refresh_token="old-refresh",
        token_type="bearer",
        expires_in=seconds,
        expires_at=round(time.time()) + seconds,
        user=User.model_validate(USER),
    )


def refreshed(request: Request) -> Response:
    return Response(
        200,
        json={
            "access_token": "new-access",
            "refresh_token": "new-refresh",
            "token_type": "bearer",
            "expires_in": 3600,
            "user": USER,
        },
    )


def bad_gateway(request: Request) -> Response:
    return Response(502, json={"code": 502, "msg": "bad gateway"})


class RefreshEndpoint:
    """A token endpoint that answers with `responses` in turn and signals
    `refreshed` once the last of them was sent."""

    def __init__(self, *responses: Callable[[Request], Response]) -> None:
        self.responses = list(responses)
        self.requests: list[Request] = []
        self.refreshed = threading.Event()

    def handle(self, request: Request) -> Response:
        self.requests.append(request)
        response = self.responses.pop(0)
        if not self.responses:
            self.refreshed.set()
        return response(request)


def events(changes: list[AuthStateChange]) -> list[AuthChangeEvent]:
    return [change.event for change in changes]


async def test_async_auto_refresh_tick_refreshes_the_session_once() -> None:
    endpoint = RefreshEndpoint(refreshed)
    client = AsyncSupabaseAuthClient(
        url="http://auth.test",
        http_session=AsyncHttpxSession(
            client=AsyncClient(transport=MockTransport(endpoint.handle))
        ),
    )
    manager = client.session_manager
    changes: list[AuthStateChange] = []
    client.on_auth_state_change(changes.append)

    await manager.save_session(session_expiring_in(2))
    await asyncio.wait_for(asyncio.to_thread(endpoint.refreshed.wait, 5), timeout=5)
    await asyncio.sleep(0.1)

    try:
        assert [json.loads(request.content) for request in endpoint.requests] == [
            {"refresh_token": "old-refresh"}
        ]
        stored = await manager.storage.get_item(manager.storage_key)
        assert stored is not None
        assert Session.model_validate_json(stored).refresh_token == "new-refresh"
        assert events(changes) == [
            AuthChangeEvent.INITIAL_SESSION,
            AuthChangeEvent.TOKEN_REFRESHED,
        ]
        assert manager.refresh_token_timer is not None
    finally:
        manager._cancel_refresh_timer()


async def test_async_auto_refresh_retries_a_failed_refresh_and_keeps_the_session() -> (
    None
):
    endpoint = RefreshEndpoint(bad_gateway, refreshed)
    client = AsyncSupabaseAuthClient(
        url="http://auth.test",
        http_session=AsyncHttpxSession(
            client=AsyncClient(transport=MockTransport(endpoint.handle))
        ),
    )
    manager = client.session_manager
    changes: list[AuthStateChange] = []
    client.on_auth_state_change(changes.append)

    await manager.save_session(session_expiring_in(2))
    await asyncio.wait_for(asyncio.to_thread(endpoint.refreshed.wait, 5), timeout=5)
    await asyncio.sleep(0.1)

    try:
        assert len(endpoint.requests) == 2
        stored = await manager.storage.get_item(manager.storage_key)
        assert stored is not None
        assert Session.model_validate_json(stored).refresh_token == "new-refresh"
        assert events(changes) == [
            AuthChangeEvent.INITIAL_SESSION,
            AuthChangeEvent.TOKEN_REFRESHED,
        ]
    finally:
        manager._cancel_refresh_timer()


async def test_async_auto_refresh_persists_the_rotated_session_with_a_suspending_storage() -> (
    None
):
    class SuspendingStorage(AsyncMemoryStorage):
        @override
        async def set_item(self, key: str, value: str) -> None:
            # A database or file backed storage yields to the event loop.
            await asyncio.sleep(0)
            await super().set_item(key, value)

    endpoint = RefreshEndpoint(refreshed)
    storage = SuspendingStorage()
    client = AsyncSupabaseAuthClient(
        url="http://auth.test",
        http_session=AsyncHttpxSession(
            client=AsyncClient(transport=MockTransport(endpoint.handle))
        ),
        storage=storage,
    )
    manager = client.session_manager
    changes: list[AuthStateChange] = []
    client.on_auth_state_change(changes.append)

    await manager.save_session(session_expiring_in(2))
    await asyncio.wait_for(asyncio.to_thread(endpoint.refreshed.wait, 5), timeout=5)
    await asyncio.sleep(0.1)

    try:
        stored = await storage.get_item(manager.storage_key)
        assert stored is not None
        assert Session.model_validate_json(stored).refresh_token == "new-refresh"
        assert events(changes) == [
            AuthChangeEvent.INITIAL_SESSION,
            AuthChangeEvent.TOKEN_REFRESHED,
        ]
    finally:
        manager._cancel_refresh_timer()


def test_sync_auto_refresh_tick_refreshes_the_session_once() -> None:
    endpoint = RefreshEndpoint(refreshed)
    client = SyncSupabaseAuthClient(
        url="http://auth.test",
        http_session=HttpxSession(
            client=Client(transport=MockTransport(endpoint.handle))
        ),
    )
    manager = client.session_manager
    changes: list[AuthStateChange] = []
    client.on_auth_state_change(changes.append)

    manager.save_session(session_expiring_in(2))
    assert endpoint.refreshed.wait(5)
    time.sleep(0.1)

    try:
        assert [json.loads(request.content) for request in endpoint.requests] == [
            {"refresh_token": "old-refresh"}
        ]
        stored = manager.storage.get_item(manager.storage_key)
        assert stored is not None
        assert Session.model_validate_json(stored).refresh_token == "new-refresh"
        assert events(changes) == [
            AuthChangeEvent.INITIAL_SESSION,
            AuthChangeEvent.TOKEN_REFRESHED,
        ]
        assert manager.refresh_token_timer is not None
    finally:
        manager._cancel_refresh_timer()


def test_sync_auto_refresh_retries_a_failed_refresh_and_keeps_the_session() -> None:
    endpoint = RefreshEndpoint(bad_gateway, refreshed)
    client = SyncSupabaseAuthClient(
        url="http://auth.test",
        http_session=HttpxSession(
            client=Client(transport=MockTransport(endpoint.handle))
        ),
    )
    manager = client.session_manager
    changes: list[AuthStateChange] = []
    client.on_auth_state_change(changes.append)

    manager.save_session(session_expiring_in(2))
    assert endpoint.refreshed.wait(5)
    time.sleep(0.1)

    try:
        assert len(endpoint.requests) == 2
        stored = manager.storage.get_item(manager.storage_key)
        assert stored is not None
        assert Session.model_validate_json(stored).refresh_token == "new-refresh"
        assert events(changes) == [
            AuthChangeEvent.INITIAL_SESSION,
            AuthChangeEvent.TOKEN_REFRESHED,
        ]
    finally:
        manager._cancel_refresh_timer()
