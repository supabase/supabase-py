import os
from dataclasses import dataclass, field
from io import BytesIO
from typing import (
    List,
    Literal,
    Protocol,
    Union,
)

from pydantic import BaseModel
from yarl import URL

from ..types import JSON, JSONParser
from .headers import Headers
from .query import URLQuery

HTTPRequestMethod = Literal["GET", "POST", "PATCH", "PUT", "DELETE", "HEAD"]


@dataclass
class Request:
    url: URL
    method: HTTPRequestMethod
    headers: Headers
    content: bytes | None


@dataclass
class Response:
    headers: Headers
    content: bytes
    status: int
    request: Request

    @property
    def is_success(self) -> bool:
        return 200 <= self.status <= 300


class ToRequest(Protocol):
    def finalize(self, base_url: URL, default_headers: Headers) -> Request: ...


@dataclass
class EmptyRequest:
    path: List[str]
    method: HTTPRequestMethod
    headers: Headers = field(default_factory=Headers.empty, kw_only=True)
    query: URLQuery = field(default_factory=URLQuery.empty, kw_only=True)

    def finalize(self, base_url: URL, default_headers: Headers) -> Request:
        return Request(
            method=self.method,
            url=base_url.joinpath(*self.path).with_query(self.query.as_query()),
            headers=default_headers.update(self.headers),
            content=None,
        )


@dataclass
class BytesRequest(EmptyRequest):
    body: bytes

    def finalize(self, base_url: URL, default_headers: Headers) -> Request:
        headers = default_headers.update(self.headers).set(
            "Content-Type", "application/octet-stream"
        )
        return Request(
            method=self.method,
            url=base_url.joinpath(*self.path).with_query(self.query.as_query()),
            headers=headers,
            content=self.body,
        )


@dataclass
class JSONRequest(EmptyRequest):
    body: Union[JSON, BaseModel]
    exclude_none: bool = True

    def finalize(self, base_url: URL, default_headers: Headers) -> Request:
        headers = default_headers.update(self.headers).set(
            "Content-Type", "application/json"
        )
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
        )


@dataclass
class TextRequest(EmptyRequest):
    text: str

    def finalize(self, base_url: URL, default_headers: Headers) -> Request:
        headers = default_headers.update(self.headers).set(
            "Content-Type", "text/plain; charset=utf-8"
        )
        return Request(
            method=self.method,
            url=base_url.joinpath(*self.path).with_query(self.query.as_query()),
            headers=headers,
            content=self.text.encode("utf-8"),
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


@dataclass
class MultipartFormDataRequest(EmptyRequest):
    fields: list[PartField]

    def finalize(self, base_url: URL, default_headers: Headers) -> Request:
        content, content_type = encode_multipart_formdata(fields=self.fields)
        headers = default_headers.update(self.headers).set("Content-Type", content_type)
        print(content)
        return Request(
            method=self.method,
            url=base_url.joinpath(*self.path).with_query(self.query.as_query()),
            headers=headers,
            content=content,
        )
