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


class StorageDownloadTooLargeError(StorageException):
    """Raised when a download is read into memory and its body is larger than
    the `max_bytes` the caller allowed."""

    def __init__(self, max_bytes: int) -> None:
        super().__init__(f"The download is larger than {max_bytes} bytes")
        self.max_bytes = max_bytes
        """The cap the body exceeded."""


class StorageRangeIgnoredError(StorageException):
    """Raised when `download` asked for a byte range and the server answered
    with the whole object instead, as a cache that ignores the `Range` header
    does. Use `download_stream` to accept the whole object in that case."""

    def __init__(self, byte_range: str, status: int) -> None:
        super().__init__(
            f"The server answered the request for {byte_range} with HTTP {status}"
            " and the whole object instead of HTTP 206 and the range"
        )
        self.byte_range = byte_range
        """The `Range` header that was sent, such as `bytes=0-99`."""
        self.status = status
        """The HTTP status the server answered with."""


class ResumableUploadPausedError(StorageException):
    """Raised by `run` of a resumable upload that `pause` stopped before it
    completed. Call `run` again to continue it."""


class ResumableUploadCancelledError(StorageException):
    """Raised by `run` of a resumable upload that `cancel` stopped. The upload
    cannot continue."""


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


class _AnalyticsApiErrorDetail(BaseModel):
    message: str
    type: str | None = None


class _AnalyticsApiErrorMessage(BaseModel):
    """Wire format of an analytics bucket error body."""

    error: _AnalyticsApiErrorDetail


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


StorageApiErrorParser = TypeAdapter[StorageApiErrorMessage | _AnalyticsApiErrorMessage](
    StorageApiErrorMessage | _AnalyticsApiErrorMessage
)


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
    match parsed:
        case StorageApiErrorMessage():
            message, code = parsed.message, parsed.code or parsed.error
        case _AnalyticsApiErrorMessage():
            message = parsed.error.message
            code = parsed.error.type or "InternalError"
    return StorageApiError(
        message,
        status_code=response.status,
        code=code,
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
