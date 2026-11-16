import math
import os
from collections.abc import AsyncIterator, Iterator
from dataclasses import dataclass, field
from io import BytesIO
from typing import (
    Protocol,
    override,
)

from pydantic import BaseModel
from yarl import URL

from ..types import JSON, JSONParser
from ..types import HTTPRequestMethod as HTTPRequestMethod
from .body import FileContent, RequestContent
from .headers import Headers
from .query import URLQuery
from .retry import RetryPolicy


def validate_request_timeout(timeout: float | None) -> None:
    if timeout is not None and not (math.isfinite(timeout) and timeout > 0):
        raise ValueError(
            f"Request timeout must be a positive number of seconds, not {timeout!r}"
        )


@dataclass
class Request:
    url: URL
    method: HTTPRequestMethod
    headers: Headers
    content: RequestContent | None
    delay: float | None
    timeout: float | None = None
    retry: RetryPolicy | bool | None = None

    def __post_init__(self) -> None:
        validate_request_timeout(self.timeout)


@dataclass
class Response:
    headers: Headers
    content: bytes
    status: int
    request: Request

    @property
    def is_success(self) -> bool:
        return 200 <= self.status < 300

    @property
    def is_error(self) -> bool:
        return 400 <= self.status <= 599


@dataclass
class StreamedResponse:
    """A response whose body is read as it arrives. `body` can be read once,
    and raises a `SupabaseTransportError` when the transfer fails."""

    headers: Headers
    status: int
    request: Request
    body: Iterator[bytes]

    @property
    def is_success(self) -> bool:
        return 200 <= self.status < 300

    def read(self) -> Response:
        """Reads the rest of the body into a `Response`."""
        return Response(
            headers=self.headers,
            content=b"".join(self.body),
            status=self.status,
            request=self.request,
        )


@dataclass
class AsyncStreamedResponse:
    """A response whose body is read as it arrives. `body` can be read once,
    and raises a `SupabaseTransportError` when the transfer fails."""

    headers: Headers
    status: int
    request: Request
    body: AsyncIterator[bytes]

    @property
    def is_success(self) -> bool:
        return 200 <= self.status < 300

    async def read(self) -> Response:
        """Reads the rest of the body into a `Response`."""
        return Response(
            headers=self.headers,
            content=b"".join([chunk async for chunk in self.body]),
            status=self.status,
            request=self.request,
        )


class ToRequest(Protocol):
    def finalize(self, base_url: URL, default_headers: Headers) -> Request: ...


@dataclass(frozen=True)
class EmptyRequest:
    path: list[str]
    method: HTTPRequestMethod
    delay: float | None = field(default=None, kw_only=True)
    timeout: float | None = field(default=None, kw_only=True)
    retry: RetryPolicy | bool | None = field(default=None, kw_only=True)
    """Whether the executor retries the request when it fails in a way its
    `RetryPolicy` retries. None leaves it to the method of the request, True
    retries it whatever its method, False never retries it, and a
    `RetryPolicy` retries it with that policy whatever its method."""
    headers: Headers = field(default_factory=Headers.empty, kw_only=True)
    query: URLQuery = field(default_factory=URLQuery.empty, kw_only=True)

    def __post_init__(self) -> None:
        validate_request_timeout(self.timeout)

    def finalize(self, base_url: URL, default_headers: Headers) -> Request:
        return Request(
            method=self.method,
            url=base_url.joinpath(*self.path).with_query(self.query.as_query()),
            headers=default_headers.update(self.headers),
            content=None,
            delay=self.delay,
            timeout=self.timeout,
            retry=self.retry,
        )

    def _headers_with_content_type(
        self, default_headers: Headers, content_type: str
    ) -> Headers:
        headers = default_headers.update(self.headers)
        if "content-type" in self.headers:
            return headers
        return headers.override("Content-Type", content_type)


@dataclass(frozen=True)
class BytesRequest(EmptyRequest):
    """A request that sends `body` as it is. An iterable body is streamed,
    and a `FileContent` whose length is known is sent with a
    `Content-Length`."""

    body: RequestContent

    @override
    def finalize(self, base_url: URL, default_headers: Headers) -> Request:
        headers = self._headers_with_content_type(
            default_headers, "application/octet-stream"
        )
        if isinstance(self.body, FileContent) and "content-length" not in headers:
            length = self.body.length
            if length is not None:
                headers = headers.override("Content-Length", str(length))
        return Request(
            method=self.method,
            url=base_url.joinpath(*self.path).with_query(self.query.as_query()),
            headers=headers,
            content=self.body,
            delay=self.delay,
            timeout=self.timeout,
            retry=self.retry,
        )


