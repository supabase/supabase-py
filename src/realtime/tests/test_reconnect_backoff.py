from unittest.mock import patch

import pytest

from realtime.client import MAX_RECONNECT_DELAY, reconnect_delay


def upper_bound(low: float, high: float) -> float:
    return high


def test_the_backoff_doubles_from_one_second_and_is_capped() -> None:
    with patch("realtime.client.random.uniform", upper_bound):
        delays = [reconnect_delay(attempt) for attempt in range(1, 9)]

    assert delays == [1, 2, 4, 8, 16, 30, 30, 30]
    assert MAX_RECONNECT_DELAY == 30


def test_the_backoff_does_not_overflow_after_many_attempts() -> None:
    with patch("realtime.client.random.uniform", upper_bound):
        assert reconnect_delay(100_000) == MAX_RECONNECT_DELAY


@pytest.mark.parametrize("attempt", [1, 3, 6, 50])
def test_each_wait_is_drawn_from_zero_to_the_backoff(attempt: int) -> None:
    for _ in range(200):
        delay = reconnect_delay(attempt)
        assert 0 <= delay <= min(MAX_RECONNECT_DELAY, 2 ** (attempt - 1))
