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
class Response:
    headers: Headers
    content: bytes
    status: int

    def is_success(self) -> bool:
        return 200 <= self.status <= 300


@dataclass
class Request:
    url: URL
    method: HTTPRequestMethod
    headers: Headers
    content: bytes | None


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

    def to_request(self, base_url: URL, default_headers: Headers) -> Request:
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
class FormField:
    name: str
    data: bytes
    filename: str
    headers: Headers

    def render_headers(self) -> bytes:
        """
        Renders the headers for this request field.
        """
        lines = []
        sort_keys = ["Content-Disposition", "Content-Type", "Content-Location"]
        for sort_key in sort_keys:
            if val := self.headers.get(sort_key):
                lines.append(f"{sort_key}: {val}")
        for header_name, header_value in self.headers.items():
            if header_name not in sort_keys:
                if header_value:
                    lines.append(f"{header_name}: {header_value}")
        lines.append("\r\n")
        return "\r\n".join(lines).encode("utf-8")


def encode_multipart_formdata(fields: list[FormField]) -> tuple[bytes, str]:
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
    files: list[FormField]

    def to_request(self, base_url: URL, default_headers: Headers) -> Request:
        content, content_type = encode_multipart_formdata(fields=self.files)
        headers = default_headers.update(self.headers).set("Content-Type", content_type)
        return Request(
            method=self.method,
            url=base_url.joinpath(*self.path).with_query(self.query.as_query()),
            headers=headers,
            content=content,
        )
