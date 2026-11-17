import asyncio
import inspect
import time
from collections.abc import (
    AsyncGenerator,
    AsyncIterable,
    Awaitable,
    Callable,
    Generator,
)
from contextlib import (
    AbstractAsyncContextManager,
    AbstractContextManager,
    asynccontextmanager,
    contextmanager,
)
from dataclasses import dataclass, field, replace
from functools import cached_property, update_wrapper
from time import perf_counter
from types import TracebackType
from typing import (
    Any,
    Concatenate,
    Protocol,
    Self,
    overload,
    override,
)

from yarl import URL

from .._logging import get_logger
from .errors import SupabaseTransportError
from .headers import Headers
from .request import (
    AsyncStreamedResponse,
    Request,
    Response,
    StreamedResponse,
    ToRequest,
    validate_request_timeout,
)
from .retry import RetryPolicy, _policy_for

type HttpMethod[Success] = Generator[ToRequest, Response, Success]

logger = get_logger("http")


def _log_response(request: Request, started: float, response: Response) -> None:
    duration = perf_counter() - started
    logger.debug(
        "%s %s %d in %.3f seconds",
        request.method,
        request.url.raw_path,
        response.status,
        duration,
        extra={
            "http_method": request.method,
            "http_path": request.url.raw_path,
            "http_status": response.status,
            "duration": duration,
        },
    )


def _log_transport_error(
    request: Request, started: float, error: SupabaseTransportError
) -> None:
    duration = perf_counter() - started
    error_type = type(error).__name__
    logger.debug(
        "%s %s failed in %.3f seconds with %s",
        request.method,
        request.url.raw_path,
        duration,
        error_type,
        extra={
            "http_method": request.method,
            "http_path": request.url.raw_path,
            "duration": duration,
            "error_type": error_type,
        },
    )


@dataclass
class LoopReturnValue[Success]:
    iterable: HttpMethod[Success]
    return_value: Success = field(init=False)

    def __iter__(self) -> HttpMethod[Success]:
        self.return_value = yield from self.iterable
        return self.return_value


class HttpSession(Protocol):
    def send(self, request: Request) -> Response: ...
    def stream(self, request: Request) -> AbstractContextManager[StreamedResponse]: ...
    def __enter__(self) -> Self: ...
    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...


class AsyncHttpSession(Protocol):
    async def send(self, request: Request) -> Response: ...
    def stream(
        self, request: Request
    ) -> AbstractAsyncContextManager[AsyncStreamedResponse]: ...
    async def __aenter__(self) -> Self: ...
    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None: ...


class _SharedHttpSession:
    """Sends the requests with a session that another client closes."""

    def __init__(self, session: HttpSession) -> None:
        self.session = session

    def send(self, request: Request) -> Response:
        return self.session.send(request)

    def stream(self, request: Request) -> AbstractContextManager[StreamedResponse]:
        return self.session.stream(request)

    def __enter__(self) -> Self:
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        pass


class _SharedAsyncHttpSession:
    """Sends the requests with a session that another client closes."""

    def __init__(self, session: AsyncHttpSession) -> None:
        self.session = session

    async def send(self, request: Request) -> Response:
        return await self.session.send(request)

    def stream(
        self, request: Request
    ) -> AbstractAsyncContextManager[AsyncStreamedResponse]:
        return self.session.stream(request)

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        pass


class _Retries:
    """The retries of one request: the attempt to send next, and how many
    were made before it."""

    def __init__(self, request: Request, policy: RetryPolicy) -> None:
        self.request = request
        self.policy = policy
        self.attempt = request
        self.count = 0

    def delay_after(
        self,
        outcome: Response
        | StreamedResponse
        | AsyncStreamedResponse
        | SupabaseTransportError,
    ) -> float | None:
        """Seconds to wait before the next attempt, or None when `outcome` is
        the final one. Prepares the next attempt when there is one."""
        delay = self.policy.delay(outcome, self.count)
        if delay is None:
            return None
        self.count += 1
        self.attempt = replace(
            self.request,
            headers=self.request.headers.override("X-Retry-Count", str(self.count)),
        )
        logger.debug(
            "%s %s failed, retry %d of %d in %.2f seconds",
            self.request.method,
            self.request.url.raw_path,
            self.count,
            self.policy.max_retries,
            delay,
            extra={
                "http_method": self.request.method,
                "http_path": self.request.url.raw_path,
                "retry": self.count,
                "delay": delay,
            },
        )
        return delay


class _HttpIO[Session]:
    def __init__(
        self,
        session: Session,
        request_timeout: float | None = None,
        retry: RetryPolicy | None = None,
    ) -> None:
        validate_request_timeout(request_timeout)
        self.session = session
        self.request_timeout = request_timeout
        self.retry_policy = retry if retry is not None else RetryPolicy()

    def _finalize(
        self, http_request: ToRequest, base_url: URL, default_headers: Headers
    ) -> Request:
        request = http_request.finalize(base_url, default_headers)
        if request.timeout is None and self.request_timeout is not None:
            request = replace(request, timeout=self.request_timeout)
        return request

    def _retries(self, request: Request) -> _Retries | None:
        policy = _policy_for(request, self.retry_policy)
        return None if policy is None else _Retries(request, policy)


