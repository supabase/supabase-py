from __future__ import annotations

from typing import TypedDict

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


def on_error_response(response: Response) -> FunctionsHttpError | FunctionsRelayError:
    is_relay_error = response.headers.get("x-relay-header")
    if is_relay_error == "true":
        return FunctionsRelayError(
            response.text, "FunctionsRelayError", response.status_code
        )
    return FunctionsHttpError(response.text, response.status_code)


class FunctionsRelayError(FunctionsError):
    """Base exception for relay errors."""

    pass
