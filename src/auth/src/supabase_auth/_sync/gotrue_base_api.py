from __future__ import annotations

from typing import Any, Literal, Self

from httpx import Client, HTTPStatusError, QueryParams, RequestError, Response
from pydantic import BaseModel

from ..constants import API_VERSION_HEADER_NAME, API_VERSIONS_2024_01_01_NAME
from ..helpers import handle_exception


class SyncGoTrueBaseAPI:
    def __init__(
        self,
        *,
        url: str,
        headers: dict[str, str],
        http_client: Client | None,
        verify: bool = True,
        proxy: str | None = None,
    ) -> None:
        self._url = url.rstrip("/")
        # Copy: callers pass a dict they keep mutating, and GoTrueClient hands
        # its own `_headers` to the admin API. Sharing the object means a later
        # `_headers["Authorization"] = <user token>` silently downgrades every
        # other holder of that dict.
        self._headers = dict(headers)
        self._http_client = http_client or Client(
            verify=bool(verify),
            proxy=proxy,
            follow_redirects=True,
            http2=True,
        )

    def __enter__(self) -> Self:
        return self

    def __exit__(self, exc_t, exc_v, exc_tb) -> None:
        self.close()

    def close(self) -> None:
        self._http_client.close()

    def _request(
        self,
        method: Literal["GET", "OPTIONS", "HEAD", "POST", "PUT", "PATCH", "DELETE"],
        path: str,
        *,
        jwt: str | None = None,
        redirect_to: str | None = None,
        headers: dict[str, str] | None = None,
        query: QueryParams | None = None,
        body: Any | None = None,
    ) -> Response:
        url = f"{self._url}/{path}"
        headers = {**self._headers, **(headers or {})}
        if API_VERSION_HEADER_NAME not in headers:
            headers[API_VERSION_HEADER_NAME] = API_VERSIONS_2024_01_01_NAME
        if "Content-Type" not in headers:
            headers["Content-Type"] = "application/json;charset=UTF-8"
        if jwt:
            headers["Authorization"] = f"Bearer {jwt}"
        query = query or QueryParams()
        if redirect_to:
            query = query.set("redirect_to", redirect_to)
        try:
            response = self._http_client.request(
                method,
                url,
                headers=headers,
                params=query,
                json=body.model_dump() if isinstance(body, BaseModel) else body,
            )

            response.raise_for_status()
            return response
        except (HTTPStatusError, RequestError, RuntimeError) as e:
            raise handle_exception(e) from e
