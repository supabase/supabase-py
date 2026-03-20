from dataclasses import dataclass, field
from typing import (
    IO,
    Any,
    Awaitable,
    Callable,
    Dict,
    Generator,
    Generic,
    List,
    Literal,
    Mapping,
    Optional,
    Protocol,
    Tuple,
    TypeAlias,
    TypeVar,
    Union,
    overload,
)

from httpx import (
    AsyncClient,
    Client,
    Headers,
    QueryParams,
    Response,
)
from httpx import (
    Request as HttpxRequest,
)
from pydantic import BaseModel
from typing_extensions import Concatenate, ParamSpec
from yarl import URL

from .types import JSON, JSONParser

HTTPRequestMethod = Literal["GET", "POST", "PATCH", "PUT", "DELETE", "HEAD"]


@dataclass
class EmptyRequest:
    path: List[str]
    method: HTTPRequestMethod
    headers: Headers = field(default_factory=Headers, kw_only=True)
    query_params: QueryParams = field(default_factory=QueryParams, kw_only=True)

    def to_request(self, base_url: URL, default_headers: Headers) -> HttpxRequest:
        headers = Headers(default_headers)
        headers.update(self.headers)
        return HttpxRequest(
            method=self.method,
            url=str(base_url.joinpath(*self.path)),
            headers=headers,
            params=self.query_params,
        )


@dataclass
class BytesRequest(EmptyRequest):
    body: bytes

    def to_request(self, base_url: URL, default_headers: Headers) -> HttpxRequest:
        headers = Headers(default_headers)
        headers.update(self.headers)
        headers["Content-Type"] = "application/octet-stream"
        return HttpxRequest(
            method=self.method,
            url=str(base_url.joinpath(*self.path)),
            headers=headers,
            params=self.query_params,
            content=self.body,
        )


@dataclass
class JSONRequest(EmptyRequest):
    body: Union[JSON, BaseModel]
    exclude_none: bool = True

    def to_request(self, base_url: URL, default_headers: Headers) -> HttpxRequest:
        headers = Headers(default_headers)
        headers.update(self.headers)
        headers["Content-Type"] = "application/json"
        if isinstance(self.body, BaseModel):
            content = self.body.__pydantic_serializer__.to_json(
                self.body, exclude_none=self.exclude_none
            )
        else:
            content = JSONParser.dump_json(self.body)
        return HttpxRequest(
            method=self.method,
            url=str(base_url.joinpath(*self.path)),
            headers=headers,
            params=self.query_params,
            content=content,
        )


@dataclass
class TextRequest(EmptyRequest):
    text: str

    def to_request(self, base_url: URL, default_headers: Headers) -> HttpxRequest:
        headers = Headers(default_headers)
        headers.update(self.headers)
        headers["Content-Type"] = "text/plain; charset=utf-8"
        return HttpxRequest(
            method=self.method,
            url=str(base_url.joinpath(*self.path)),
            headers=headers,
            params=self.query_params,
            content=self.text.encode("utf-8"),
        )


@dataclass
class MultipartFormDataRequest(EmptyRequest):
    files: Mapping[str, Tuple[str, Union[IO[bytes], bytes], str]]
    data: Dict[str, str]

    def to_request(self, base_url: URL, default_headers: Headers) -> HttpxRequest:
        headers = Headers(default_headers)
        headers.update(self.headers)
        return HttpxRequest(
            method=self.method,
            url=str(base_url.joinpath(*self.path)),
            headers=headers,
            params=self.query_params,
            files=self.files,
            data=self.data,
        )


T = TypeVar("T", covariant=True)

Success = TypeVar("Success", covariant=True)


class ToHttpxRequest(Protocol):
    def to_request(self, base_url: URL, default_headers: Headers) -> HttpxRequest: ...


HttpMethod: TypeAlias = Generator[ToHttpxRequest, Response, Success]


@dataclass
class LoopReturnValue(Generic[Success]):
    iterable: HttpMethod[Success]

    def __iter__(self) -> HttpMethod[Success]:
        self.return_value: Success = yield from self.iterable
        return self.return_value


class SyncHttpIO:
    def __init__(self, session: Client) -> None:
        self.session = session

    def communicate(
        self,
        base_url: URL,
        default_headers: Headers,
        http_iterator: HttpMethod[Success],
    ) -> Success:
        return_value_iterator = LoopReturnValue(http_iterator)
        iterator = iter(return_value_iterator)
        try:
            http_request = next(iterator)
            while True:
                response = self.session.send(
                    http_request.to_request(base_url, default_headers)
                )
                http_request = iterator.send(response)
        except StopIteration:
            return return_value_iterator.return_value


class AsyncHttpIO:
    def __init__(self, session: AsyncClient) -> None:
        self.session = session

    async def communicate(
        self,
        base_url: URL,
        default_headers: Headers,
        http_iterator: HttpMethod[Success],
    ) -> Success:
        return_value_iterator = LoopReturnValue(http_iterator)
        iterator = iter(return_value_iterator)
        try:
            http_request = next(iterator)
            while True:
                response = await self.session.send(
                    http_request.to_request(base_url, default_headers)
                )
                http_request = iterator.send(response)
        except StopIteration:
            return return_value_iterator.return_value


Params = ParamSpec("Params")
HttpIO = TypeVar("HttpIO", SyncHttpIO, AsyncHttpIO)


class HasExecutor(Protocol[HttpIO]):
    executor: HttpIO
    base_url: URL
    default_headers: Headers


@dataclass
class handle_http_io(Generic[Params, Success]):
    method: Callable[Concatenate[Any, Params], HttpMethod[Success]]

    @overload
    def __get__(
        self, obj: HasExecutor[SyncHttpIO], objtype: Optional[type] = None
    ) -> Callable[Params, Success]: ...

    @overload
    def __get__(
        self, obj: HasExecutor[AsyncHttpIO], objtype: Optional[type] = None
    ) -> Callable[Params, Awaitable[Success]]: ...

    def __get__(
        self, obj: HasExecutor[HttpIO], objtype: Optional[type] = None
    ) -> Callable[Params, Union[Success, Awaitable[Success]]]:
        def bound_method(
            *args: Params.args, **kwargs: Params.kwargs
        ) -> Union[Success, Awaitable[Success]]:
            iterator = self.method(obj, *args, **kwargs)
            return obj.executor.communicate(obj.base_url, obj.default_headers, iterator)

        return bound_method
