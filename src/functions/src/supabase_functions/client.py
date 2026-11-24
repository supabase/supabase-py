from collections.abc import AsyncGenerator, Generator, Mapping
from contextlib import (
    AbstractAsyncContextManager,
    AbstractContextManager,
    asynccontextmanager,
    contextmanager,
)
from typing import Any, Literal, cast, overload
from urllib.parse import parse_qsl

from supabase_utils.http.headers import Headers
from supabase_utils.http.io import (
    AsyncHttpIO,
    AsyncHttpSession,
    HttpMethod,
    HttpSession,
    SyncHttpIO,
    handle_http_io,
)
from supabase_utils.http.query import URLQuery
from supabase_utils.http.request import (
    BytesRequest,
    EmptyRequest,
    HTTPRequestMethod,
    JSONRequest,
    Response,
    TextRequest,
    ToRequest,
)
from supabase_utils.http.retry import RetryPolicy
from supabase_utils.types import JSON
from yarl import URL

from .errors import _is_relay_error, _on_error_response
from .stream import AsyncFunctionResponseStream, FunctionResponseStream
from .utils import (
    FunctionRegion,
    is_valid_string_argument,
)
from .version import __version__


class FunctionsClient[HttpIO: (SyncHttpIO, AsyncHttpIO)]:
    def __init__(self, url: URL, headers: Mapping[str, str], executor: HttpIO) -> None:
        if not (url.scheme == "http" or url.scheme == "https"):
            raise ValueError("url must be a valid HTTP URL string")
        supabase_headers = Headers.supabase_client_headers(
            "supabase_functions", __version__
        )
        user_headers = Headers.from_mapping(headers)
        self.default_headers = supabase_headers.update(user_headers)

        self.executor: HttpIO = executor
        self.base_url = url

    def set_auth(self, token: str) -> None:
        """Updates the authorization header

        Args:
            token: the new jwt token sent in the authorization header
        """

        self.default_headers = self.default_headers.override(
            "Authorization", f"Bearer {token}"
        )

    def _invoke_options_to_request(
        self,
        function_name: str,
        body: bytes | bytearray | str | dict[str, JSON] | list[JSON] | None,
        region: FunctionRegion | str | None,
        headers: dict[str, str] | None,
        method: HTTPRequestMethod,
        request_timeout: float | None,
        retry: RetryPolicy | bool | None,
    ) -> ToRequest:
        if not isinstance(function_name, str):
            raise ValueError("function_name must be a valid string value.")
        name, _, query_string = function_name.split("#", 1)[0].partition("?")
        if not is_valid_string_argument(name):
            raise ValueError("function_name must be a valid string value.")

        path = [name]
        new_headers = Headers.from_mapping(headers) if headers else Headers.empty()
        if "content-type" not in new_headers and (
            client_content_type := self.default_headers.get("Content-Type")
        ):
            new_headers = new_headers.set("Content-Type", client_content_type)
        query_params = URLQuery.empty()
        for key, value in parse_qsl(query_string, keep_blank_values=True):
            query_params = query_params.set(key, value)

        if region and (resolved := str(region)) != FunctionRegion.Any:
            new_headers = new_headers.override("x-region", resolved)
            query_params = query_params.override("forceFunctionRegion", resolved)
        if body is None:
            return EmptyRequest(
                method=method,
                path=path,
                headers=new_headers,
                query=query_params,
                timeout=request_timeout,
                retry=retry,
            )
        if isinstance(body, str):
            return TextRequest(
                text=body,
                method=method,
                path=path,
                headers=new_headers,
                query=query_params,
                timeout=request_timeout,
                retry=retry,
            )
        if isinstance(body, (bytes, bytearray)):
            return BytesRequest(
                body=bytes(body),
                method=method,
                path=path,
                headers=new_headers,
                query=query_params,
                timeout=request_timeout,
                retry=retry,
            )
        if isinstance(body, (dict, list)):
            return JSONRequest(
                body=body,
                method=method,
                path=path,
                headers=new_headers,
                query=query_params,
                timeout=request_timeout,
                retry=retry,
            )
        raise TypeError(
            f"body must be str, bytes, dict, list or None, not {type(body).__name__}"
        )

    @handle_http_io
    def invoke(
        self,
        function_name: str,
        body: bytes | bytearray | str | dict[str, JSON] | list[JSON] | None = None,
        region: FunctionRegion | str | None = None,
        headers: dict[str, str] | None = None,
        method: HTTPRequestMethod = "POST",
        request_timeout: float | None = None,
        retry: RetryPolicy | bool | None = None,
    ) -> HttpMethod[Response]:
        """Invokes a function

        Args:
            function_name: the name of the function to invoke. It may carry a
                query string, as in `hello?name=bob`, whose parameters are sent
                with the request. A `#fragment` is dropped.
            body: the request body. A str is sent as text, bytes as binary data,
                and a dict or list as JSON.
            region: the region to invoke the function in, a FunctionRegion or
                any region name as a string
            headers: extra headers to send with the request
            method: the HTTP method to use, POST by default
            request_timeout: seconds the invocation may go without progress,
                overriding the timeout of the client
            retry: how the invocation is retried when it fails in a way worth
                repeating. None leaves it to the `RetryPolicy` of the client,
                which retries GET and HEAD invocations only. True retries the
                invocation with that policy, and a `RetryPolicy` with that policy
                instead, both whatever its method, for a function that is safe to
                invoke twice. False never retries it.
        """
        response = yield self._invoke_options_to_request(
            function_name, body, region, headers, method, request_timeout, retry
        )
        if _is_relay_error(response) or not response.is_success:
            raise _on_error_response(response)
        return response

    @overload
    def invoke_stream(
        self: "FunctionsClient[SyncHttpIO]",
        function_name: str,
        body: bytes | bytearray | str | dict[str, JSON] | list[JSON] | None = None,
        region: FunctionRegion | str | None = None,
        headers: dict[str, str] | None = None,
        method: HTTPRequestMethod = "POST",
        request_timeout: float | None = None,
        retry: RetryPolicy | bool | None = None,
    ) -> AbstractContextManager[FunctionResponseStream]: ...

    @overload
    def invoke_stream(
        self: "FunctionsClient[AsyncHttpIO]",
        function_name: str,
        body: bytes | bytearray | str | dict[str, JSON] | list[JSON] | None = None,
        region: FunctionRegion | str | None = None,
        headers: dict[str, str] | None = None,
        method: HTTPRequestMethod = "POST",
        request_timeout: float | None = None,
        retry: RetryPolicy | bool | None = None,
    ) -> AbstractAsyncContextManager[AsyncFunctionResponseStream]: ...

    def invoke_stream(
        self: "FunctionsClient[Any]",
        function_name: str,
        body: bytes | bytearray | str | dict[str, JSON] | list[JSON] | None = None,
        region: FunctionRegion | str | None = None,
        headers: dict[str, str] | None = None,
        method: HTTPRequestMethod = "POST",
        request_timeout: float | None = None,
        retry: RetryPolicy | bool | None = None,
    ) -> (
        AbstractContextManager[FunctionResponseStream]
        | AbstractAsyncContextManager[AsyncFunctionResponseStream]
    ):
        """Invokes a function and reads its response as it arrives, for a
        function that streams, such as one that sends server-sent events.

        Entering the returned context sends the request and gives the response
        once its head arrived, with its status and headers. Its body is read
        with `iter_text()`, `iter_events()`, `read()` or by iterating over the
        chunks. An error response raises the same errors as `invoke()`.
        Leaving the context closes the connection.

        ```python
        with functions.invoke_stream("chat", body={"prompt": "Hi"}) as response:
            for event in response.iter_events():
                print(event.data)

        async with functions.invoke_stream("chat", body={"prompt": "Hi"}) as response:
            async for event in response.iter_events():
                print(event.data)
        ```

        The parameters are those of `invoke()`. `request_timeout` limits how
        long the body may go without a new chunk, not how long it may take
        in total, though a total timeout of the HTTP client still applies.
        """
        request = self._invoke_options_to_request(
            function_name, body, region, headers, method, request_timeout, retry
        )
        if isinstance(self.executor, AsyncHttpIO):
            return _async_invoke_stream(
                self.executor, self.base_url, self.default_headers, request
            )
        return _sync_invoke_stream(
            self.executor, self.base_url, self.default_headers, request
        )


