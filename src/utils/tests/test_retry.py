from datetime import UTC, datetime, timedelta
from email.utils import format_datetime
from types import SimpleNamespace
from typing import Any

import pytest
from supabase_utils.http import retry
from supabase_utils.http.errors import RequestTimeoutError, SupabaseTransportError
from supabase_utils.http.headers import Headers
from supabase_utils.http.request import HTTPRequestMethod, Request, Response
from supabase_utils.http.retry import (
    DEFAULT_RETRYABLE_METHODS,
    DEFAULT_RETRYABLE_STATUSES,
    RetryPolicy,
    _policy_for,
    _retry_after,
)
from yarl import URL

NO_JITTER = RetryPolicy(jitter=0)


def make_request(
    method: HTTPRequestMethod = "GET", retry: RetryPolicy | bool | None = None
) -> Request:
    return Request(
        url=URL("https://example.com/items"),
        method=method,
        headers=Headers.empty(),
        content=None,
        delay=None,
        retry=retry,
    )


def make_response(status: int, headers: dict[str, str] | None = None) -> Response:
    return Response(
        headers=Headers.from_mapping(headers or {}),
        content=b"",
        status=status,
        request=make_request(),
    )


def http_date(delta: timedelta) -> str:
    return format_datetime(datetime.now(UTC) + delta, usegmt=True)


@pytest.fixture
def random_draw(monkeypatch: pytest.MonkeyPatch) -> list[float]:
    """The values `random.random()` returns in `backoff`, consumed in order."""
    draws: list[float] = []
    monkeypatch.setattr(retry, "random", SimpleNamespace(random=lambda: draws.pop(0)))
    return draws


def test_defaults() -> None:
    policy = RetryPolicy()
    assert policy.max_retries == 3
    assert policy.base_delay == 0.5
    assert policy.max_delay == 30
    assert policy.jitter == 0.5
    assert policy.retryable_statuses == DEFAULT_RETRYABLE_STATUSES
    assert policy.retryable_methods == DEFAULT_RETRYABLE_METHODS
    assert policy.retry_network_errors is True
    assert 429 in DEFAULT_RETRYABLE_STATUSES
    assert 500 not in DEFAULT_RETRYABLE_STATUSES
    assert set(DEFAULT_RETRYABLE_METHODS) == {"GET", "HEAD"}


def test_sets_are_frozen_and_the_policy_hashable() -> None:
    policy = RetryPolicy(retryable_statuses={503}, retryable_methods={"GET", "POST"})
    assert policy.retryable_statuses == frozenset({503})
    assert isinstance(policy.retryable_statuses, frozenset)
    assert isinstance(policy.retryable_methods, frozenset)
    assert hash(policy) == hash(
        RetryPolicy(retryable_statuses={503}, retryable_methods={"POST", "GET"})
    )


@pytest.mark.parametrize(
    ("kwargs", "message"),
    [
        ({"max_retries": -1}, "max_retries must be a non-negative integer"),
        ({"base_delay": -1}, "base_delay must be a non-negative number"),
        ({"base_delay": float("nan")}, "base_delay must be a non-negative number"),
        ({"base_delay": float("inf")}, "base_delay must be a non-negative number"),
        ({"max_delay": 0.1}, "max_delay must be a number of seconds of at least"),
        ({"max_delay": float("nan")}, "max_delay must be a number of seconds"),
        ({"max_delay": float("inf")}, "max_delay must be a number of seconds"),
        ({"jitter": -0.1}, "jitter must be between 0 and 1"),
        ({"jitter": 1.1}, "jitter must be between 0 and 1"),
        ({"jitter": float("nan")}, "jitter must be between 0 and 1"),
    ],
)
def test_invalid_options_are_rejected(kwargs: dict[str, Any], message: str) -> None:
    with pytest.raises(ValueError, match=message):
        RetryPolicy(**kwargs)


def test_zero_delays_are_allowed() -> None:
    policy = RetryPolicy(base_delay=0, max_delay=0)
    assert policy.backoff(1) == 0
    assert policy.backoff(5) == 0


@pytest.mark.parametrize(
    ("retry", "seconds"),
    [(1, 0.5), (2, 1), (3, 2), (4, 4), (6, 16), (7, 30), (100, 30), (10_000, 30)],
)
def test_backoff_doubles_from_the_base_delay_up_to_the_cap(
    retry: int, seconds: float
) -> None:
    assert NO_JITTER.backoff(retry) == seconds


def test_backoff_rejects_a_retry_below_one() -> None:
    with pytest.raises(ValueError, match="retry must be a positive integer"):
        NO_JITTER.backoff(0)


def test_backoff_shortens_the_delay_by_up_to_the_jitter_fraction(
    random_draw: list[float],
) -> None:
    random_draw.extend([0.0, 1.0, 0.5])
    policy = RetryPolicy(jitter=0.5)
    assert policy.backoff(1) == 0.5
    assert policy.backoff(1) == 0.25
    assert policy.backoff(1) == 0.375


def test_backoff_jitter_stays_within_the_delay() -> None:
    policy = RetryPolicy(jitter=1)
    delays = [policy.backoff(3) for _ in range(200)]
    assert all(0 <= delay <= 2 for delay in delays)
    assert len(set(delays)) > 1


@pytest.mark.parametrize(
    ("value", "seconds"),
    [("5", 5.0), (" 7 ", 7.0), ("120", 120.0)],
)
def test_retry_after_in_seconds(value: str, seconds: float) -> None:
    assert _retry_after(Headers.from_mapping({"Retry-After": value})) == seconds


