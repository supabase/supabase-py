from typing import Optional

from httpx import AsyncClient, Headers, HTTPStatusError, QueryParams, Response
from pydantic import ValidationError
from yarl import URL

from ..exceptions import StorageApiError, VectorBucketErrorMessage
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
        query_params: Optional[QueryParams] = None,
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
            try:
                error = VectorBucketErrorMessage.model_validate_json(response.content)
                raise StorageApiError(
                    message=error.message,
                    code=error.code or "400",
                    status=error.statusCode,
                ) from exc
            except ValidationError as exc:
                raise StorageApiError(
                    message=f"The request failed, but could not parse error message response:'{response.text}'",
                    code="LibraryError",
                    status=response.status_code,
                ) from exc
