from __future__ import annotations

from typing import TYPE_CHECKING, Any, override

from pydantic import BaseModel
from supabase_utils.http.errors import SupabaseAPIError

if TYPE_CHECKING:
    from supabase_utils.http.request import Response


class APIErrorFromJSON(BaseModel):
    """
    A pydantic object to validate an error info object
    from a json string.
    """

    message: str | None = None
    """The error message."""
    code: str | None = None
    """The error code."""
    hint: str | None = None
    """The error hint."""
    details: Any = None
    """The error details."""


class APIError(SupabaseAPIError):
    """Raised when PostgREST answered a request with an error.

    `message`, `code`, `hint` and `details` are the fields of the error body,
    see https://postgrest.org/en/stable/references/errors.html.
    """

    _raw_error: dict[str, Any]
    hint: str | None
    """The error hint."""
    details: Any
    """The error details."""

    def __init__(
        self,
        error: dict[str, Any],
        *,
        status_code: int,
        response: Response | None = None,
    ) -> None:
        self._raw_error = error
        self.hint = error.get("hint")
        self.details = error.get("details")
        super().__init__(
            error.get("message") or "Unknown error",
            status_code=status_code,
            code=error.get("code"),
            response=response,
        )

    @override
    def __repr__(self) -> str:
        error_text = f"Error {self.code}:" if self.code else ""
        message_text = f"\nMessage: {self.message}" if self.message else ""
        hint_text = f"\nHint: {self.hint}" if self.hint else ""
        details_text = f"\nDetails: {self.details}" if self.details else ""
        complete_error_text = f"{error_text}{message_text}{hint_text}{details_text}"
        return complete_error_text or "Empty error"

    def json(self) -> dict[str, Any]:
        """Convert the error into a dictionary.

        Returns:
            :class:`dict`
        """
        return self._raw_error


def generate_default_error_message(r: Response) -> dict[str, str]:
    return {
        "message": "JSON could not be generated",
        "code": str(r.status),
        "hint": "Refer to full message for details",
        "details": str(r.content),
    }
