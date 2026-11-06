from types import TracebackType

from aiohttp import (
    ClientHandlerType,
    ClientMiddlewareType,
    ClientRequest,
    ClientSession,
    ClientTimeout,
)
from aiohttp import ClientResponse as AioResponse
from yarl import URL

from ..errors import RequestTimeoutError
from ..headers import Headers
from ..redirects import CREDENTIAL_HEADERS, keeps_credentials
from ..request import Request, Response


async def to_supabase_response(req: Request, resp: AioResponse) -> Response:
    return Response(
        status=resp.status,
        content=await resp.read(),
        headers=Headers.from_mapping(resp.headers),
        request=req,
    )


def strip_cross_origin_credentials(origin: URL) -> ClientMiddlewareType:
    left_origin = False

    async def middleware(
        request: ClientRequest, handler: ClientHandlerType
    ) -> AioResponse:
        nonlocal left_origin
        left_origin = left_origin or not keeps_credentials(origin, request.url)
        if left_origin:
            for name in CREDENTIAL_HEADERS:
                request.headers.popall(name, None)
        return await handler(request)

    return middleware


class AsyncAiohttpSession:
    def __init__(self, client: ClientSession) -> None:
        self.client = client

    async def send(self, request: Request) -> Response:
        try:
            response = await self.client.request(
                method=request.method,
                url=str(request.url),
                data=request.content,
                headers=dict(request.headers),
                timeout=self.client.timeout
                if request.timeout is None
                else ClientTimeout(
                    connect=request.timeout,
                    sock_connect=request.timeout,
                    sock_read=request.timeout,
                ),
                middlewares=(
                    # Per request middlewares replace the session ones, so keep those.
                    *self.client._middlewares,
                    strip_cross_origin_credentials(request.url),
                ),
            )
            return await to_supabase_response(request, response)
        except TimeoutError as error:
            raise RequestTimeoutError(request) from error

    async def __aenter__(self) -> "AsyncAiohttpSession":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.client.__aexit__(exc_type, exc, tb)
