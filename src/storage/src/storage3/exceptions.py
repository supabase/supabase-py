from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, TypeAdapter, ValidationError
from supabase_utils.errors import SupabaseError
from supabase_utils.http.errors import SupabaseAPIError

if TYPE_CHECKING:
    from supabase_utils.http.request import Response


class StorageException(SupabaseError):
    """Raised when a storage operation fails.

    A plain `StorageException` is a failure the client raised on its own. A
    failure the storage service reported is a `StorageApiError`.
    """


class VectorBucketException(StorageException):
    """Raised when a vector bucket operation is given invalid input."""


class StorageApiErrorMessage(BaseModel):
    """Wire format of a storage API error body."""

    statusCode: str | int
    error: str
    message: str
    code: str | None = None


# Kept as an alias: the vector endpoints return the same error body.
VectorBucketErrorMessage = StorageApiErrorMessage


class StorageApiError(StorageException, SupabaseAPIError):
    """Raised when the storage service answered a request with an error.
    `code` is the error code of the service, such as `NoSuchKey`."""

    def __init__(
        self,
        message: str,
        *,
        status_code: int,
        code: str,
        response: Response | None = None,
    ) -> None:
        super().__init__(message, status_code=status_code, code=code, response=response)


StorageApiErrorParser = TypeAdapter(StorageApiErrorMessage)


def parse_api_error(response: Response) -> StorageApiError:
    try:
        parsed = StorageApiErrorParser.validate_json(response.content)
    except ValidationError:
        body = response.content.decode("utf-8", errors="replace")
        message = f"Unable to parse error message: {body}"
        return StorageApiError(
            message,
            status_code=response.status,
            code="InternalError",
            response=response,
        )
    return StorageApiError(
        parsed.message,
        status_code=response.status,
        code=parsed.code or parsed.error,
        response=response,
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
