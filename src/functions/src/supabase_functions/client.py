import platform
from typing import Generic, Literal, overload

from httpx import AsyncClient, Client, Headers, QueryParams, Response
from supabase_utils.http import (
    AsyncExecutor,
    BytesRequest,
    EmptyRequest,
    Executor,
    HTTPRequestMethod,
    JSONRequest,
    ResponseCases,
    ResponseHandler,
    SyncExecutor,
    TextRequest,
    ToHttpxRequest,
    handle_http_response,
)
from supabase_utils.types import JSON
from yarl import URL

from .errors import on_error_response
from .utils import (
    FunctionRegion,
    is_valid_str_arg,
)
from .version import __version__


class FunctionsClient(Generic[Executor]):
    def __init__(self, url: URL, headers: dict[str, str], executor: Executor) -> None:
        if not (url.scheme == "http" or url.scheme == "https"):
            raise ValueError("url must be a valid HTTP URL string")
        self.headers = {
            "X-Client-Info": f"supabase-py/supabase_functions v{__version__}",
            "X-Supabase-Client-Platform": platform.system(),
            "X-Supabase-Client-Platform-Version": platform.release(),
            "X-Supabase-Client-Runtime": "python",
            "X-Supabase-Client-Runtime-Version": platform.python_version(),
            **headers,
        }

        self.executor: Executor = executor
        self.base_url = url

    def set_auth(self, token: str) -> None:
        """Updates the authorization header

        Parameters
        ----------
        token : str
            the new jwt token sent in the authorization header
        """

        self.headers["Authorization"] = f"Bearer {token}"

    def _invoke_options_to_request(
        self,
        function_name: str,
        body: bytes | str | dict[str, JSON] | None,
        region: FunctionRegion | None,
        headers: dict[str, str] | None,
        method: HTTPRequestMethod,
    ) -> ToHttpxRequest:
        if not is_valid_str_arg(function_name):
            raise ValueError("function_name must a valid string value.")

        path = [function_name]
        new_headers = Headers(self.headers)
        query_params = QueryParams()

        if headers:
            new_headers.update(headers)
        if region and region != FunctionRegion.Any:
            new_headers["x-region"] = region.value
            # Add region as query parameter
            query_params = query_params.set("forceFunctionRegion", region.value)

        if isinstance(body, str):
            return TextRequest(
                text=body,
                method=method,
                path=path,
                headers=new_headers,
                query_params=query_params,
            )
        elif isinstance(body, dict):
            return JSONRequest(
                body=body,
                method=method,
                path=path,
                headers=new_headers,
                query_params=query_params,
                exclude_none=False,
            )
        elif isinstance(body, bytes):
            return BytesRequest(
                body=body,
                method=method,
                path=path,
                headers=new_headers,
                query_params=query_params,
            )
        else:
            return EmptyRequest(
                method=method, path=path, headers=new_headers, query_params=query_params
            )

    @handle_http_response
    def invoke(
        self,
        function_name: str,
        body: bytes | str | dict[str, JSON] | None = None,
        region: FunctionRegion | None = None,
        headers: dict[str, str] | None = None,
        method: HTTPRequestMethod = "POST",
    ) -> ResponseHandler[Response]:
        """Invokes a function

        Parameters
        ----------
        function_name : the name of the function to invoke
        invoke_options : object with the following properties
            `headers`: object representing the headers to send with the request
            `body`: the body of the request
            `responseType`: how the response should be parsed. The default is `json`
        """
        request = self._invoke_options_to_request(
            function_name, body, region, headers, method
        )
        return ResponseCases(
            request=request,
            on_success=lambda response: response,
            on_failure=on_error_response,
        )


class AsyncFunctionsClient(FunctionsClient[AsyncExecutor]):
    def __init__(
        self,
        url: str,
        headers: dict[str, str],
        timeout: int = 60,
        verify: bool = True,
        proxy: str | None = None,
        http_client: AsyncClient | None = None,
    ) -> None:
        http_client = http_client or AsyncClient(
            verify=verify,
            timeout=timeout,
            proxy=proxy,
            follow_redirects=True,
            http2=True,
        )
        FunctionsClient.__init__(
            self,
            url=URL(url),
            executor=AsyncExecutor(session=http_client),
            headers=headers,
        )


class SyncFunctionsClient(FunctionsClient[SyncExecutor]):
    def __init__(
        self,
        url: str,
        headers: dict[str, str],
        timeout: int = 60,
        verify: bool = True,
        proxy: str | None = None,
        http_client: Client | None = None,
    ) -> None:
        http_client = http_client or Client(  # kept for backwards compatibility
            verify=verify,
            timeout=timeout,
            proxy=proxy,
            follow_redirects=True,
            http2=True,
        )
        FunctionsClient.__init__(
            self,
            url=URL(url),
            executor=SyncExecutor(session=http_client),
            headers=headers,
        )


@overload
def create_client(
    url: str, headers: dict[str, str], *, is_async: Literal[True], verify: bool
) -> AsyncFunctionsClient: ...


@overload
def create_client(
    url: str, headers: dict[str, str], *, is_async: Literal[False], verify: bool
) -> SyncFunctionsClient: ...


def create_client(
    url: str,
    headers: dict[str, str],
    *,
    is_async: bool,
    verify: bool = True,
) -> AsyncFunctionsClient | SyncFunctionsClient:
    if is_async:
        return AsyncFunctionsClient(url, headers, verify=verify)
    else:
        return SyncFunctionsClient(url, headers, verify=verify)
