from __future__ import annotations

from typing import TYPE_CHECKING

from ..errors import SupabaseError

if TYPE_CHECKING:
    from .request import Request, Response


class SupabaseAPIError(SupabaseError):
    """Raised when a Supabase service answered a request with an error.

    Catch it to handle a failure any service reported:

    ```python
    try:
        client.table("countries").select("*").execute()
    except SupabaseAPIError as error:
        print(error.status_code, error.message)
    ```
    """

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        code: str | None = None,
        response: Response | None = None,
    ) -> None:
        super().__init__(message, code=code)
        self.status_code = status_code
        """HTTP status code of the response that caused the error."""
        self.response = response
        """The response that caused the error. Its `content` is the body as
        the service sent it, and its `headers` carry the `sb-request-id` to
        quote when asking for support. None when the error was built without
        a response, as a client-side check does."""


class SupabaseTransportError(SupabaseError):
    """Raised when a request to a Supabase service never received a response,
    because the connection failed or the request timed out.

    The exception of the HTTP client is chained as `__cause__`. The request
    may still have reached the service, so the outcome of an operation that
    is not idempotent is unknown.

    ```python
    try:
        client.table("countries").select("*").execute()
    except SupabaseTransportError as error:
        print(f"No response: {error.__cause__!r}")
    ```
    """

    def __init__(self, request: Request, reason: str = "failed") -> None:
        self.request = request
        """The request that was sent."""
        super().__init__(f"{request.method} {request.url.with_query(None)} {reason}")


class RequestTimeoutError(SupabaseTransportError, TimeoutError):
    """Raised when a request to a Supabase service times out."""

    def __init__(self, request: Request) -> None:
        super().__init__(request, "timed out")
