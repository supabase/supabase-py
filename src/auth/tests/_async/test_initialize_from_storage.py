import time
from collections.abc import Callable

import pytest
from httpx import AsyncClient, MockTransport, Request, Response
from supabase_auth import AsyncGoTrueClient
from supabase_auth.errors import AuthApiError
from supabase_auth.types import Session, User

USER = {
    "id": "11111111-1111-1111-1111-111111111111",
    "aud": "authenticated",
    "app_metadata": {},
    "user_metadata": {},
    "created_at": "2024-01-01T00:00:00Z",
}

Handler = Callable[[Request], Response]


def refreshed_session_response(request: Request) -> Response:
    return Response(
        200,
        json={
            "access_token": "new-access",
            "refresh_token": "new-refresh",
            "token_type": "bearer",
            "expires_in": 3600,
            "expires_at": int(time.time()) + 3600,
            "user": USER,
        },
    )


def failed_refresh_response(request: Request) -> Response:
    return Response(
        400,
        json={
            "code": 400,
            "error_code": "refresh_token_not_found",
            "msg": "Invalid Refresh Token: Refresh Token Not Found",
        },
    )


def unavailable_response(request: Request) -> Response:
    return Response(503, json={"msg": "Service Unavailable"})


def stored_session(expires_at: int, refresh_token: str) -> Session:
    return Session(
        access_token="old-access",
        refresh_token=refresh_token,
        token_type="bearer",
        expires_in=3600,
        expires_at=expires_at,
        user=User.model_validate(USER),
    )


def recording_transport(handler: Handler, requests: list[Request]) -> MockTransport:
    def record(request: Request) -> Response:
        requests.append(request)
        return handler(request)

    return MockTransport(record)


async def client_with_stored_session(
    http_client: AsyncClient,
    auto_refresh_token: bool,
    expires_at: int,
    refresh_token: str = "old-refresh",
) -> AsyncGoTrueClient:
    client = AsyncGoTrueClient(
        url="http://auth.test",
        auto_refresh_token=auto_refresh_token,
        http_client=http_client,
    )
    await client._storage.set_item(
        client._storage_key,
        stored_session(expires_at, refresh_token).model_dump_json(),
    )
    return client


async def stored_access_token(client: AsyncGoTrueClient) -> str | None:
    raw_session = await client._storage.get_item(client._storage_key)
    session = client._get_valid_session(raw_session)
    return session.access_token if session else None


async def test_initialize_from_storage_keeps_expired_session_without_auto_refresh() -> (
    None
):
    requests: list[Request] = []
    transport = recording_transport(refreshed_session_response, requests)
    async with AsyncClient(transport=transport) as http_client:
        client = await client_with_stored_session(
            http_client, False, int(time.time()) - 60
        )

        await client.initialize_from_storage()

        assert requests == []
        assert await stored_access_token(client) == "old-access"

        session = await client.get_session()

        assert session is not None
        assert session.access_token == "new-access"
        assert len(requests) == 1
        assert await stored_access_token(client) == "new-access"


async def test_initialize_from_storage_keeps_session_within_expiry_margin_without_auto_refresh() -> (
    None
):
    requests: list[Request] = []
    transport = recording_transport(refreshed_session_response, requests)
    async with AsyncClient(transport=transport) as http_client:
        client = await client_with_stored_session(
            http_client, False, int(time.time()) + 5
        )

        await client.initialize_from_storage()

        assert requests == []
        assert await stored_access_token(client) == "old-access"


async def test_get_session_raises_when_kept_session_refresh_is_rejected() -> None:
    requests: list[Request] = []
    transport = recording_transport(failed_refresh_response, requests)
    async with AsyncClient(transport=transport) as http_client:
        client = await client_with_stored_session(
            http_client, False, int(time.time()) - 60
        )

        await client.initialize_from_storage()
        assert await stored_access_token(client) == "old-access"

        with pytest.raises(AuthApiError):
            await client.get_session()

        assert len(requests) == 1


async def test_initialize_from_storage_removes_expired_session_without_refresh_token() -> (
    None
):
    requests: list[Request] = []
    transport = recording_transport(refreshed_session_response, requests)
    async with AsyncClient(transport=transport) as http_client:
        client = await client_with_stored_session(
            http_client, False, int(time.time()) - 60, refresh_token=""
        )

        await client.initialize_from_storage()

        assert requests == []
        assert await client._storage.get_item(client._storage_key) is None


async def test_initialize_from_storage_refreshes_expired_session_with_auto_refresh() -> (
    None
):
    requests: list[Request] = []
    transport = recording_transport(refreshed_session_response, requests)
    async with AsyncClient(transport=transport) as http_client:
        client = await client_with_stored_session(
            http_client, True, int(time.time()) - 60
        )

        await client.initialize_from_storage()

        assert len(requests) == 1
        assert await stored_access_token(client) == "new-access"
        session = await client.get_session()
        assert session is not None
        assert session.access_token == "new-access"
        assert len(requests) == 1
        await client._remove_session()


async def test_initialize_from_storage_removes_session_when_auto_refresh_fails() -> (
    None
):
    requests: list[Request] = []
    transport = recording_transport(failed_refresh_response, requests)
    async with AsyncClient(transport=transport) as http_client:
        client = await client_with_stored_session(
            http_client, True, int(time.time()) - 60
        )

        await client.initialize_from_storage()

        assert len(requests) == 1
        assert await client._storage.get_item(client._storage_key) is None


async def test_initialize_from_storage_keeps_session_and_retries_on_retryable_error() -> (
    None
):
    requests: list[Request] = []
    transport = recording_transport(unavailable_response, requests)
    async with AsyncClient(transport=transport) as http_client:
        client = await client_with_stored_session(
            http_client, True, int(time.time()) - 60
        )

        await client.initialize_from_storage()

        assert len(requests) == 1
        assert await stored_access_token(client) == "old-access"
        assert client._refresh_token_timer is not None
        await client._remove_session()
