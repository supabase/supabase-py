from supabase_auth.constants import get_retry_interval


def test_get_retry_interval_uses_exponential_backoff_in_milliseconds() -> None:
    assert get_retry_interval(1) == 200
    assert get_retry_interval(2) == 400
    assert get_retry_interval(3) == 800


def test_get_retry_interval_stays_within_expected_range_for_max_retries() -> None:
    # Regression check for overflow-prone formula: RETRY_INTERVAL ** (retries * 100)
    assert get_retry_interval(10) == 102400
