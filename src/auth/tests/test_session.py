import pytest

from supabase_auth.constants import MAX_RETRIES
from supabase_auth.session import _retry_delay


@pytest.mark.parametrize(
    ("attempt", "seconds"),
    [(1, 0.2), (2, 0.4), (3, 0.8), (4, 1.6), (8, 25.6), (MAX_RETRIES - 1, 30)],
)
def test_retry_delay_starts_at_200_milliseconds_and_doubles_up_to_30_seconds(
    attempt: int, seconds: float
) -> None:
    assert _retry_delay(attempt) == pytest.approx(seconds)
