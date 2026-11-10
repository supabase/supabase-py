import asyncio
import threading
import time
from concurrent.futures import ThreadPoolExecutor

from httpx import AsyncClient, Client, MockTransport, Request, Response
from supabase_utils.http.adapters.httpx import AsyncHttpxSession, HttpxSession
from supabase_utils.types import JSON

from supabase_auth import AsyncSupabaseAuthClient, SyncSupabaseAuthClient
from supabase_auth.types import AuthChangeEvent, AuthStateChange, Session, User

USER: dict[str, JSON] = {
    "id": "11111111-1111-1111-1111-111111111111",
    "aud": "authenticated",
    "app_metadata": {},
    "user_metadata": {},
    "created_at": "2026-01-01T00:00:00Z",
}


def expired_session() -> Session:
    return Session(
        access_token="old-access",
        refresh_token="old-refresh",
        token_type="bearer",
        expires_in=3600,
        expires_at=round(time.time()) - 60,
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


class AsyncRefreshGate:
    """A token endpoint that holds every refresh until `release` is called."""

    def __init__(self) -> None:
        self.requests: list[Request] = []
        self.started = asyncio.Event()
        self.gate = asyncio.Event()

    async def handle(self, request: Request) -> Response:
        self.requests.append(request)
        self.started.set()
        await self.gate.wait()
        return refreshed(request)

    def client(self) -> AsyncSupabaseAuthClient:
        return AsyncSupabaseAuthClient(
            url="http://auth.test",
            http_session=AsyncHttpxSession(
                client=AsyncClient(transport=MockTransport(self.handle))
            ),
            auto_refresh_token=False,
        )


async def test_concurrent_get_session_calls_share_one_refresh() -> None:
    endpoint = AsyncRefreshGate()
    client = endpoint.client()
    await client.session_manager.save_session(expired_session())
    changes: list[AuthStateChange] = []
    client.on_auth_state_change(changes.append)

    waiters = [asyncio.create_task(client.get_session()) for _ in range(5)]
    await asyncio.wait_for(endpoint.started.wait(), timeout=1)
    endpoint.gate.set()
    sessions = await asyncio.gather(*waiters)

    assert len(endpoint.requests) == 1
    assert {session.access_token for session in sessions if session} == {"new-access"}
    assert [change.event for change in changes] == [
        AuthChangeEvent.INITIAL_SESSION,
        AuthChangeEvent.TOKEN_REFRESHED,
    ]


async def test_cancelling_one_waiter_keeps_the_refresh_for_the_others() -> None:
    endpoint = AsyncRefreshGate()
    client = endpoint.client()
    await client.session_manager.save_session(expired_session())

    first = asyncio.create_task(client.get_session())
    second = asyncio.create_task(client.get_session())
    await asyncio.wait_for(endpoint.started.wait(), timeout=1)
    first.cancel()
    await asyncio.sleep(0)
    endpoint.gate.set()
    session = await asyncio.wait_for(second, timeout=1)

    assert first.cancelled()
    assert session is not None
    assert session.access_token == "new-access"
    assert len(endpoint.requests) == 1


async def test_a_refresh_started_by_a_cancelled_caller_is_still_saved() -> None:
    endpoint = AsyncRefreshGate()
    client = endpoint.client()
    manager = client.session_manager
    await manager.save_session(expired_session())

    only = asyncio.create_task(client.get_session())
    await asyncio.wait_for(endpoint.started.wait(), timeout=1)
    only.cancel()
    await asyncio.sleep(0)
    endpoint.gate.set()
    refresh = manager._refresh_task
    assert refresh is not None
    await asyncio.wait_for(refresh, timeout=1)

    stored = await manager.storage.get_item(manager.storage_key)
    assert stored is not None
    assert Session.model_validate_json(stored).access_token == "new-access"


def test_concurrent_sync_get_session_calls_share_one_refresh() -> None:
    requests: list[Request] = []
    lock = threading.Lock()

    def handler(request: Request) -> Response:
        with lock:
            requests.append(request)
        time.sleep(0.1)
        return refreshed(request)

    client = SyncSupabaseAuthClient(
        url="http://auth.test",
        http_session=HttpxSession(client=Client(transport=MockTransport(handler))),
        auto_refresh_token=False,
    )
    client.session_manager.save_session(expired_session())

    def get_session(_worker: int) -> Session | None:
        return client.get_session()

    with ThreadPoolExecutor(max_workers=5) as pool:
        sessions = list(pool.map(get_session, range(5)))

    assert len(requests) == 1
    assert {session.access_token for session in sessions if session} == {"new-access"}
