import re
from typing import Any

from httpx import Response
from pydantic import BaseModel


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
    details: Any | None = None
    """The error details."""


class APIError(Exception):
    """
    Base exception for all API errors.
    """

    _raw_error: dict[str, Any]
    message: str | None
    """The error message."""
    code: str | None
    """The error code."""
    hint: str | None
    """The error hint."""
    details: Any | None
    """The error details."""

    def __init__(self, error: dict[str, Any]) -> None:
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

    def json(self) -> dict[str, Any]:
        """Convert the error into a dictionary.

        Returns:
            :class:`dict`
        """
        return self._raw_error


def _split_outside_quotes(value: str, separator: str) -> list[str]:
    parts: list[str] = []
    current: list[str] = []
    in_quotes = False
    escaped = False
    for char in value:
        if escaped:
            escaped = False
        elif in_quotes and char == "\\":
            escaped = True
        elif char == '"':
            in_quotes = not in_quotes
        elif char == separator and not in_quotes:
            parts.append("".join(current))
            current = []
            continue
        current.append(char)
    parts.append("".join(current))
    return parts


def _unquote(value: str) -> str:
    value = value.strip()
    if len(value) >= 2 and value[0] == value[-1] == '"':
        return re.sub(r"\\(.)", r"\1", value[1:-1])
    return value


def _proxy_status_error_code(r: Response) -> str | None:
    proxy_status: str = r.headers.get("Proxy-Status", "")
    for member in _split_outside_quotes(proxy_status, ","):
        name, *params = _split_outside_quotes(member, ";")
        if _unquote(name).lower() != "postgrest":
            continue
        for param in params:
            key, _, value = param.partition("=")
            if key.strip() == "error":
                return _unquote(value) or None
        return None
    return None


def generate_default_error_message(r: Response) -> dict[str, Any]:
    # Error bodies that are missing (HEAD) or not PostgREST JSON (for example
    # a proxy error page) do not carry the error code, so read it from the
    # Proxy-Status header when PostgREST set it.
    return {
        "message": r.reason_phrase or f"Request failed with status {r.status_code}",
        "code": _proxy_status_error_code(r) or str(r.status_code),
        "hint": None,
        "details": r.text or None,
    }
