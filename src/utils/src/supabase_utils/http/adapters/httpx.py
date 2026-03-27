from types import TracebackType

from httpx import AsyncClient, Client
from httpx import Request as HttpxRequest
from httpx import Response as HttpxResponse

from ..headers import Headers
from ..request import Request, Response


def to_httpx_request(req: Request) -> HttpxRequest:
    return HttpxRequest(
        method=req.method,
        url=str(req.url),
        headers=req.headers.iter_items(),
        content=req.content,
    )


def to_supabase_response(req: Request, resp: HttpxResponse) -> Response:
    return Response(
        status=resp.status_code,
        content=resp.content,
        headers=Headers.from_mapping(resp.headers),
        request=req,
    )


class HttpxSession:
    def __init__(self, client: Client) -> None:
        self.client = client

    def send(self, request: Request) -> Response:
        response = self.client.send(to_httpx_request(request))
        return to_supabase_response(request, response)

    def __enter__(self) -> "HttpxSession":
        return self

    def __exit__(
        self,
        exc_type: type[Exception] | None,
        exc: Exception | None,
        tb: TracebackType | None,
    ) -> None:
        self.client.close()


class AsyncHttpxSession:
    def __init__(self, client: AsyncClient) -> None:
        self.client = client

    async def send(self, request: Request) -> Response:
        response = await self.client.send(to_httpx_request(request))
        return to_supabase_response(request, response)

    async def __aenter__(self) -> "AsyncHttpxSession":
        return self

    async def __aexit__(
        self,
        exc_type: type[Exception] | None,
        exc: Exception | None,
        tb: TracebackType | None,
    ) -> None:
        await self.client.aclose()
