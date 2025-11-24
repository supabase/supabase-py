from typing import Optional

from httpx import AsyncClient, Headers, QueryParams, Response
from yarl import URL

from ..types import JSON, RequestMethod


class RequestBuilder:
    def __init__(self, session: AsyncClient, base_url: URL, headers: Headers) -> None:
        self._session = session
        self._base_url = base_url
        self.headers = headers

    async def send(
        self,
        http_method: RequestMethod,
        path: list[str],
        body: JSON = None,
        query_params: Optional[QueryParams] = None,
    ) -> Response:
        return await self._session.request(
            method=http_method,
            json=body,
            url=str(self._base_url.joinpath(*path)),
            headers=self.headers,
            params=query_params or QueryParams(),
        )
