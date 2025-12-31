from __future__ import annotations

from typing import TypedDict


class FunctionsApiErrorDict(TypedDict):
    """Typed dictionary representing a Functions API error."""
    name: str
    message: str
    status: int


class FunctionsError(Exception):
    """Base exception class for Supabase Functions errors."""
    def __init__(self, message: str, name: str, status: int) -> None:
        """
        Initialize a functionserror.
        args:
             message (str):HUman-readable error message.
             name (str): Error type name.
             status (init): HTTP status code.
        """
        super().__init__(message)
        self.message = message
        self.name = name
        self.status = status

    def to_dict(self) -> FunctionsApiErrorDict:
        """
        Convert the error into a dictionary representation.

        Returns:
            FunctionsApiErrorDict: Dictionary containing error details.
        """
        return {
            "name": self.name,
            "message": self.message,
            "status": self.status,
        }


class FunctionsHttpError(FunctionsError):
     """Error raised for HTTP-related Functions failures."""

     def __init__(self, message: str, code: int | None = None) -> None:
         """
        Initialize a FunctionsHttpError.

        Args:
            message (str): Error message.
            code (int | None): Optional HTTP status code.
        """
         super().__init__(
            message,
            "FunctionsHttpError",
            400 if code is None else code,
        )


class FunctionsRelayError(FunctionsError):
     """Error raised for relay-related Functions failures."""

     def __init__(self, message: str, code: int | None = None) -> None:
         """
        Initialize a FunctionsRelayError.

        Args:
            message (str): Error message.
            code (int | None): Optional HTTP status code.
        """
         super().__init__(
            message,
            "FunctionsRelayError",
            400 if code is None else code,
        )
