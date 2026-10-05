from __future__ import annotations

from typing import TYPE_CHECKING, TypedDict

if TYPE_CHECKING:
    from httpx import Response


class FunctionsApiErrorDict(TypedDict):
    name: str
    message: str
    status: int


class FunctionsError(Exception):
    def __init__(self, message: str, name: str, status: int) -> None:
        super().__init__(message)
        self.message = message
        self.name = name
        self.status = status

    def to_dict(self) -> FunctionsApiErrorDict:
        return {
            "name": self.name,
            "message": self.message,
            "status": self.status,
        }


class FunctionsHttpError(FunctionsError):
    def __init__(self, message: str, code: int | None = None) -> None:
        super().__init__(
            message,
            "FunctionsHttpError",
            400 if code is None else code,
        )


class FunctionsRelayError(FunctionsError):
    """Base exception for relay errors."""

    def __init__(self, message: str, code: int | None = None) -> None:
        super().__init__(
            message,
            "FunctionsRelayError",
            400 if code is None else code,
        )


def _error_message_from(response: Response) -> str | None:
    """Best-effort extraction of an error message from an edge function response.

    An edge function may reply with a plain-text or empty body, so a failed JSON
    decode must not mask the underlying HTTP error.
    """
    try:
        body = response.json()
    except ValueError:
        return response.text or None
    if isinstance(body, dict):
        return body.get("error")
    return response.text or None
