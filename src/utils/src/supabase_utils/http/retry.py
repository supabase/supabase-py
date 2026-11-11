from __future__ import annotations

import math
import random
from collections.abc import Set as AbstractSet
from dataclasses import dataclass
from datetime import UTC, datetime
from email.utils import parsedate_to_datetime
from typing import TYPE_CHECKING, get_args

from ..types import HTTPRequestMethod
from .errors import SupabaseTransportError

if TYPE_CHECKING:
    from .headers import Headers
    from .request import Request, Response

DEFAULT_RETRYABLE_STATUSES: frozenset[int] = frozenset(
    {408, 429, 502, 503, 504, 520, 521, 522, 523, 524, 530}
)
"""The statuses a `RetryPolicy` retries by default: a request timeout, a rate
limit, a gateway error, and the Cloudflare statuses for an edge that could
not reach the project. A 500 is left out, since PostgREST answers a failing
query with it and a retry fails the same way."""

DEFAULT_RETRYABLE_METHODS: frozenset[HTTPRequestMethod] = frozenset({"GET", "HEAD"})
"""The methods a `RetryPolicy` retries by default. GET and HEAD requests are
idempotent for every Supabase service, so a request that may have reached
the service can be sent again."""

_MAX_EXPONENT = 64
_METHODS: frozenset[str] = frozenset(get_args(HTTPRequestMethod))


def _retry_after(headers: Headers) -> float | None:
    """Seconds a `Retry-After` header asks to wait, or None when there is no
    such header or it carries no usable timing.

    The header holds either a number of seconds or an HTTP date. Zero seconds
    and a date that is not in the future are ignored, since waiting nothing
    would make every client that saw the header send again at the same time.
    """
    value = headers.get("Retry-After")
    if value is None:
        return None
    value = value.strip()
    if value.isdecimal():
        seconds = int(value)
        return float(seconds) if seconds > 0 else None
    try:
        date = parsedate_to_datetime(value)
    except (TypeError, ValueError, IndexError):
        return None
    if date.tzinfo is None:
        date = date.replace(tzinfo=UTC)
    seconds_until = (date - datetime.now(UTC)).total_seconds()
    return seconds_until if seconds_until > 0 else None


@dataclass(frozen=True, kw_only=True)
class RetryPolicy:
    """How the executors retry a request that failed in a way worth repeating.

    A request is retried when its method is in `retryable_methods`, or when
    it was sent with `retry=True` or a policy of its own, and the attempt
    either answered with a status in `retryable_statuses` or failed with a
    `SupabaseTransportError` while `retry_network_errors` is set. The wait
    before a retry is the `Retry-After` the response asked for, up to
    `max_delay`, and otherwise an exponential backoff from `base_delay` with
    jitter.

    Pass one to the client of a service, or to the supabase client for every
    service, and `max_retries=0` to not retry at all:

    ```python
    supabase = create_client(
        url,
        key,
        retry=RetryPolicy(max_retries=5),
        storage=StorageClientOptions(retry=RetryPolicy(max_retries=0)),
    )
    ```
    """

    max_retries: int = 3
    """How many times a request is sent again after its first attempt. 0 sends
    every request exactly once."""

    base_delay: float = 0.5
    """Seconds to wait before the first retry. The wait doubles for every retry
    after it."""

    max_delay: float = 30.0
    """The longest wait between two attempts, in seconds. A response whose
    `Retry-After` asks for a longer wait is not retried, so that a caller is
    not held up for longer than it allowed. Raise it to wait for such a
    response."""

    jitter: float = 0.5
    """The fraction of a backoff wait that is randomized. Each wait is the
    backoff shortened at random by up to this fraction of it, which keeps many
    clients from retrying in lockstep. 0 waits the backoff exactly."""

    retryable_statuses: AbstractSet[int] = DEFAULT_RETRYABLE_STATUSES
    """The response statuses that are retried."""

    retryable_methods: AbstractSet[HTTPRequestMethod] = DEFAULT_RETRYABLE_METHODS
    """The request methods that are retried when the request does not say
    itself whether it is. Add a method only when every request a client sends
    with it is safe to send twice."""

    retry_network_errors: bool = True
    """Whether a request that failed with a `SupabaseTransportError`, because
    the connection failed or the request timed out, is retried. Such a request
    may have reached the service, which is why only the `retryable_methods`
    are retried. A retried timeout waits the `request_timeout` again."""

    def __post_init__(self) -> None:
        if not (isinstance(self.max_retries, int) and self.max_retries >= 0):
            raise ValueError(
                f"max_retries must be a non-negative integer, not {self.max_retries!r}"
            )
        if not (math.isfinite(self.base_delay) and self.base_delay >= 0):
            raise ValueError(
                "base_delay must be a non-negative number of seconds, "
                f"not {self.base_delay!r}"
            )
        if not (math.isfinite(self.max_delay) and self.max_delay >= self.base_delay):
            raise ValueError(
                f"max_delay must be a number of seconds of at least base_delay, "
                f"not {self.max_delay!r}"
            )
        if not 0 <= self.jitter <= 1:
            raise ValueError(f"jitter must be between 0 and 1, not {self.jitter!r}")
        methods = frozenset(method.upper() for method in self.retryable_methods)
        if unknown := methods - _METHODS:
            raise ValueError(
                f"retryable_methods must be HTTP request methods, not {sorted(unknown)}"
            )
        object.__setattr__(
            self, "retryable_statuses", frozenset(self.retryable_statuses)
        )
        object.__setattr__(self, "retryable_methods", methods)

    def backoff(self, retry: int) -> float:
        """Seconds to wait before the `retry`-th retry, counted from 1: the
        `base_delay` doubled for every retry before it, capped at `max_delay`
        and shortened at random by up to the `jitter` fraction."""
        if retry < 1:
            raise ValueError(f"retry must be a positive integer, not {retry!r}")
        exponent = min(retry - 1, _MAX_EXPONENT)
        delay = min(self.base_delay * 2.0**exponent, self.max_delay)
        return delay * (1 - self.jitter * random.random())

    def delay(
        self, outcome: Response | SupabaseTransportError, retries: int
    ) -> float | None:
        """Seconds to wait before sending a request again after `outcome`, the
        response it got or the transport error that failed it, when `retries`
        retries were made before.

        None when the request is not sent again: the retries are used up, the
        outcome is not one this policy retries, or the response asks with
        `Retry-After` for a wait longer than `max_delay`.
        """
        if retries >= self.max_retries:
            return None
        if isinstance(outcome, SupabaseTransportError):
            return self.backoff(retries + 1) if self.retry_network_errors else None
        if outcome.status not in self.retryable_statuses:
            return None
        requested = _retry_after(outcome.headers)
        if requested is None:
            return self.backoff(retries + 1)
        return requested if requested <= self.max_delay else None


def _policy_for(request: Request, default: RetryPolicy) -> RetryPolicy | None:
    """The policy that retries `request`, or None when it is never retried.

    `request.retry` decides: None leaves it to `default`, which retries the
    request when its method is one of its `retryable_methods`. True retries it
    with `default` whatever its method, False never retries it, and a
    `RetryPolicy` retries it with that policy whatever its method.
    """
    if request.retry is None:
        return default if request.method in default.retryable_methods else None
    if request.retry is False:
        return None
    return default if request.retry is True else request.retry