def test_retry_after_as_a_date_in_the_future() -> None:
    headers = Headers.from_mapping({"Retry-After": http_date(timedelta(seconds=10))})
    seconds = _retry_after(headers)
    assert seconds is not None
    assert 8 < seconds <= 10


@pytest.mark.parametrize(
    "value",
    ["0", "-3", "1.5", "soon", "", "Mon, 32 Foo 2026 00:00:00 GMT"],
)
def test_unusable_retry_after_is_ignored(value: str) -> None:
    assert _retry_after(Headers.from_mapping({"Retry-After": value})) is None


def test_retry_after_in_the_past_is_ignored() -> None:
    headers = Headers.from_mapping({"Retry-After": http_date(timedelta(seconds=-10))})
    assert _retry_after(headers) is None


def test_missing_retry_after() -> None:
    assert _retry_after(Headers.empty()) is None


@pytest.mark.parametrize("status", sorted(DEFAULT_RETRYABLE_STATUSES))
def test_delay_backs_off_after_a_retryable_status(status: int) -> None:
    assert NO_JITTER.delay(make_response(status), 0) == 0.5
    assert NO_JITTER.delay(make_response(status), 1) == 1
    assert NO_JITTER.delay(make_response(status), 2) == 2


@pytest.mark.parametrize("status", [200, 204, 400, 401, 404, 409, 500, 501])
def test_delay_is_none_for_other_statuses(status: int) -> None:
    assert NO_JITTER.delay(make_response(status), 0) is None


def test_delay_is_none_once_the_retries_are_used_up() -> None:
    assert NO_JITTER.delay(make_response(503), 3) is None
    assert RetryPolicy(max_retries=0).delay(make_response(503), 0) is None
    assert RetryPolicy(max_retries=1, jitter=0).delay(make_response(503), 0) == 0.5
    assert RetryPolicy(max_retries=1).delay(make_response(503), 1) is None


def test_delay_honors_retry_after_without_jitter(random_draw: list[float]) -> None:
    response = make_response(429, {"Retry-After": "3"})
    assert RetryPolicy().delay(response, 0) == 3
    assert random_draw == []


def test_delay_honors_a_retry_after_date() -> None:
    response = make_response(503, {"Retry-After": http_date(timedelta(seconds=20))})
    seconds = RetryPolicy().delay(response, 0)
    assert seconds is not None
    assert 18 < seconds <= 20


def test_delay_is_none_when_retry_after_exceeds_the_max_delay() -> None:
    assert RetryPolicy().delay(make_response(429, {"Retry-After": "31"}), 0) is None
    assert RetryPolicy().delay(make_response(429, {"Retry-After": "30"}), 0) == 30
    assert (
        RetryPolicy(max_delay=60).delay(make_response(429, {"Retry-After": "31"}), 0)
        == 31
    )


def test_delay_ignores_retry_after_on_a_status_that_is_not_retried() -> None:
    assert RetryPolicy().delay(make_response(400, {"Retry-After": "1"}), 0) is None


def test_delay_backs_off_after_an_unusable_retry_after() -> None:
    assert NO_JITTER.delay(make_response(503, {"Retry-After": "0"}), 0) == 0.5


@pytest.mark.parametrize(
    "error",
    [SupabaseTransportError(make_request()), RequestTimeoutError(make_request())],
)
def test_delay_backs_off_after_a_network_error(error: SupabaseTransportError) -> None:
    assert NO_JITTER.delay(error, 0) == 0.5
    assert NO_JITTER.delay(error, 2) == 2
    assert NO_JITTER.delay(error, 3) is None


def test_delay_is_none_for_a_network_error_when_those_are_not_retried() -> None:
    policy = RetryPolicy(retry_network_errors=False)
    assert policy.delay(SupabaseTransportError(make_request()), 0) is None
    assert policy.delay(make_response(503), 0) is not None


def test_custom_statuses_replace_the_defaults() -> None:
    policy = RetryPolicy(retryable_statuses={500}, jitter=0)
    assert policy.delay(make_response(500), 0) == 0.5
    assert policy.delay(make_response(503), 0) is None


@pytest.mark.parametrize("method", ["GET", "HEAD"])
def test_policy_for_retries_idempotent_requests_by_default(
    method: HTTPRequestMethod,
) -> None:
    assert _policy_for(make_request(method), NO_JITTER) is NO_JITTER


@pytest.mark.parametrize("method", ["POST", "PUT", "PATCH", "DELETE"])
def test_policy_for_leaves_other_requests_alone_by_default(
    method: HTTPRequestMethod,
) -> None:
    assert _policy_for(make_request(method), NO_JITTER) is None


def test_policy_for_true_retries_the_request_whatever_its_method() -> None:
    assert _policy_for(make_request("POST", retry=True), NO_JITTER) is NO_JITTER


def test_policy_for_false_never_retries_the_request() -> None:
    assert _policy_for(make_request("GET", retry=False), NO_JITTER) is None


def test_policy_for_uses_the_policy_of_the_request_with_its_own_methods() -> None:
    own = RetryPolicy(max_retries=1)
    assert _policy_for(make_request("GET", retry=own), NO_JITTER) is own
    assert _policy_for(make_request("POST", retry=own), NO_JITTER) is None
    writes = RetryPolicy(retryable_methods={"POST"})
    assert _policy_for(make_request("POST", retry=writes), NO_JITTER) is writes
    assert _policy_for(make_request("GET", retry=writes), NO_JITTER) is None


def test_policy_for_uses_the_methods_of_the_default_policy() -> None:
    uploads = RetryPolicy(retryable_methods={"GET", "HEAD", "PUT"})
    assert _policy_for(make_request("PUT"), uploads) is uploads
    assert _policy_for(make_request("POST"), uploads) is None
