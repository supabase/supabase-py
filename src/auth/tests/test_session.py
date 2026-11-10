import time

import pytest

from supabase_auth.constants import MAX_RETRIES
from supabase_auth.session import _retry_delay
from supabase_auth.types import Session, User


@pytest.mark.parametrize(
    ("attempt", "seconds"),
    [(1, 0.2), (2, 0.4), (3, 0.8), (4, 1.6), (8, 25.6), (MAX_RETRIES - 1, 30)],
)
def test_retry_delay_starts_at_200_milliseconds_and_doubles_up_to_30_seconds(
    attempt: int, seconds: float
) -> None:
    assert _retry_delay(attempt) == pytest.approx(seconds)


def test_a_session_without_a_lifetime_expires_now() -> None:
    session = Session(
        access_token="access",
        refresh_token="refresh",
        token_type="bearer",
        expires_in=0,
        user=User.model_validate(
            {
                "id": "11111111-1111-1111-1111-111111111111",
                "aud": "authenticated",
                "app_metadata": {},
                "user_metadata": {},
                "created_at": "2026-01-01T00:00:00Z",
            }
        ),
    )

    assert session.expires_at is not None
    assert abs(session.expires_at - time.time()) <= 1
