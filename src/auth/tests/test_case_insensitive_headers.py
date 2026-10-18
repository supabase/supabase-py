from collections.abc import Callable
from typing import Any

import pytest
from httpx import AsyncClient, Client, MockTransport, Request, Response
from supabase_auth import AsyncGoTrueClient, SyncGoTrueClient

USER = {
    "id": "11111111-1111-1111-1111-111111111111",
    "aud": "authenticated",
    "app_metadata": {},
    "user_metadata": {},
    "created_at": "2026-01-01T00:00:00Z",
}


def _handler(captured: dict[str, Any]) -> Callable[[Request], Response]:
    def handle(request: Request) -> Response:
        captured["api_version"] = request.headers.get_list("x-supabase-api-version")
        return Response(200, json=USER)

    return handle


def test_sync_custom_api_version_header_is_case_insensitive() -> None:
    captured: dict[str, Any] = {}
    client = SyncGoTrueClient(
        url="http://auth.test",
        headers={"x-supabase-api-version": "custom-version"},
        auto_refresh_token=False,
        http_client=Client(transport=MockTransport(_handler(captured))),
    )

    client.get_user("token")

    assert captured["api_version"] == ["custom-version"]


@pytest.mark.asyncio
async def test_async_custom_api_version_header_is_case_insensitive() -> None:
    captured: dict[str, Any] = {}
    client = AsyncGoTrueClient(
        url="http://auth.test",
        headers={"x-supabase-api-version": "custom-version"},
        auto_refresh_token=False,
        http_client=AsyncClient(transport=MockTransport(_handler(captured))),
    )

    await client.get_user("token")

    assert captured["api_version"] == ["custom-version"]
