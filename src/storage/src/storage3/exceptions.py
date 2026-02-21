from typing import Optional, TypedDict, Union

from pydantic import BaseModel

from .utils import StorageException


class VectorBucketException(Exception):
    def __init__(self, msg: str) -> None:
        self.msg = msg


class VectorBucketErrorMessage(BaseModel):
    statusCode: Union[str, int]
    error: str
    message: str
    code: Optional[str] = None


class StorageApiErrorDict(TypedDict):
    name: str
    message: str
    code: str
    status: Union[int, str]


class StorageApiError(StorageException):
    """Error raised when an operation on the storage API fails."""

    def __init__(self, message: str, code: str, status: Union[int, str]) -> None:
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
