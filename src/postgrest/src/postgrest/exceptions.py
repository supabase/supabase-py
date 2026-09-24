from typing import Any, Dict, Optional

from pydantic import BaseModel


class APIErrorFromJSON(BaseModel):
    """
    A pydantic object to validate an error info object
    from a json string.
    """

    message: Optional[str]
    """The error message."""
    code: Optional[str]
    """The error code."""
    hint: Optional[str]
    """The error hint."""
    details: Optional[str]
    """The error details."""


class APIError(Exception):
    """
    Base exception for all API errors.
    """

    _raw_error: Dict[str, str]
    message: Optional[str]
    """The error message."""
    code: Optional[str]
    """The error code."""
    hint: Optional[str]
    """The error hint."""
    details: Optional[str]
    """The error details."""
    request_url: Optional[str]
    """The URL of the request that caused the error."""

    def __init__(
        self, error: Dict[str, Any], request_url: Optional[str] = None
    ) -> None:
        self._raw_error = error
        self.message = error.get("message")
        self.code = error.get("code")
        self.hint = error.get("hint")
        self.details = error.get("details")
        self.request_url = request_url

        error_message = str(error)
        if request_url:
            error_message = f"{error_message}\nRequest URL: {request_url}"

        Exception.__init__(self, error_message)

    def __repr__(self) -> str:
        error_text = f"Error {self.code}:" if self.code else ""
        message_text = f"\nMessage: {self.message}" if self.message else ""
        hint_text = f"\nHint: {self.hint}" if self.hint else ""
        details_text = f"\nDetails: {self.details}" if self.details else ""
        request_url_text = (
            f"\nRequest URL: {self.request_url}" if self.request_url else ""
        )
        complete_error_text = (
            f"{error_text}{message_text}{hint_text}{details_text}{request_url_text}"
        )
        return complete_error_text or "Empty error"

    def json(self) -> Dict[str, str]:
        """Convert the error into a dictionary.

        Returns:
            :class:`dict`
        """
        return self._raw_error


def generate_default_error_message(r):
    return {
        "message": "JSON could not be generated",
        "code": r.status_code,
        "hint": "Refer to full message for details",
        "details": str(r.content),
    }
