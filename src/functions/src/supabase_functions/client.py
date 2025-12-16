from typing import Dict, Generic, Literal, Optional, Union, overload
from warnings import warn

from httpx import AsyncClient, Client, Headers, QueryParams, Response
from supabase_utils.http import (
    AsyncExecutor,
    EndpointRequest,
    Executor,
    FromHTTPResponse,
    ServerEndpoint,
    SyncExecutor,
    http_endpoint,
)
from supabase_utils.types import JSON, JSONParser
from yarl import URL

from .errors import FunctionsHttpError, FunctionsRelayError, on_error_response
from .utils import (
    FunctionRegion,
    is_valid_str_arg,
)
from .version import __version__


def json_or_bytes(json: bool) -> FromHTTPResponse[Union[bytes, JSON]]:
    def from_response(response: Response) -> Union[bytes, JSON]:
        if json:
            return JSONParser.validate_json(response.content)
        else:
            return response.content

    return from_response


class FunctionsClient(Generic[Executor]):
    def __init__(
        self,
        url: URL,
        headers: Dict,
        executor: Executor,
        timeout: Optional[int] = None,
        verify: Optional[bool] = None,
        proxy: Optional[str] = None,
    ) -> None:
        self.headers = {
            "User-Agent": f"supabase-py/functions-py v{__version__}",
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

    @http_endpoint
    def invoke(
        self, *, function_name: str, invoke_options: Optional[Dict] = None
    ) -> ServerEndpoint[Union[JSON, bytes], FunctionsHttpError | FunctionsRelayError]:
        """Invokes a function

        Parameters
        ----------
        function_name : the name of the function to invoke
        invoke_options : object with the following properties
            `headers`: object representing the headers to send with the request
            `body`: the body of the request
            `responseType`: how the response should be parsed. The default is `json`
        """
        if not is_valid_str_arg(function_name):
            raise ValueError("function_name must a valid string value.")
        headers = self.headers
        params = QueryParams()
        body = None
        response_type = "text/plain"

        if invoke_options is not None:
            headers.update(invoke_options.get("headers", {}))
            response_type = invoke_options.get("responseType", "text/plain")

            region = invoke_options.get("region")
            if region:
                if not isinstance(region, FunctionRegion):
                    warn(f"Use FunctionRegion({region})", stacklevel=2)
                    region = FunctionRegion(region)

                if region.value != "any":
                    headers["x-region"] = region.value
                    # Add region as query parameter
                    params = params.set("forceFunctionRegion", region.value)

            body = invoke_options.get("body")
            if isinstance(body, str):
                headers["Content-Type"] = "text/plain"
            elif isinstance(body, dict):
                headers["Content-Type"] = "application/json"

        return ServerEndpoint(
            request=EndpointRequest(
                method="POST",
                path=[function_name],
                headers=Headers(headers),
                body=body,
                query_params=params,
            ),
            on_success=json_or_bytes(response_type == "json"),
            on_failure=on_error_response,
        )


class AsyncFunctionsClient(FunctionsClient[AsyncExecutor]):
    def __init__(
        self,
        url: str,
        headers: Dict,
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
        headers: Dict,
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
        return AsyncFunctionsClient(url, headers, verify)
    else:
        return SyncFunctionsClient(url, headers, verify)