@contextmanager
def _sync_invoke_stream(
    executor: SyncHttpIO, base_url: URL, headers: Headers, request: ToRequest
) -> Generator[FunctionResponseStream]:
    with executor.stream(base_url, headers, request) as response:
        if _is_relay_error(response) or not response.is_success:
            raise _on_error_response(response.read())
        yield FunctionResponseStream(response)


@asynccontextmanager
async def _async_invoke_stream(
    executor: AsyncHttpIO, base_url: URL, headers: Headers, request: ToRequest
) -> AsyncGenerator[AsyncFunctionResponseStream]:
    async with executor.stream(base_url, headers, request) as response:
        if _is_relay_error(response) or not response.is_success:
            raise _on_error_response(await response.read())
        yield AsyncFunctionResponseStream(response)


class AsyncFunctionsClient(FunctionsClient[AsyncHttpIO]):
    def __init__(
        self,
        url: str,
        headers: Mapping[str, str],
        http_session: AsyncHttpSession,
        *,
        request_timeout: float | None = None,
        retry: RetryPolicy | None = None,
    ) -> None:
        """Create a functions client.

        Args:
            url: the URL of the functions service
            headers: headers sent with every invocation
            http_session: the HTTP session that sends the requests
            request_timeout: seconds an invocation may go without progress before
                it fails with `RequestTimeoutError`. None leaves the timeout to the
                HTTP client.
            retry: how GET and HEAD invocations that failed in a way worth
                repeating are retried. None uses the default `RetryPolicy`. Use
                the `retry` argument of `invoke()` to override it for one
                invocation.
        """
        super().__init__(
            url=URL(url),
            executor=AsyncHttpIO(
                session=http_session, request_timeout=request_timeout, retry=retry
            ),
            headers=headers,
        )


