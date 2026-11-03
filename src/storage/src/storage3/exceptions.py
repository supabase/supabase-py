from typing import TypedDict

from httpx import Response
from pydantic import BaseModel, ValidationError

from .utils import StorageException


class VectorBucketException(Exception):
    def __init__(self, msg: str) -> None:
        self.msg = msg


class VectorBucketErrorMessage(BaseModel):
    statusCode: str | int
    error: str
    message: str
    code: str | None = None


class _AnalyticsBucketErrorDetail(BaseModel):
    message: str
    type: str


class _AnalyticsBucketErrorMessage(BaseModel):
    error: _AnalyticsBucketErrorDetail


class StorageApiErrorDict(TypedDict):
    name: str
    message: str
    code: str
    status: int | str


class StorageApiError(StorageException):
    """Error raised when an operation on the storage API fails."""

    def __init__(self, message: str, code: str, status: int | str) -> None:
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


def _parse_storage_api_error(response: Response) -> StorageApiError:
    try:
        error = VectorBucketErrorMessage.model_validate_json(response.content)
        return StorageApiError(
            message=error.message,
            code=error.code or "400",
            status=error.statusCode,
        )
    except ValidationError:
        pass
    try:
        analytics_error = _AnalyticsBucketErrorMessage.model_validate_json(
            response.content
        )
        return StorageApiError(
            message=analytics_error.error.message,
            code=analytics_error.error.type,
            status=response.status_code,
        )
    except ValidationError:
        pass
    return StorageApiError(
        message=f"The request failed, but could not parse error message response:'{response.text}'",
        code="LibraryError",
        status=response.status_code,
    )
