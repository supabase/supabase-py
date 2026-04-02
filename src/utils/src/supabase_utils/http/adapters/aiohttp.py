from types import TracebackType

from aiohttp import ClientResponse as AioResponse
from aiohttp import ClientSession

from ..headers import Headers
from ..request import Request, Response


async def to_supabase_response(req: Request, resp: AioResponse) -> Response:
    return Response(
        status=resp.status,
        content=await resp.read(),
        headers=Headers.from_mapping(resp.headers),
        request=req,
    )


class AsyncAiohttpSession:
    def __init__(self, client: ClientSession) -> None:
        self.client = client

    async def send(self, request: Request) -> Response:
        response = await self.client.request(
            method=request.method,
            url=str(request.url),
            data=request.content,
            headers=dict(request.headers),
        )
        return await to_supabase_response(request, response)

    async def __aenter__(self) -> "AsyncAiohttpSession":
        return self

    async def __aexit__(
        self,
        exc_type: type[Exception] | None,
        exc: Exception | None,
        tb: TracebackType | None,
    ) -> None:
        await self.client.__aexit__(exc_type, exc, tb)
