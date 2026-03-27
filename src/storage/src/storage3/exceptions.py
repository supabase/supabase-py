from typing import TypeVar

from pydantic import BaseModel, TypeAdapter, ValidationError
from pydantic.dataclasses import dataclass
from supabase_utils.http.request import Response


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

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return f"StorageApiError(message='{self.message}', code={self.code}, status='{self.status}')"


StorageApiErrorParser = TypeAdapter(StorageApiError)


def parse_api_error(response: Response) -> StorageApiError:
    try:
        return StorageApiErrorParser.validate_json(response.content)
    except ValidationError:
        message = f"Unable to parse error message: {response.content.decode('utf-8')}"
        return StorageApiError(message=message, code="InternalError", status=400)


Inner = TypeVar("Inner")


def validate_adapter(response: Response, type_adapter: TypeAdapter[Inner]) -> Inner:
    if response.is_success:
        return type_adapter.validate_json(response.content)
    raise parse_api_error(response)


Model = TypeVar("Model", bound=BaseModel)


def validate_model(response: Response, model: type[Model]) -> Model:
    if response.is_success:
        return model.model_validate_json(response.content)
    raise parse_api_error(response)
