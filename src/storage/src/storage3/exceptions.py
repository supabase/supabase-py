from typing import override

from pydantic import BaseModel, TypeAdapter, ValidationError
from pydantic.dataclasses import dataclass
from supabase_utils.http.request import Response


class StorageException(Exception):
    """Error raised when an operation on the storage API fails."""


class VectorBucketException(StorageException):
    def __init__(self, message: str) -> None:
        super().__init__(message)
        self.message = message


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

    @override
    def __repr__(self) -> str:
        return str(self)

    @override
    def __str__(self) -> str:
        return f"StorageApiError(message='{self.message}', code={self.code}, status='{self.status}')"


StorageApiErrorParser = TypeAdapter(StorageApiErrorMessage)


def parse_api_error(response: Response) -> StorageApiError:
    try:
        parsed = StorageApiErrorParser.validate_json(response.content)
    except ValidationError:
        body = response.content.decode("utf-8", errors="replace")
        message = f"Unable to parse error message: {body}"
        return StorageApiError(
            message=message, code="InternalError", status=response.status
        )
    return StorageApiError(
        message=parsed.message,
        code=parsed.code or parsed.error,
        status=response.status,
    )


def _validate_adapter[Inner](
    response: Response, type_adapter: TypeAdapter[Inner]
) -> Inner:
    if response.is_success:
        return type_adapter.validate_json(response.content)
    raise parse_api_error(response)


def _validate_model[Model: BaseModel](response: Response, model: type[Model]) -> Model:
    if response.is_success:
        return model.model_validate_json(response.content)
    raise parse_api_error(response)
