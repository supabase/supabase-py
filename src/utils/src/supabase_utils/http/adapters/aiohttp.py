from collections.abc import AsyncGenerator, AsyncIterator
from contextlib import asynccontextmanager
from types import TracebackType

from aiohttp import (
    ClientError,
    ClientHandlerType,
    ClientMiddlewareType,
    ClientRequest,
    ClientSession,
    ClientTimeout,
)
from aiohttp import ClientResponse as AioResponse
from yarl import URL

from ..body import CHUNK_SIZE, async_chunks
from ..errors import RequestTimeoutError, SupabaseTransportError
from ..headers import Headers
from ..redirects import CREDENTIAL_HEADERS, keeps_credentials
from ..request import AsyncStreamedResponse, Request, Response


async def to_supabase_response(req: Request, resp: AioResponse) -> Response:
    return Response(
        status=resp.status,
        content=await resp.read(),
        headers=Headers.from_mapping(resp.headers),
        request=req,
    )


def _transport_error(
    request: Request, error: TimeoutError | ClientError
) -> SupabaseTransportError:
    if isinstance(error, TimeoutError):
        return RequestTimeoutError(request)
    return SupabaseTransportError(request)


async def _body(request: Request, response: AioResponse) -> AsyncIterator[bytes]:
    try:
        async for chunk in response.content.iter_chunked(CHUNK_SIZE):
            yield chunk
    except (TimeoutError, ClientError) as error:
        raise _transport_error(request, error) from error


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
    """Sends the requests with an aiohttp client session.

    Leaving the session closes `client` unless `owns_client` is false, for a
    client that its owner closes.
    """

    def __init__(self, client: ClientSession, *, owns_client: bool = True) -> None:
        self.client = client
        self.owns_client = owns_client

    def _timeout(self, request_timeout: float | None) -> ClientTimeout:
        session_timeout = self.client.timeout
        if request_timeout is None:
            return session_timeout
        return ClientTimeout(
            total=session_timeout.total,
            connect=request_timeout,
            sock_connect=request_timeout,
            sock_read=request_timeout,
            ceil_threshold=session_timeout.ceil_threshold,
        )

    async def send(self, request: Request) -> Response:
        try:
            response = await self._request(request)
            return await to_supabase_response(request, response)
        except (TimeoutError, ClientError) as error:
            raise _transport_error(request, error) from error

    @asynccontextmanager
    async def stream(self, request: Request) -> AsyncGenerator[AsyncStreamedResponse]:
        try:
            response = await self._request(request)
        except (TimeoutError, ClientError) as error:
            raise _transport_error(request, error) from error
        try:
            yield AsyncStreamedResponse(
                headers=Headers.from_mapping(response.headers),
                status=response.status,
                request=request,
                body=_body(request, response),
            )
        finally:
            response.release()

    async def _request(self, request: Request) -> AioResponse:
        content = request.content
        if content is not None and not isinstance(content, bytes):
            content = async_chunks(content)
        return await self.client.request(
            method=request.method,
            url=str(request.url),
            data=content,
            headers=dict(request.headers),
            timeout=self._timeout(request.timeout),
            # The packages read the status themselves, so an error status
            # must come back as a response even on a session that raises.
            raise_for_status=False,
            middlewares=(
                # Per request middlewares replace the session ones, so keep those.
                *self.client._middlewares,
                strip_cross_origin_credentials(request.url),
            ),
        )

    async def __aenter__(self) -> "AsyncAiohttpSession":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if self.owns_client:
            await self.client.__aexit__(exc_type, exc, tb)
