from typing import Any, Dict, Literal, Optional, Union
from warnings import warn

from httpx import AsyncClient, HTTPError, Response

from ..errors import FunctionsHttpError, FunctionsRelayError
from ..utils import (
    FunctionRegion,
    is_http_url,
    is_valid_str_arg,
)
from ..version import __version__


class AsyncFunctionsClient:
    def __init__(
        self,
        url: str,
        headers: Dict,
        timeout: Optional[int] = None,
        verify: Optional[bool] = None,
        proxy: Optional[str] = None,
        http_client: Optional[AsyncClient] = None,
    ):
        if not is_http_url(url):
            raise ValueError("url must be a valid HTTP URL string")
        self.url = url
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

        self.verify = bool(verify) if verify is not None else True
        self.timeout = int(abs(timeout)) if timeout is not None else 60

        if http_client is not None:
            http_client.base_url = self.url
            http_client.headers.update({**self.headers})
            self._client = http_client
        else:
            self._client = AsyncClient(
                base_url=self.url,
                headers=self.headers,
                verify=self.verify,
                timeout=self.timeout,
                proxy=proxy,
                follow_redirects=True,
                http2=True,
            )

    async def _request(
        self,
        method: Literal["GET", "OPTIONS", "HEAD", "POST", "PUT", "PATCH", "DELETE"],
        url: str,
        headers: Optional[Dict[str, str]] = None,
        json: Optional[Dict[Any, Any]] = None,
    ) -> Response:
        user_data = {"data": json} if isinstance(json, str) else {"json": json}
        response = await self._client.request(method, url, **user_data, headers=headers)

        try:
            response.raise_for_status()
        except HTTPError as exc:
            status_code = None
            if hasattr(response, "status_code"):
                status_code = response.status_code

            raise FunctionsHttpError(
                response.json().get("error")
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

    async def invoke(
        self, function_name: str, invoke_options: Optional[Dict] = None
    ) -> Union[Dict, bytes]:
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
        body = None
        response_type = "text/plain"
        if invoke_options is not None:
            headers.update(invoke_options.get("headers", {}))
            response_type = invoke_options.get("responseType", "text/plain")

            region = invoke_options.get("region")
            if region:
                if not isinstance(region, FunctionRegion):
                    warn(f"Use FunctionRegion({region})")
                    region = FunctionRegion(region)

                if region.value != "any":
                    headers["x-region"] = region.value

            body = invoke_options.get("body")
            if isinstance(body, str):
                headers["Content-Type"] = "text/plain"
            elif isinstance(body, dict):
                headers["Content-Type"] = "application/json"

        response = await self._request(
            "POST", f"{self.url}/{function_name}", headers=headers, json=body
        )
        is_relay_error = response.headers.get("x-relay-header")

        if is_relay_error and is_relay_error == "true":
            raise FunctionsRelayError(response.json().get("error"))

        if response_type == "json":
            data = response.json()
        else:
            data = response.content
        return data
