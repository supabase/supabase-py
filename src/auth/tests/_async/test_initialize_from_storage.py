import json
import sys
import time
from collections.abc import Callable
from unittest.mock import patch

import pytest
from httpx import AsyncClient, MockTransport, Request, Response
from supabase_auth import AsyncGoTrueClient
from supabase_auth.constants import MAX_RETRIES
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


def assert_refresh_requests(requests: list[Request], count: int) -> None:
    assert len(requests) == count
    for request in requests:
        assert request.url.path == "/token"
        assert request.url.params["grant_type"] == "refresh_token"


async def client_with_stored_session(
    handler: Handler,
    requests: list[Request],
    auto_refresh_token: bool,
    expires_at: int,
    refresh_token: str = "old-refresh",
) -> AsyncGoTrueClient:
    client = AsyncGoTrueClient(
        url="http://auth.test",
        auto_refresh_token=auto_refresh_token,
        http_client=AsyncClient(transport=recording_transport(handler, requests)),
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
    client = await client_with_stored_session(
        refreshed_session_response, requests, False, int(time.time()) - 60
    )
    async with client:
        await client.initialize_from_storage()

        assert requests == []
        assert await stored_access_token(client) == "old-access"

        session = await client.get_session()

        assert session is not None
        assert session.access_token == "new-access"
        assert_refresh_requests(requests, 1)
        assert json.loads(requests[0].content) == {"refresh_token": "old-refresh"}
        assert await stored_access_token(client) == "new-access"


async def test_initialize_from_storage_keeps_session_within_expiry_margin_without_auto_refresh() -> (
    None
):
    requests: list[Request] = []
    client = await client_with_stored_session(
        refreshed_session_response, requests, False, int(time.time()) + 5
    )
    async with client:
        await client.initialize_from_storage()

        assert requests == []
        assert await stored_access_token(client) == "old-access"

        session = await client.get_session()

        assert session is not None
        assert session.access_token == "new-access"
        assert_refresh_requests(requests, 1)
        assert json.loads(requests[0].content) == {"refresh_token": "old-refresh"}


async def test_get_session_raises_when_kept_session_refresh_is_rejected() -> None:
    requests: list[Request] = []
    client = await client_with_stored_session(
        failed_refresh_response, requests, False, int(time.time()) - 60
    )
    async with client:
        await client.initialize_from_storage()
        assert await stored_access_token(client) == "old-access"

        with pytest.raises(AuthApiError):
            await client.get_session()

        assert_refresh_requests(requests, 1)


async def test_initialize_from_storage_removes_expired_session_without_refresh_token() -> (
    None
):
    requests: list[Request] = []
    client = await client_with_stored_session(
        refreshed_session_response,
        requests,
        False,
        int(time.time()) - 60,
        refresh_token="",
    )
    async with client:
        await client.initialize_from_storage()

        assert requests == []
        assert await client._storage.get_item(client._storage_key) is None


async def test_initialize_from_storage_refreshes_expired_session_with_auto_refresh() -> (
    None
):
    requests: list[Request] = []
    client = await client_with_stored_session(
        refreshed_session_response, requests, True, int(time.time()) - 60
    )
    async with client:
        await client.initialize_from_storage()

        assert_refresh_requests(requests, 1)
        assert await stored_access_token(client) == "new-access"
        session = await client.get_session()
        assert session is not None
        assert session.access_token == "new-access"
        assert_refresh_requests(requests, 1)
        await client._remove_session()


async def test_initialize_from_storage_removes_session_when_auto_refresh_fails() -> (
    None
):
    requests: list[Request] = []
    client = await client_with_stored_session(
        failed_refresh_response, requests, True, int(time.time()) - 60
    )
    async with client:
        await client.initialize_from_storage()

        assert_refresh_requests(requests, 1)
        assert await client._storage.get_item(client._storage_key) is None


async def test_initialize_from_storage_keeps_session_and_retries_on_retryable_error() -> (
    None
):
    requests: list[Request] = []

    def unavailable_then_refreshed(request: Request) -> Response:
        if len(requests) == 1:
            return unavailable_response(request)
        return refreshed_session_response(request)

    client = await client_with_stored_session(
        unavailable_then_refreshed, requests, True, int(time.time()) - 60
    )
    async with client:
        with patch.object(sys.modules[AsyncGoTrueClient.__module__], "Timer") as timer:
            await client.initialize_from_storage()

            assert_refresh_requests(requests, 1)
            assert await stored_access_token(client) == "old-access"
            timer.assert_called_once()
            timer.return_value.start.assert_called_once()

            await timer.call_args.args[1]()

        assert_refresh_requests(requests, 2)
        assert await stored_access_token(client) == "new-access"
        await client._remove_session()


async def test_initialize_from_storage_removes_session_after_retry_limit() -> None:
    requests: list[Request] = []
    client = await client_with_stored_session(
        unavailable_response, requests, True, int(time.time()) - 60
    )
    async with client:
        with patch.object(sys.modules[AsyncGoTrueClient.__module__], "Timer") as timer:
            await client.initialize_from_storage()
            for _ in range(MAX_RETRIES - 1):
                assert await stored_access_token(client) == "old-access"
                await timer.call_args.args[1]()

        assert_refresh_requests(requests, MAX_RETRIES)
        assert timer.call_count == MAX_RETRIES - 1
        assert await client._storage.get_item(client._storage_key) is None
