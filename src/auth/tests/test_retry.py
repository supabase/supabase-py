from httpx import AsyncClient, Client
from supabase_utils.http.adapters.httpx import AsyncHttpxSession, HttpxSession
from supabase_utils.http.retry import RetryPolicy

from supabase_auth import (
    AsyncSupabaseAuthAdmin,
    AsyncSupabaseAuthClient,
    SyncSupabaseAuthAdmin,
    SyncSupabaseAuthClient,
)

URL = "https://example.supabase.co/auth/v1"


def test_sync_clients_default_to_the_default_retry_policy() -> None:
    with Client() as http_client:
        session = HttpxSession(client=http_client)
        client = SyncSupabaseAuthClient(URL, session)
        admin = SyncSupabaseAuthAdmin(URL, session)
        assert client.executor.retry_policy == RetryPolicy()
        assert client.mfa.executor.retry_policy == RetryPolicy()
        assert admin.executor.retry_policy == RetryPolicy()


def test_sync_clients_pass_the_retry_policy_to_their_executor() -> None:
    policy = RetryPolicy(max_retries=1)
    with Client() as http_client:
        session = HttpxSession(client=http_client)
        client = SyncSupabaseAuthClient(URL, session, retry=policy)
        admin = SyncSupabaseAuthAdmin(URL, session, retry=policy)
        assert client.executor.retry_policy is policy
        assert client.mfa.executor.retry_policy is policy
        assert client.session_manager.executor.retry_policy is policy
        assert admin.executor.retry_policy is policy


async def test_async_clients_pass_the_retry_policy_to_their_executor() -> None:
    policy = RetryPolicy(max_retries=1)
    async with AsyncClient() as http_client:
        session = AsyncHttpxSession(client=http_client)
        client = AsyncSupabaseAuthClient(URL, session, retry=policy)
        admin = AsyncSupabaseAuthAdmin(URL, session, retry=policy)
        assert client.executor.retry_policy is policy
        assert client.mfa.executor.retry_policy is policy
        assert client.session_manager.executor.retry_policy is policy
        assert admin.executor.retry_policy is policy
