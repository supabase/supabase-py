import asyncio
import inspect
import time
from collections.abc import Awaitable, Callable, Generator
from dataclasses import dataclass, field
from functools import cached_property, update_wrapper
from types import TracebackType
from typing import (
    Any,
    Concatenate,
    Protocol,
    Self,
    overload,
)

from yarl import URL

from .headers import Headers
from .request import Request, Response, ToRequest, validate_request_timeout

type HttpMethod[Success] = Generator[ToRequest, Response, Success]


@dataclass
class LoopReturnValue[Success]:
    iterable: HttpMethod[Success]
    return_value: Success = field(init=False)

    def __iter__(self) -> HttpMethod[Success]:
        self.return_value = yield from self.iterable
        return self.return_value


class HttpSession(Protocol):
    def send(self, request: Request) -> Response: ...
    def __enter__(self) -> Self: ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...


class AsyncHttpSession(Protocol):
    async def send(self, request: Request) -> Response: ...
    async def __aenter__(self) -> Self: ...
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...


class SyncHttpIO:
    def __init__(
        self, session: HttpSession, request_timeout: float | None = None
    ) -> None:
        validate_request_timeout(request_timeout)
        self.session = session
        self.request_timeout = request_timeout

    def communicate[Success](
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
                request = http_request.finalize(base_url, default_headers)
                if request.timeout is None:
                    request.timeout = self.request_timeout
                if request.delay:
                    time.sleep(request.delay)
                response = self.session.send(request)
                http_request = iterator.send(response)
        except StopIteration:
            return return_value_iterator.return_value


class AsyncHttpIO:
    def __init__(
        self, session: AsyncHttpSession, request_timeout: float | None = None
    ) -> None:
        validate_request_timeout(request_timeout)
        self.session = session
        self.request_timeout = request_timeout

    async def communicate[Success](
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
                request = http_request.finalize(base_url, default_headers)
                if request.timeout is None:
                    request.timeout = self.request_timeout
                if request.delay:
                    await asyncio.sleep(request.delay)
                response = await self.session.send(request)
                http_request = iterator.send(response)
        except StopIteration:
            return return_value_iterator.return_value


class HasExecutor[HttpIO: (SyncHttpIO, AsyncHttpIO)](Protocol):
    executor: HttpIO
    base_url: URL
    default_headers: Headers


@dataclass
class handle_http_io[**Params, Success]:
    method: Callable[Concatenate[Any, Params], HttpMethod[Success]]

    @overload
    def __get__(
        self, obj: HasExecutor[SyncHttpIO], objtype: type | None = None
    ) -> Callable[Params, Success]: ...

    @overload
    def __get__(
        self, obj: HasExecutor[AsyncHttpIO], objtype: type | None = None
    ) -> Callable[Params, Awaitable[Success]]: ...

    def __get__(
        self,
        obj: HasExecutor[SyncHttpIO] | HasExecutor[AsyncHttpIO],
        objtype: type | None = None,
    ) -> Callable[Params, Success | Awaitable[Success]]:
        def bound_method(
            *args: Params.args, **kwargs: Params.kwargs
        ) -> Success | Awaitable[Success]:
            iterator = self.method(obj, *args, **kwargs)
            return obj.executor.communicate(obj.base_url, obj.default_headers, iterator)

        update_wrapper(bound_method, self.method)
        # pyrefly: ignore[missing-attribute]
        bound_method.__signature__ = self.bound_signature
        return bound_method

    @cached_property
    def bound_signature(self) -> inspect.Signature:
        signature = inspect.signature(self.method)
        parameters = list(signature.parameters.values())[1:]
        return signature.replace(
            parameters=parameters, return_annotation=inspect.Signature.empty
        )
