import platform
from typing import Dict, Generic, Literal, Optional, Union, overload
from warnings import warn

from httpx import AsyncClient, Client, Headers, QueryParams, Response
from supabase_utils.http import (
    AsyncExecutor,
    BytesRequest,
    EmptyRequest,
    Executor,
    HTTPRequestMethod,
    JSONRequest,
    ResponseHandler,
    SyncExecutor,
    TextRequest,
    ToHttpxRequest,
    http_request,
)
from supabase_utils.types import JSON
from yarl import URL

from .errors import FunctionsHttpError, FunctionsRelayError, on_error_response
from .utils import (
    FunctionRegion,
    is_valid_str_arg,
)
from .version import __version__


class FunctionsClient(Generic[Executor]):
    def __init__(
        self,
        url: URL,
        headers: Dict[str, str],
        executor: Executor,
        timeout: Optional[int] = None,
        verify: Optional[bool] = None,
        proxy: Optional[str] = None,
    ) -> None:
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

        if timeout is not None:
            warn(
                "The 'timeout' parameter is deprecated. Please configure it in the http client instead.",
                DeprecationWarning,
                stacklevel=2,
            )
        if verify is not None:
            warn(
                "The 'verify' parameter is deprecated. Please configure it in the http client instead.",
                DeprecationWarning,
                stacklevel=2,
            )
        if proxy is not None:
            warn(
                "The 'proxy' parameter is deprecated. Please configure it in the http client instead.",
                DeprecationWarning,
                stacklevel=2,
            )

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
        body: Union[bytes, str, Dict[str, JSON], None],
        region: Optional[FunctionRegion],
        headers: Optional[Dict[str, str]],
        method: Optional[HTTPRequestMethod],
    ) -> ToHttpxRequest:
        if not is_valid_str_arg(function_name):
            raise ValueError("function_name must a valid string value.")

        method = method or "POST"
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

    @http_request
    def invoke(
        self,
        function_name: str,
        body: Union[bytes, str, Dict[str, JSON], None] = None,
        region: Optional[FunctionRegion] = None,
        headers: Optional[Dict[str, str]] = None,
        method: Optional[HTTPRequestMethod] = None,
    ) -> ResponseHandler[Response, Union[FunctionsHttpError, FunctionsRelayError]]:
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
        return ResponseHandler(
            request=request,
            on_success=lambda response: response,
            on_failure=on_error_response,
        )


class AsyncFunctionsClient(FunctionsClient[AsyncExecutor]):
    def __init__(
        self,
        url: str,
        headers: Dict[str, str],
        timeout: Optional[int] = None,
        verify: Optional[bool] = None,
        proxy: Optional[str] = None,
        http_client: Optional[AsyncClient] = None,
    ) -> None:
        self.url = URL(url)  # kept for backwards compatibility
        self.verify = (
            bool(verify) if verify is not None else True
        )  # kept for backwards compatibility
        self.timeout = (
            int(abs(timeout)) if timeout is not None else 60
        )  # kept for backwards compatibility
        self._client = http_client or AsyncClient(  # kept for backwards compatibility
            verify=self.verify,
            timeout=self.timeout,
            proxy=proxy,
            follow_redirects=True,
            http2=True,
        )
        FunctionsClient.__init__(
            self,
            url=self.url,
            executor=AsyncExecutor(session=self._client),
            headers=headers,
            timeout=timeout,
            proxy=proxy,
        )


class SyncFunctionsClient(FunctionsClient[SyncExecutor]):
    def __init__(
        self,
        url: str,
        headers: Dict[str, str],
        timeout: Optional[int] = None,
        verify: Optional[bool] = None,
        proxy: Optional[str] = None,
        http_client: Optional[Client] = None,
    ) -> None:
        self.url = URL(url)  # kept for backwards compatibility
        self.verify = (
            bool(verify) if verify is not None else True
        )  # kept for backwards compatibility
        self.timeout = (
            int(abs(timeout)) if timeout is not None else 60
        )  # kept for backwards compatibility
        self._client = http_client or Client(  # kept for backwards compatibility
            verify=self.verify,
            timeout=self.timeout,
            proxy=proxy,
            follow_redirects=True,
            http2=True,
        )
        FunctionsClient.__init__(
            self,
            url=self.url,
            executor=SyncExecutor(session=self._client),
            headers=headers,
            timeout=timeout,
            proxy=proxy,
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
) -> Union[AsyncFunctionsClient, SyncFunctionsClient]:
    if is_async:
        return AsyncFunctionsClient(url, headers, verify=verify)
    else:
        return SyncFunctionsClient(url, headers, verify=verify)
