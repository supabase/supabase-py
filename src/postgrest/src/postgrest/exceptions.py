from typing import Any, Dict, Optional

from httpx import Response
from pydantic import BaseModel


class APIErrorFromJSON(BaseModel):
    """
    A pydantic object to validate an error info object
    from a json string.
    """

    message: Optional[str] = None
    """The error message."""
    code: Optional[str] = None
    """The error code."""
    hint: Optional[str] = None
    """The error hint."""
    details: Optional[Any] = None
    """The error details."""


class APIError(Exception):
    """
    Base exception for all API errors.
    """

    _raw_error: Dict[str, Any]
    message: Optional[str]
    """The error message."""
    code: Optional[str]
    """The error code."""
    hint: Optional[str]
    """The error hint."""
    details: Optional[Any]
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

    def json(self) -> Dict[str, Any]:
        """Convert the error into a dictionary.

        Returns:
            :class:`dict`
        """
        return self._raw_error


def _proxy_status_error_code(r: Response) -> Optional[str]:
    proxy_status: str = r.headers.get("Proxy-Status", "")
    for param in proxy_status.split(";")[1:]:
        key, _, value = param.strip().partition("=")
        if key == "error" and value:
            return value.strip('"')
    return None


def generate_default_error_message(r):
    if not r.content:
        # HEAD responses have no body, so PostgREST reports the error code
        # in the Proxy-Status header instead.
        return {
            "message": r.reason_phrase or f"Request failed with status {r.status_code}",
            "code": _proxy_status_error_code(r) or r.status_code,
            "hint": None,
            "details": None,
        }
    return {
        "message": "JSON could not be generated",
        "code": r.status_code,
        "hint": "Refer to full message for details",
        "details": str(r.content),
    }
