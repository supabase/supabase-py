from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import ValidationError
from supabase_utils.errors import SupabaseError
from supabase_utils.http.errors import SupabaseAPIError
from supabase_utils.types import JSONParser

if TYPE_CHECKING:
    from supabase_utils.http.request import Response


class FunctionsError(SupabaseError):
    """Raised when invoking an edge function fails."""


class FunctionsHttpError(FunctionsError, SupabaseAPIError):
    """Raised when the edge function answered with an error status."""

    def __init__(
        self, message: str, *, status_code: int, response: Response | None = None
    ) -> None:
        super().__init__(message, status_code=status_code, response=response)


class FunctionsRelayError(FunctionsError, SupabaseAPIError):
    """Raised when the relay in front of the edge function answered with an
    error, marked by the `x-relay-error` header."""

    def __init__(
        self, message: str, *, status_code: int, response: Response | None = None
    ) -> None:
        super().__init__(message, status_code=status_code, response=response)


def _is_relay_error(response: Response) -> bool:
    return response.headers.get("x-relay-error") == "true"


def _error_message_from(response: Response) -> str | None:
    try:
        body = JSONParser.validate_json(response.content)
    except ValidationError:
        body = None
    if isinstance(body, dict):
        error = body.get("error") or body.get("message")
        if isinstance(error, str):
            return error
        if error is not None:
            return JSONParser.dump_json(error).decode("utf-8")
    return response.content.decode("utf-8", errors="replace") or None


def _on_error_response(response: Response) -> FunctionsHttpError | FunctionsRelayError:
    if _is_relay_error(response):
        return FunctionsRelayError(
            response.content.decode("utf-8", errors="replace"),
            status_code=response.status,
            response=response,
        )
    return FunctionsHttpError(
        _error_message_from(response)
        or "An error occurred while requesting your edge function at "
        f"{str(response.request.url)!r}.",
        status_code=response.status,
        response=response,
    )
