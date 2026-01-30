from typing import Optional, Union

from httpx import Response
from pydantic import BaseModel, ValidationError


class VectorBucketException(Exception):
    def __init__(self, msg: str) -> None:
        self.msg = msg


class VectorBucketErrorMessage(BaseModel):
    statusCode: Union[str, int]
    error: str
    message: str
    code: Optional[str] = None


class StorageException(Exception):
    """Error raised when an operation on the storage API fails."""


class StorageApiError(StorageException, BaseModel):
    message: str
    code: str
    status: Union[int, str]


def parse_api_error(response: Response) -> StorageApiError:
    try:
        return StorageApiError.model_validate_json(response.content)
    except ValidationError:
        message = f"Unable to parse error message: {response.text}"
        return StorageApiError(message=message, code="InternalError", status=400)
