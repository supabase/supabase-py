from httpx import Response
from pydantic import BaseModel, TypeAdapter, ValidationError
from pydantic.dataclasses import dataclass


class StorageException(Exception):
    """Error raised when an operation on the storage API fails."""


class VectorBucketException(StorageException):
    def __init__(self, msg: str) -> None:
        self.msg = msg


class VectorBucketErrorMessage(BaseModel):
    statusCode: str | int
    error: str
    message: str
    code: str | None = None


@dataclass
class StorageApiError(StorageException):
    message: str
    code: str
    status: int | str


StorageApiErrorParser = TypeAdapter(StorageApiError)


def parse_api_error(response: Response) -> StorageApiError:
    try:
        return StorageApiErrorParser.validate_json(response.content)
    except ValidationError:
        message = f"Unable to parse error message: {response.text}"
        return StorageApiError(message=message, code="InternalError", status=400)
