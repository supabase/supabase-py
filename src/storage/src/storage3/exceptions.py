from typing import TypeVar

from pydantic import BaseModel, TypeAdapter, ValidationError
from pydantic.dataclasses import dataclass
from supabase_utils.http.request import Response


class StorageException(Exception):
    """Error raised when an operation on the storage API fails."""


class VectorBucketException(StorageException):
    def __init__(self, msg: str) -> None:
        self.msg = msg


class StorageApiErrorMessage(BaseModel):
    """Wire format of a storage API error body."""

    statusCode: str | int
    error: str
    message: str
    code: str | None = None


# Kept as an alias: the vector endpoints return the same error body.
VectorBucketErrorMessage = StorageApiErrorMessage


@dataclass
class StorageApiError(StorageException):
    message: str
    code: str
    status: int | str

    def __repr__(self) -> str:
        return str(self)

    def __str__(self) -> str:
        return f"StorageApiError(message='{self.message}', code={self.code}, status='{self.status}')"


StorageApiErrorParser = TypeAdapter(StorageApiErrorMessage)


def parse_api_error(response: Response) -> StorageApiError:
    try:
        parsed = StorageApiErrorParser.validate_json(response.content)
    except ValidationError:
        body = response.content.decode("utf-8", errors="replace")
        return StorageApiError(
            message=f"Unable to parse error message: {body}",
            code="InternalError",
            status=response.status,
        )
    return StorageApiError(
        message=parsed.message,
        code=parsed.code or parsed.error,
        status=parsed.statusCode,
    )


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
