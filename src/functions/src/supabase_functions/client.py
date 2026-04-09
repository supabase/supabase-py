import platform
from typing import Dict, Generic, Literal, overload

from httpx import AsyncClient, Client
from supabase_utils.http.adapters.httpx import AsyncHttpxSession, HttpxSession
from supabase_utils.http.headers import Headers
from supabase_utils.http.io import (
    AsyncHttpIO,
    HttpIO,
    HttpMethod,
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

from .errors import on_error_response
from .utils import (
    FunctionRegion,
    is_valid_str_arg,
)
from .version import __version__


class FunctionsClient(Generic[HttpIO]):
    def __init__(self, url: URL, headers: Dict[str, str], executor: HttpIO) -> None:
        if not (url.scheme == "http" or url.scheme == "https"):
            raise ValueError("url must be a valid HTTP URL string")
        self.default_headers = Headers.from_mapping(
            {
                "X-Client-Info": f"supabase-py/supabase_functions v{__version__}",
                "X-Supabase-Client-Platform": platform.system(),
                "X-Supabase-Client-Platform-Version": platform.release(),
                "X-Supabase-Client-Runtime": "python",
                "X-Supabase-Client-Runtime-Version": platform.python_version(),
                **headers,
            }
        )

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
        body: bytes | str | Dict[str, JSON] | None,
        region: FunctionRegion | None,
        headers: Dict[str, str] | None,
        method: HTTPRequestMethod,
    ) -> ToRequest:
        if not is_valid_str_arg(function_name):
            raise ValueError("function_name must a valid string value.")

        path = [function_name]
        new_headers = Headers.from_mapping(headers) if headers else Headers.empty()
        query_params = URLQuery.empty()

        if region and region != FunctionRegion.Any:
            new_headers = new_headers.set("x-region", region.value)
            # Add region as query parameter
            query_params = query_params.set("forceFunctionRegion", region.value)
        if isinstance(body, str):
            return TextRequest(
                text=body,
                method=method,
                path=path,
                headers=new_headers,
                query=query_params,
            )
        elif isinstance(body, dict):
            return JSONRequest(
                body=body,
                method=method,
                path=path,
                headers=new_headers,
                query=query_params,
                exclude_none=False,
            )
        elif isinstance(body, bytes):
            return BytesRequest(
                body=body,
                method=method,
                path=path,
                headers=new_headers,
                query=query_params,
            )
        else:
            return EmptyRequest(
                method=method, path=path, headers=new_headers, query=query_params
            )

    @handle_http_io
    def invoke(
        self,
        function_name: str,
        body: bytes | str | Dict[str, JSON] | None = None,
        region: FunctionRegion | None = None,
        headers: Dict[str, str] | None = None,
        method: HTTPRequestMethod = "POST",
    ) -> HttpMethod[Response]:
        """Invokes a function

        Parameters
        ----------
        function_name : the name of the function to invoke
        invoke_options : object with the following properties
            `headers`: object representing the headers to send with the request
            `body`: the body of the request
            `responseType`: how the response should be parsed. The default is `json`
        """
        response = yield self._invoke_options_to_request(
            function_name, body, region, headers, method
        )
        if not response.is_success:
            raise on_error_response(response)
        return response


class AsyncFunctionsClient(FunctionsClient[AsyncHttpIO]):
    def __init__(
        self,
        url: str,
        headers: Dict[str, str],
        http_client: AsyncClient | None = None,
    ) -> None:
        http_client = http_client or AsyncClient(
            follow_redirects=True,
            http2=True,
        )
        FunctionsClient.__init__(
            self,
            url=URL(url),
            executor=AsyncHttpIO(session=AsyncHttpxSession(client=http_client)),
            headers=headers,
        )


class SyncFunctionsClient(FunctionsClient[SyncHttpIO]):
    def __init__(
        self,
        url: str,
        headers: Dict[str, str],
        http_client: Client | None = None,
    ) -> None:
        http_client = http_client or Client(
            follow_redirects=True,
            http2=True,
        )
        FunctionsClient.__init__(
            self,
            url=URL(url),
            executor=SyncHttpIO(session=HttpxSession(client=http_client)),
            headers=headers,
        )


@overload
def create_client(
    url: str, headers: dict[str, str], *, is_async: Literal[True]
) -> AsyncFunctionsClient: ...


@overload
def create_client(
    url: str, headers: dict[str, str], *, is_async: Literal[False]
) -> SyncFunctionsClient: ...


def create_client(
    url: str, headers: dict[str, str], *, is_async: bool
) -> AsyncFunctionsClient | SyncFunctionsClient:
    if is_async:
        return AsyncFunctionsClient(url, headers)
    else:
        return SyncFunctionsClient(url, headers)
