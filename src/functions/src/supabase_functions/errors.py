from __future__ import annotations

from typing import TypedDict

from pydantic import ValidationError
from supabase_utils.http.request import Response
from supabase_utils.types import JSONParser


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


def on_error_response(response: Response) -> FunctionsHttpError | FunctionsRelayError:
    if _is_relay_error(response):
        return FunctionsRelayError(
            response.content.decode("utf-8", errors="replace"), code=response.status
        )
    return FunctionsHttpError(
        _error_message_from(response)
        or "An error occurred while requesting your edge function at "
        f"{str(response.request.url)!r}.",
        response.status,
    )


class FunctionsRelayError(FunctionsError):
    """Base exception for relay errors."""

    def __init__(self, message: str, code: int | None = None) -> None:
        super().__init__(
            message,
            "FunctionsRelayError",
            400 if code is None else code,
        )
