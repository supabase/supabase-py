from typing import Any, Dict

from pydantic import BaseModel
from supabase_utils.http.request import Response


class APIErrorFromJSON(BaseModel):
    """
    A pydantic object to validate an error info object
    from a json string.
    """

    message: str | None
    """The error message."""
    code: str | None
    """The error code."""
    hint: str | None
    """The error hint."""
    details: str | None
    """The error details."""


class APIError(Exception):
    """
    Base exception for all API errors.
    """

    _raw_error: Dict[str, str]
    message: str | None
    """The error message."""
    code: str | None
    """The error code."""
    hint: str | None
    """The error hint."""
    details: str | None
    """The error details."""

    def __init__(self, error: Dict[str, Any]) -> None:
        self._raw_error = error
        self.message = error.get("message")
        self.code = error.get("code")
        self.hint = error.get("hint")
        self.details = error.get("details")
        Exception.__init__(self, str(self))

    def __repr__(self) -> str:
        error_text = f"Error {self.code}:" if self.code else ""
        message_text = f"\nMessage: {self.message}" if self.message else ""
        hint_text = f"\nHint: {self.hint}" if self.hint else ""
        details_text = f"\nDetails: {self.details}" if self.details else ""
        complete_error_text = f"{error_text}{message_text}{hint_text}{details_text}"
        return complete_error_text or "Empty error"

    def json(self) -> Dict[str, str]:
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