@dataclass(frozen=True)
class JSONRequest(EmptyRequest):
    body: JSON | BaseModel
    exclude_none: bool = True

    @override
    def finalize(self, base_url: URL, default_headers: Headers) -> Request:
        headers = self._headers_with_content_type(default_headers, "application/json")
        if isinstance(self.body, BaseModel):
            content = self.body.__pydantic_serializer__.to_json(
                self.body, exclude_none=self.exclude_none
            )
        else:
            content = JSONParser.dump_json(self.body)
        return Request(
            method=self.method,
            url=base_url.joinpath(*self.path).with_query(self.query.as_query()),
            headers=headers,
            content=content,
            delay=self.delay,
            timeout=self.timeout,
            retry=self.retry,
        )


@dataclass(frozen=True)
class TextRequest(EmptyRequest):
    text: str

    @override
    def finalize(self, base_url: URL, default_headers: Headers) -> Request:
        headers = self._headers_with_content_type(
            default_headers, "text/plain; charset=utf-8"
        )
        return Request(
            method=self.method,
            url=base_url.joinpath(*self.path).with_query(self.query.as_query()),
            headers=headers,
            content=self.text.encode("utf-8"),
            delay=self.delay,
            timeout=self.timeout,
            retry=self.retry,
        )


@dataclass
class FileField:
    name: str
    data: bytes
    filename: str
    content_type: str
    headers: dict[str, str] = field(default_factory=dict)
    content_disposition: str | None = None
    content_location: str | None = None

    def render_headers(self) -> bytes:
        """
        Renders the headers for this request field.
        """
        lines = []
        lines.append(f"Content-Type: {self.content_type}")
        content_disposition = self.content_disposition or "form-data"
        lines.append(
            f'Content-Disposition: {content_disposition}; name="{self.name}"; filename="{self.filename}"'
        )
        if self.content_location:
            lines.append(f"Content-Location: {self.content_location}")
        for header_name, header_value in self.headers.items():
            if header_value:
                lines.append(f"{header_name}: {header_value}")
        lines.append("\r\n")
        return "\r\n".join(lines).encode("utf-8")


@dataclass
class DataField:
    name: str
    data: bytes
    headers: dict[str, str] = field(default_factory=dict)
    content_disposition: str | None = None

    def render_headers(self) -> bytes:
        """
        Renders the headers for this request field.
        """
        lines = []
        content_disposition = self.content_disposition or "form-data"
        lines.append(f'Content-Disposition: {content_disposition}; name="{self.name}"')
        for header_name, header_value in self.headers.items():
            if header_value:
                lines.append(f"{header_name}: {header_value}")
        lines.append("\r\n")
        return "\r\n".join(lines).encode("utf-8")


class PartField(Protocol):
    data: bytes

    def render_headers(self) -> bytes: ...


def encode_multipart_formdata(fields: list[PartField]) -> tuple[bytes, str]:
    body = BytesIO()
    boundary = os.urandom(16).hex()
    bin_boundary = boundary.encode("ascii")
    for form_field in fields:
        body.write(b"--%s\r\n" % (bin_boundary))
        body.write(form_field.render_headers())
        body.write(form_field.data)
        body.write(b"\r\n")
    body.write(b"--%s--\r\n" % (bin_boundary))
    content_type = f"multipart/form-data; boundary={boundary}"
    return body.getvalue(), content_type


@dataclass(frozen=True)
class MultipartFormDataRequest(EmptyRequest):
    fields: list[PartField]

    @override
    def finalize(self, base_url: URL, default_headers: Headers) -> Request:
        content, content_type = encode_multipart_formdata(fields=self.fields)
        headers = default_headers.update(self.headers).override(
            "Content-Type", content_type
        )
        return Request(
            method=self.method,
            url=base_url.joinpath(*self.path).with_query(self.query.as_query()),
            headers=headers,
            content=content,
            delay=self.delay,
            timeout=self.timeout,
            retry=self.retry,
        )
