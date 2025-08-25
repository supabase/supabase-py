from typing import TypedDict

from .utils import StorageException


class StorageApiErrorDict(TypedDict):
    name: str
    message: str
    status: int


class StorageApiError(StorageException):
    """Error raised when an operation on the storage API fails."""

    def __init__(self, message: str, code: str, status: int) -> None:
        error_message = (
            f"{{'statusCode': {status}, 'error': {code}, 'message': {message}}}"
        )
        super().__init__(error_message)
        self.name = "StorageApiError"
        self.message = message
        self.code = code
        self.status = status

    def to_dict(self) -> StorageApiErrorDict:
        return {
            "name": self.name,
            "code": self.code,
            "message": self.message,
            "status": self.status,
        }
