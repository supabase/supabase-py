from dataclasses import dataclass
from typing import (
    Any,
    Awaitable,
    Callable,
    Generator,
    Generic,
    Optional,
    Protocol,
    TypeAlias,
    TypeVar,
    Union,
    overload,
)

from typing_extensions import Concatenate, ParamSpec
from yarl import URL

from .headers import Headers
from .request import Request, Response, ToRequest

T = TypeVar("T", covariant=True)

Success = TypeVar("Success", covariant=True)


HttpMethod: TypeAlias = Generator[ToRequest, Response, Success]


@dataclass
class LoopReturnValue(Generic[Success]):
    iterable: HttpMethod[Success]

    def __iter__(self) -> HttpMethod[Success]:
        self.return_value: Success = yield from self.iterable
        return self.return_value


class HttpSession(Protocol):
    def send(self, request: Request) -> Response: ...


class AsyncHttpSession(Protocol):
    def send(self, request: Request) -> Awaitable[Response]: ...


class SyncHttpIO:
    def __init__(self, session: HttpSession) -> None:
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
                    http_request.finalize(base_url, default_headers)
                )
                http_request = iterator.send(response)
        except StopIteration:
            return return_value_iterator.return_value


class AsyncHttpIO:
    def __init__(self, session: AsyncHttpSession) -> None:
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
                    http_request.finalize(base_url, default_headers)
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
