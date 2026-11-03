from httpx import AsyncClient, Headers, HTTPStatusError, QueryParams, Response
from yarl import URL

from ..exceptions import _parse_storage_api_error
from ..types import JSON, RequestMethod


class AsyncRequestBuilder:
    def __init__(self, session: AsyncClient, base_url: URL, headers: Headers) -> None:
        self._session = session
        self._base_url = base_url
        self.headers = headers

    async def send(
        self,
        http_method: RequestMethod,
        path: list[str],
        body: JSON = None,
        query_params: QueryParams | None = None,
    ) -> Response:
        response = await self._session.request(
            method=http_method,
            json=body,
            url=str(self._base_url.joinpath(*path)),
            headers=self.headers,
            params=query_params or QueryParams(),
        )
        try:
            response.raise_for_status()
            return response
        except HTTPStatusError as exc:
            raise _parse_storage_api_error(response) from exc
