import json
from typing import Any, Callable, List

import pytest
from httpx import Client, MockTransport, Request, Response
from supabase_auth import SyncGoTrueClient
from supabase_auth.constants import EXPIRY_MARGIN
from supabase_auth.timer import Timer


@pytest.mark.parametrize("persist_session", [True, False])
def test_auto_refresh_tick_sends_one_refresh_request(
    monkeypatch: pytest.MonkeyPatch, persist_session: bool
) -> None:
    ticks: List[Callable[[], Any]] = []

    def schedule(timer: Any) -> None:
        ticks.append(timer._function)

    # Run each tick by hand instead of waiting for the real timer.
    monkeypatch.setattr(Timer, "start", schedule)

    refresh_tokens: List[str] = []

    def handler(request: Request) -> Response:
        if request.url.params["grant_type"] == "refresh_token":
            refresh_tokens.append(json.loads(request.content)["refresh_token"])
        n = len(refresh_tokens)
        return Response(
            200,
            json={
                "access_token": f"access-{n}",
                "refresh_token": f"refresh-{n}",
                "token_type": "bearer",
                # The tick fires once the session is inside EXPIRY_MARGIN.
                "expires_in": EXPIRY_MARGIN,
                "user": {
                    "id": "00000000-0000-4000-8000-000000000001",
                    "aud": "authenticated",
                    "app_metadata": {},
                    "user_metadata": {},
                    "created_at": "2024-01-01T00:00:00Z",
                },
            },
        )

    with Client(transport=MockTransport(handler)) as http_client:
        client = SyncGoTrueClient(
            url="https://example.supabase.co/auth/v1",
            http_client=http_client,
            persist_session=persist_session,
        )
        client.sign_in_with_password(
            {"email": "user@example.com", "password": "password"}
        )
        for tick in range(1, 4):
            assert len(ticks) == 1
            ticks.pop()()
            assert refresh_tokens == [f"refresh-{i}" for i in range(tick)]
