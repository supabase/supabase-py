from __future__ import annotations

import re
from email.message import Message
from http import HTTPStatus
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
            `dict`
        """
        return self._raw_error


def generate_default_error_message(response: Response) -> dict[str, Any]:
    """The fields of an `APIError` for an error response whose body is not
    PostgREST JSON, because there is none, as for a HEAD request, or because
    a proxy answered instead, as with an HTML error page.

    The message is the HTTP status phrase and `details` the decoded body.
    PostgREST puts the error code of a bodiless response in the `Proxy-Status`
    header, so the code comes from there when it is set and is the HTTP
    status otherwise.
    """
    return {
        "message": _status_phrase(response.status),
        "code": _proxy_status_error_code(response) or str(response.status),
        "hint": None,
        "details": _decode_body(response),
    }


def _decode_body(response: Response) -> str | None:
    """The body of `response` as text, in the charset of its `Content-Type`
    when it names one the Python codecs know, else as UTF-8 with undecodable
    bytes replaced. None when the response has no body."""
    if not response.content:
        return None
    try:
        return response.content.decode(_charset(response))
    except (LookupError, UnicodeDecodeError):
        return response.content.decode("utf-8", errors="replace")


def _charset(response: Response) -> str:
    content_type = Message()
    content_type["Content-Type"] = response.headers.get("Content-Type") or ""
    return content_type.get_content_charset() or "utf-8"


def _status_phrase(status: int) -> str:
    try:
        return HTTPStatus(status).phrase
    except ValueError:
        return f"Request failed with status {status}"


def _proxy_status_error_code(response: Response) -> str | None:
    """The `error` parameter of the `PostgREST` member of the `Proxy-Status`
    header, a structured field list (RFC 9209) in which each intermediary
    gets a member, as in `cdn; error=connection_timeout, PostgREST;
    error=PGRST301`. None when PostgREST set no member or no error."""
    proxy_status = response.headers.get("Proxy-Status") or ""
    for member in _split_outside_quotes(proxy_status, ","):
        name, *parameters = _split_outside_quotes(member, ";")
        if _unquote(name).lower() != "postgrest":
            continue
        for parameter in parameters:
            key, _, value = parameter.partition("=")
            if key.strip() == "error":
                return _unquote(value) or None
    return None


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