class SyncHttpIO(_HttpIO[HttpSession]):
    @override
    def _finalize(
        self, http_request: ToRequest, base_url: URL, default_headers: Headers
    ) -> Request:
        request = super()._finalize(http_request, base_url, default_headers)
        if isinstance(request.content, AsyncIterable):
            raise TypeError(
                "A sync client cannot send an async iterable body, "
                "pass a sync iterable or use the async client"
            )
        return request

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
                request = self._finalize(http_request, base_url, default_headers)
                if request.delay:
                    time.sleep(request.delay)
                response = self._send(request)
                http_request = iterator.send(response)
        except StopIteration:
            return return_value_iterator.return_value
        finally:
            iterator.close()

    @contextmanager
    def stream(
        self, base_url: URL, default_headers: Headers, http_request: ToRequest
    ) -> Generator[StreamedResponse]:
        """Sends `http_request` and yields the response once its head arrives,
        with the body still to read. The request is retried only before that,
        as `communicate` retries it. Leaving the context closes the response."""
        request = self._finalize(http_request, base_url, default_headers)
        if request.delay:
            time.sleep(request.delay)
        retries = self._retries(request)
        while True:
            returned = False
            try:
                with self.session.stream(
                    request if retries is None else retries.attempt
                ) as response:
                    delay = None if retries is None else retries.delay_after(response)
                    if delay is None:
                        returned = True
                        yield response
                        return
            except SupabaseTransportError as error:
                if returned or retries is None:
                    raise
                delay = retries.delay_after(error)
                if delay is None:
                    raise
            time.sleep(delay)

    def _send_once(self, request: Request) -> Response:
        started = perf_counter()
        try:
            response = self.session.send(request)
        except SupabaseTransportError as error:
            _log_transport_error(request, started, error)
            raise
        _log_response(request, started, response)
        return response

    def _send(self, request: Request) -> Response:
        retries = self._retries(request)
        if retries is None:
            return self._send_once(request)
        while True:
            try:
                response = self._send_once(retries.attempt)
            except SupabaseTransportError as error:
                delay = retries.delay_after(error)
                if delay is None:
                    raise
            else:
                delay = retries.delay_after(response)
                if delay is None:
                    return response
            time.sleep(delay)


class AsyncHttpIO(_HttpIO[AsyncHttpSession]):
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
                request = self._finalize(http_request, base_url, default_headers)
                if request.delay:
                    await asyncio.sleep(request.delay)
                response = await self._send(request)
                http_request = iterator.send(response)
        except StopIteration:
            return return_value_iterator.return_value
        finally:
            iterator.close()

    @asynccontextmanager
    async def stream(
        self, base_url: URL, default_headers: Headers, http_request: ToRequest
    ) -> AsyncGenerator[AsyncStreamedResponse]:
        """Sends `http_request` and yields the response once its head arrives,
        with the body still to read. The request is retried only before that,
        as `communicate` retries it. Leaving the context closes the response."""
        request = self._finalize(http_request, base_url, default_headers)
        if request.delay:
            await asyncio.sleep(request.delay)
        retries = self._retries(request)
        while True:
            returned = False
            try:
                async with self.session.stream(
                    request if retries is None else retries.attempt
                ) as response:
                    delay = None if retries is None else retries.delay_after(response)
                    if delay is None:
                        returned = True
                        yield response
                        return
            except SupabaseTransportError as error:
                if returned or retries is None:
                    raise
                delay = retries.delay_after(error)
                if delay is None:
                    raise
            await asyncio.sleep(delay)

    async def _send_once(self, request: Request) -> Response:
        started = perf_counter()
        try:
            response = await self.session.send(request)
        except SupabaseTransportError as error:
            _log_transport_error(request, started, error)
            raise
        _log_response(request, started, response)
        return response

    async def _send(self, request: Request) -> Response:
        retries = self._retries(request)
        if retries is None:
            return await self._send_once(request)
        while True:
            try:
                response = await self._send_once(retries.attempt)
            except SupabaseTransportError as error:
                delay = retries.delay_after(error)
                if delay is None:
                    raise
            else:
                delay = retries.delay_after(response)
                if delay is None:
                    return response
            await asyncio.sleep(delay)


class _HasExecutor[HttpIO: (SyncHttpIO, AsyncHttpIO)](Protocol):
    @property
    def executor(self) -> HttpIO: ...
    @property
    def base_url(self) -> URL: ...
    @property
    def default_headers(self) -> Headers: ...


@dataclass
class handle_http_io[**Params, Success]:
    method: Callable[Concatenate[Any, Params], HttpMethod[Success]]

    @overload
    def __get__(
        self, obj: _HasExecutor[SyncHttpIO], objtype: type | None = None
    ) -> Callable[Params, Success]: ...

    @overload
    def __get__(
        self, obj: _HasExecutor[AsyncHttpIO], objtype: type | None = None
    ) -> Callable[Params, Awaitable[Success]]: ...

    def __get__(
        self,
        obj: _HasExecutor[SyncHttpIO] | _HasExecutor[AsyncHttpIO],
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
