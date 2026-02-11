from __future__ import annotations

from typing import Any, Literal

from httpx import AsyncClient, HTTPStatusError, QueryParams, Response
from pydantic import BaseModel
from typing_extensions import Self

from ..constants import API_VERSION_HEADER_NAME, API_VERSIONS_2024_01_01_NAME
from ..helpers import handle_exception, model_dump


class AsyncGoTrueBaseAPI:
    def __init__(
        self,
        *,
        url: str,
        headers: dict[str, str],
        http_client: AsyncClient | None,
        verify: bool = True,
        proxy: str | None = None,
    ) -> None:
        self._url = url
        self._headers = headers
        self._http_client = http_client or AsyncClient(
            verify=bool(verify),
            proxy=proxy,
            follow_redirects=True,
            http2=True,
        )

    async def __aenter__(self) -> Self:
        return self

    async def __aexit__(self, exc_t, exc_v, exc_tb) -> None:
        await self.close()

    async def close(self) -> None:
        await self._http_client.aclose()

    async def _request(
        self,
        method: Literal["GET", "OPTIONS", "HEAD", "POST", "PUT", "PATCH", "DELETE"],
        path: str,
        *,
        jwt: str | None = None,
        redirect_to: str | None = None,
        headers: dict[str, str] | None = None,
        query: QueryParams | None = None,
        body: Any | None = None,
        no_resolve_json: bool = False,
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
            response = await self._http_client.request(
                method,
                url,
                headers=headers,
                params=query,
                json=model_dump(body) if isinstance(body, BaseModel) else body,
            )

            response.raise_for_status()
            return response
        except (HTTPStatusError, RuntimeError) as e:
            raise handle_exception(e)  # noqa
