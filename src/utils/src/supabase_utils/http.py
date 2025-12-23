from dataclasses import dataclass
from typing import (
    Any,
    Awaitable,
    Callable,
    Generic,
    List,
    Literal,
    Optional,
    Protocol,
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
    Request,
    Response,
)
from pydantic import BaseModel, TypeAdapter
from typing_extensions import Concatenate, ParamSpec
from yarl import URL

from .types import JSON

HTTPRequestMethod = Literal["GET", "POST", "PATCH", "PUT", "DELETE", "HEAD"]


@dataclass
class EndpointRequest:
    method: HTTPRequestMethod
    headers: Headers
    query_params: QueryParams
    path: List[str]
    body: JSON

    def to_request(self, base_url: URL) -> Request:
        return Request(
            method=self.method,
            url=str(base_url.joinpath(*self.path)),
            headers=self.headers,
            params=self.query_params,
            json=self.body,
        )


T = TypeVar("T", covariant=True)


class FromHTTPResponse(Protocol[T]):
    def __call__(self, response: Response) -> T: ...


Success = TypeVar("Success")
Failure = TypeVar("Failure", bound=Exception)

Model = TypeVar("Model", bound=BaseModel)


def validate_model(model: type[Model]) -> FromHTTPResponse[Model]:
    def from_response(response: Response) -> Model:
        return model.model_validate_json(response.content)

    return from_response


Inner = TypeVar("Inner")


def validate_adapter(adapter: TypeAdapter[Inner]) -> FromHTTPResponse[Inner]:
    def from_response(response: Response) -> Inner:
        return adapter.validate_json(response.content)

    return from_response


@dataclass
class ServerEndpoint(Generic[Success, Failure]):
    request: EndpointRequest
    on_success: FromHTTPResponse[Success]
    on_failure: FromHTTPResponse[Failure]


class SyncExecutor:
    def __init__(self, session: Client) -> None:
        self.session = session

    def communicate(
        self, base_url: URL, endpoint: ServerEndpoint[Success, Failure]
    ) -> Success:
        response = self.session.send(endpoint.request.to_request(base_url))
        try:
            response.raise_for_status()
            return endpoint.on_success(response)
        except HTTPStatusError:
            raise endpoint.on_failure(response) from None


class AsyncExecutor:
    def __init__(self, session: AsyncClient) -> None:
        self.session = session

    async def communicate(
        self, base_url: URL, endpoint: ServerEndpoint[Success, Failure]
    ) -> Success:
        request = endpoint.request.to_request(base_url)
        response = await self.session.send(request)
        try:
            response.raise_for_status()
            return endpoint.on_success(response)
        except HTTPStatusError:
            raise endpoint.on_failure(response) from None


Params = ParamSpec("Params")
Executor = TypeVar("Executor", SyncExecutor, AsyncExecutor)


class HasExecutor(Protocol[Executor]):
    executor: Executor
    base_url: URL


@dataclass
class http_endpoint(Generic[Params, Success, Failure]):
    method: Callable[Concatenate[Any, Params], ServerEndpoint[Success, Failure]]

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
            endpoint = self.method(obj, *args, **kwargs)
            return obj.executor.communicate(obj.base_url, endpoint)

        return bound_method