class SyncFunctionsClient(FunctionsClient[SyncHttpIO]):
    def __init__(
        self,
        url: str,
        headers: Mapping[str, str],
        http_session: HttpSession,
        *,
        request_timeout: float | None = None,
        retry: RetryPolicy | None = None,
    ) -> None:
        """Create a functions client.

        Args:
            url: the URL of the functions service
            headers: headers sent with every invocation
            http_session: the HTTP session that sends the requests
            request_timeout: seconds an invocation may go without progress before
                it fails with `RequestTimeoutError`. None leaves the timeout to the
                HTTP client.
            retry: how GET and HEAD invocations that failed in a way worth
                repeating are retried. None uses the default `RetryPolicy`. Use
                the `retry` argument of `invoke()` to override it for one
                invocation.
        """
        super().__init__(
            url=URL(url),
            executor=SyncHttpIO(
                session=http_session, request_timeout=request_timeout, retry=retry
            ),
            headers=headers,
        )


@overload
def create_client(
    url: str,
    headers: dict[str, str],
    *,
    http_session: AsyncHttpSession,
    is_async: Literal[True],
    request_timeout: float | None = None,
    retry: RetryPolicy | None = None,
) -> AsyncFunctionsClient: ...


@overload
def create_client(
    url: str,
    headers: dict[str, str],
    *,
    http_session: HttpSession,
    is_async: Literal[False],
    request_timeout: float | None = None,
    retry: RetryPolicy | None = None,
) -> SyncFunctionsClient: ...


def create_client(
    url: str,
    headers: dict[str, str],
    *,
    http_session: AsyncHttpSession | HttpSession,
    is_async: bool,
    request_timeout: float | None = None,
    retry: RetryPolicy | None = None,
) -> AsyncFunctionsClient | SyncFunctionsClient:
    if is_async:
        return AsyncFunctionsClient(
            url,
            headers,
            cast("AsyncHttpSession", http_session),
            request_timeout=request_timeout,
            retry=retry,
        )
    return SyncFunctionsClient(
        url,
        headers,
        cast("HttpSession", http_session),
        request_timeout=request_timeout,
        retry=retry,
    )
