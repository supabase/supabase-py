import platform
from typing import Any, Literal
from warnings import warn

from httpx import URL as HttpxURL
from httpx import Client, Headers, HTTPError, QueryParams, Request, Response
from yarl import URL

from ..errors import FunctionsHttpError, FunctionsRelayError, _error_message_from
from ..utils import (
    FunctionRegion,
    is_http_url,
    is_valid_str_arg,
)
from ..version import __version__

HTTPMethod = Literal["GET", "OPTIONS", "HEAD", "POST", "PUT", "PATCH", "DELETE"]


def _port_or_default(url: HttpxURL) -> int | None:
    if url.port is not None:
        return url.port
    return {"http": 80, "https": 443}.get(url.scheme)


def _keeps_credentials(source: HttpxURL, target: HttpxURL) -> bool:
    if source.host != target.host:
        return False
    if source.scheme == target.scheme:
        return _port_or_default(source) == _port_or_default(target)
    return (
        source.scheme == "http"
        and _port_or_default(source) == 80
        and target.scheme == "https"
        and _port_or_default(target) == 443
    )


class _RedirectGuardClient(Client):
    """Drops the ``apiKey`` header on redirects that leave the origin.

    httpx only strips ``Authorization`` on such redirects, so the project key
    (the ``service_role`` key in server side usage) would otherwise be sent to
    whatever host an invoked edge function redirects to.
    """

    def _redirect_headers(
        self, request: Request, url: HttpxURL, method: str
    ) -> Headers:
        headers = super()._redirect_headers(request, url, method)
        if not _keeps_credentials(request.url, url):
            headers.pop("apiKey", None)
        return headers


class SyncFunctionsClient:
    def __init__(
        self,
        url: str,
        headers: dict,
        timeout: int | None = None,
        verify: bool | None = None,
        proxy: str | None = None,
        http_client: Client | None = None,
    ) -> None:
        if not is_http_url(url):
            raise ValueError("url must be a valid HTTP URL string")
        self.url = URL(url)
        self.headers = Headers(
            {
                "X-Client-Info": (
                    f"supabase-py/supabase_functions v{__version__}"
                    f"; platform={platform.system()}"
                    f"; platform-version={platform.release()}"
                    f"; runtime=python"
                    f"; runtime-version={platform.python_version()}"
                )
            }
        )
        self.headers.update(headers)

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

        self.verify = bool(verify) if verify is not None else True
        self.timeout = int(abs(timeout)) if timeout is not None else 60
        self._client = http_client or _RedirectGuardClient(
            verify=self.verify,
            timeout=self.timeout,
            proxy=proxy,
            follow_redirects=True,
            http2=True,
        )

    def _request(
        self,
        method: HTTPMethod,
        path: list[str],
        headers: Headers,
        json: dict[Any, Any] | str | bytes | None = None,
        params: QueryParams | None = None,
    ) -> Response:
        url = self.url.joinpath(*path)
        response = (
            self._client.request(
                method, str(url), content=json, headers=headers, params=params
            )
            if isinstance(json, (str, bytes))
            else self._client.request(
                method, str(url), json=json, headers=headers, params=params
            )
        )
        # Relay failures set this header even on non-2xx responses.
        if response.headers.get("x-relay-error") == "true":
            raise FunctionsRelayError(response.text, response.status_code)
        try:
            response.raise_for_status()
        except HTTPError as exc:
            status_code = None
            if hasattr(response, "status_code"):
                status_code = response.status_code

            raise FunctionsHttpError(
                _error_message_from(response)
                or f"An error occurred while requesting your edge function at {exc.request.url!r}.",
                status_code,
            ) from exc

        return response

    def set_auth(self, token: str) -> None:
        """Updates the authorization header

        Parameters
        ----------
        token : str
            the new jwt token sent in the authorization header
        """

        self.headers["Authorization"] = f"Bearer {token}"

    def invoke(
        self, function_name: str, invoke_options: dict | None = None
    ) -> dict | bytes:
        """Invokes a function

        Parameters
        ----------
        function_name : the name of the function to invoke. It may carry a query
            string, as in `hello?name=bob`. A `#fragment` is dropped.
        invoke_options : object with the following properties
            `headers`: object representing the headers to send with the request
            `body`: the body of the request
            `method`: the HTTP method to invoke the function with. The default is `POST`
            `responseType`: how the response should be parsed. The default is `json`
        """
        if not is_valid_str_arg(function_name):
            raise ValueError("function_name must a valid string value.")
        # Like a URL, a name such as "hello?name=bob" carries query params and
        # the fragment is never sent.
        path, _, query = function_name.split("#", 1)[0].partition("?")
        if not is_valid_str_arg(path):
            raise ValueError("function_name must a valid string value.")
        headers = Headers(self.headers)
        params = QueryParams(query)
        body = None
        method: HTTPMethod = "POST"
        response_type = "text/plain"

        if invoke_options is not None:
            headers.update(invoke_options.get("headers", {}))
            method = invoke_options.get("method", "POST")
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
            if headers.get("content-type", None) is None:
                if isinstance(body, str):
                    headers["Content-Type"] = "text/plain"
                elif isinstance(body, dict):
                    headers["Content-Type"] = "application/json"
                elif isinstance(body, bytes):
                    headers["Content-Type"] = "application/octet-stream"

        response = self._request(
            method, [path], headers=headers, json=body, params=params
        )
        if response_type == "json":
            data = response.json()
        else:
            data = response.content
        return data
