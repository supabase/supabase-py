from collections.abc import Mapping
from typing import Literal, cast, overload

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
from supabase_utils.types import JSON
from yarl import URL

from .errors import _is_relay_error, _on_error_response
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

        Parameters
        ----------
        token : str
            the new jwt token sent in the authorization header
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
    ) -> ToRequest:
        if not is_valid_string_argument(function_name):
            raise ValueError("function_name must be a valid string value.")

        path = [function_name]
        new_headers = Headers.from_mapping(headers) if headers else Headers.empty()
        if "content-type" not in new_headers and (
            client_content_type := self.default_headers.get("Content-Type")
        ):
            new_headers = new_headers.set("Content-Type", client_content_type)
        query_params = URLQuery.empty()

        if region and (resolved := FunctionRegion(region)) != FunctionRegion.Any:
            new_headers = new_headers.override("x-region", resolved.value)
            # Add region as query parameter
            query_params = query_params.set("forceFunctionRegion", resolved.value)
        if body is None:
            return EmptyRequest(
                method=method,
                path=path,
                headers=new_headers,
                query=query_params,
                timeout=request_timeout,
            )
        if isinstance(body, str):
            return TextRequest(
                text=body,
                method=method,
                path=path,
                headers=new_headers,
                query=query_params,
                timeout=request_timeout,
            )
        if isinstance(body, (bytes, bytearray)):
            return BytesRequest(
                body=bytes(body),
                method=method,
                path=path,
                headers=new_headers,
                query=query_params,
                timeout=request_timeout,
            )
        if isinstance(body, (dict, list)):
            return JSONRequest(
                body=body,
                method=method,
                path=path,
                headers=new_headers,
                query=query_params,
                timeout=request_timeout,
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
    ) -> HttpMethod[Response]:
        """Invokes a function

        Parameters
        ----------
        function_name : the name of the function to invoke
        body : the request body. A str is sent as text, bytes as binary data,
            and a dict or list as JSON.
        region : the region to invoke the function in
        headers : extra headers to send with the request
        method : the HTTP method to use, POST by default
        request_timeout : seconds the invocation may go without progress,
            overriding the timeout of the client
        """
        response = yield self._invoke_options_to_request(
            function_name, body, region, headers, method, request_timeout
        )
        if _is_relay_error(response) or not response.is_success:
            raise _on_error_response(response)
        return response


class AsyncFunctionsClient(FunctionsClient[AsyncHttpIO]):
    def __init__(
        self,
        url: str,
        headers: Mapping[str, str],
        http_session: AsyncHttpSession,
        *,
        request_timeout: float | None = None,
    ) -> None:
        """Create a functions client.

        Parameters
        ----------
        url : the URL of the functions service
        headers : headers sent with every invocation
        http_session : the HTTP session that sends the requests
        request_timeout : seconds an invocation may go without progress before
            it fails with `RequestTimeoutError`. None leaves the timeout to the
            HTTP client.
        """
        super().__init__(
            url=URL(url),
            executor=AsyncHttpIO(session=http_session, request_timeout=request_timeout),
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
    ) -> None:
        """Create a functions client.

        Parameters
        ----------
        url : the URL of the functions service
        headers : headers sent with every invocation
        http_session : the HTTP session that sends the requests
        request_timeout : seconds an invocation may go without progress before
            it fails with `RequestTimeoutError`. None leaves the timeout to the
            HTTP client.
        """
        super().__init__(
            url=URL(url),
            executor=SyncHttpIO(session=http_session, request_timeout=request_timeout),
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
) -> AsyncFunctionsClient: ...


@overload
def create_client(
    url: str,
    headers: dict[str, str],
    *,
    http_session: HttpSession,
    is_async: Literal[False],
    request_timeout: float | None = None,
) -> SyncFunctionsClient: ...


def create_client(
    url: str,
    headers: dict[str, str],
    *,
    http_session: AsyncHttpSession | HttpSession,
    is_async: bool,
    request_timeout: float | None = None,
) -> AsyncFunctionsClient | SyncFunctionsClient:
    if is_async:
        return AsyncFunctionsClient(
            url,
            headers,
            cast("AsyncHttpSession", http_session),
            request_timeout=request_timeout,
        )
    return SyncFunctionsClient(
        url,
        headers,
        cast("HttpSession", http_session),
        request_timeout=request_timeout,
    )
