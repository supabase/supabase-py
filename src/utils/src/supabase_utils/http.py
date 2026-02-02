from dataclasses import dataclass, field
from typing import (
    IO,
    Any,
    Awaitable,
    Callable,
    Dict,
    Generic,
    List,
    Literal,
    Mapping,
    Optional,
    Protocol,
    Tuple,
    TypeVar,
    Union,
    overload,
)

from httpx import (
    AsyncClient,
    Client,
    Headers,
    HTTPStatusError,
    QueryParams,
    Response,
)
from httpx import (
    Request as HttpxRequest,
)
from pydantic import BaseModel, TypeAdapter
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

    def to_request(self, base_url: URL) -> HttpxRequest:
        return HttpxRequest(
            method=self.method,
            url=str(base_url.joinpath(*self.path)),
            headers=self.headers,
            params=self.query_params,
        )


@dataclass
class BytesRequest(EmptyRequest):
    body: bytes

    def to_request(self, base_url: URL) -> HttpxRequest:
        headers = Headers(self.headers)
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

    def to_request(self, base_url: URL) -> HttpxRequest:
        headers = Headers(self.headers)
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

    def to_request(self, base_url: URL) -> HttpxRequest:
        headers = Headers(self.headers)
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

    def to_request(self, base_url: URL) -> HttpxRequest:
        return HttpxRequest(
            method=self.method,
            url=str(base_url.joinpath(*self.path)),
            headers=self.headers,
            params=self.query_params,
            files=self.files,
            data=self.data,
        )


T = TypeVar("T", covariant=True)


class FromHttpxResponse(Protocol[T]):
    def __call__(self, response: Response) -> T: ...


Success = TypeVar("Success", covariant=True)
Failure = TypeVar("Failure", covariant=True, bound=Exception)

Model = TypeVar("Model", bound=BaseModel)


def validate_model(model: type[Model]) -> FromHttpxResponse[Model]:
    def from_response(response: Response) -> Model:
        return model.model_validate_json(response.content)

    return from_response


Inner = TypeVar("Inner")


def validate_adapter(adapter: TypeAdapter[Inner]) -> FromHttpxResponse[Inner]:
    def from_response(response: Response) -> Inner:
        return adapter.validate_json(response.content)

    return from_response


class ToHttpxRequest(Protocol):
    def to_request(self, base_url: URL) -> HttpxRequest: ...


@dataclass
class ResponseHandler(Generic[Success]):
    request: ToHttpxRequest
    callback: FromHttpxResponse[Success]


def ResponseCases(
    request: ToHttpxRequest,
    on_success: FromHttpxResponse[Success],
    on_failure: FromHttpxResponse[Failure],
) -> ResponseHandler[Success]:
    def callback(response: Response) -> Success:
        try:
            response.raise_for_status()
            return on_success(response)
        except HTTPStatusError:
            raise on_failure(response) from None

    return ResponseHandler(
        request=request,
        callback=callback,
    )


class SyncExecutor:
    def __init__(self, session: Client) -> None:
        self.session = session

    def communicate(
        self, base_url: URL, resp_callback: ResponseHandler[Success]
    ) -> Success:
        response = self.session.send(resp_callback.request.to_request(base_url))
        return resp_callback.callback(response)


class AsyncExecutor:
    def __init__(self, session: AsyncClient) -> None:
        self.session = session

    async def communicate(
        self, base_url: URL, resp_callback: ResponseHandler[Success]
    ) -> Success:
        response = await self.session.send(resp_callback.request.to_request(base_url))
        return resp_callback.callback(response)


Params = ParamSpec("Params")
Executor = TypeVar("Executor", SyncExecutor, AsyncExecutor)


class HasExecutor(Protocol[Executor]):
    executor: Executor
    base_url: URL


@dataclass
class handle_http_response(Generic[Params, Success]):
    method: Callable[Concatenate[Any, Params], ResponseHandler[Success]]

    @overload
    def __get__(
        self, obj: HasExecutor[SyncExecutor], objtype: Optional[type] = None
    ) -> Callable[Params, Success]: ...

    @overload
    def __get__(
        self, obj: HasExecutor[AsyncExecutor], objtype: Optional[type] = None
    ) -> Callable[Params, Awaitable[Success]]: ...

    def __get__(
        self, obj: HasExecutor[Executor], objtype: Optional[type] = None
    ) -> Callable[Params, Union[Success, Awaitable[Success]]]:
        def bound_method(
            *args: Params.args, **kwargs: Params.kwargs
        ) -> Union[Success, Awaitable[Success]]:
            handler = self.method(obj, *args, **kwargs)
            return obj.executor.communicate(obj.base_url, handler)

        return bound_method
