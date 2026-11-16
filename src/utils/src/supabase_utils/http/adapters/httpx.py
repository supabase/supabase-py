from collections.abc import (
    AsyncGenerator,
    AsyncIterable,
    AsyncIterator,
    Generator,
    Iterable,
    Iterator,
)
from contextlib import asynccontextmanager, contextmanager
from types import TracebackType

from httpx import (
    AsyncClient,
    Auth,
    Client,
    RequestError,
    Timeout,
    TimeoutException,
    TooManyRedirects,
)
from httpx import Request as HttpxRequest
from httpx import Response as HttpxResponse
from yarl import URL

from ..body import async_chunks
from ..errors import RequestTimeoutError, SupabaseTransportError
from ..headers import Headers
from ..redirects import CREDENTIAL_HEADERS, keeps_credentials
from ..request import AsyncStreamedResponse, Request, Response, StreamedResponse
from ..retry import _is_replayable

_BODY_KEEPING_REDIRECTS = frozenset({307, 308})


def to_httpx_request(req: Request) -> HttpxRequest:
    content = req.content
    if content is not None and not isinstance(content, (bytes, Iterable)):
        raise TypeError("HttpxSession cannot send an async iterable body")
    return _httpx_request(req, content)


class _AsyncBody:
    """A body httpx can iterate again, as it does when it follows a redirect
    that keeps the body, with every iteration reading `content` anew."""

    def __init__(self, content: Iterable[bytes] | AsyncIterable[bytes]) -> None:
        self.content = content

    def __aiter__(self) -> AsyncIterator[bytes]:
        return async_chunks(self.content)


def to_async_httpx_request(req: Request) -> HttpxRequest:
    content = req.content
    if content is not None and not isinstance(content, bytes):
        content = _AsyncBody(content)
    return _httpx_request(req, content)


def _follows(request: Request, response: HttpxResponse) -> bool:
    """Whether to follow the redirect `response` answers `request` with. A
    redirect that sends the body again is not followed for a body that can be
    sent only once, so the caller gets the redirect response instead."""
    return response.status_code not in _BODY_KEEPING_REDIRECTS or _is_replayable(
        request
    )


def _httpx_request(
    req: Request,
    content: bytes | Iterable[bytes] | AsyncIterable[bytes] | None,
) -> HttpxRequest:
    return HttpxRequest(
        method=req.method,
        url=str(req.url),
        headers=req.headers.iter_items(),
        content=content,
        extensions={}
        if req.timeout is None
        else {"timeout": Timeout(req.timeout).as_dict()},
    )


def _request_auth(client: Client | AsyncClient, request: HttpxRequest) -> Auth | None:
    if "Authorization" in request.headers:
        return Auth()
    return client.auth


def to_supabase_response(req: Request, resp: HttpxResponse) -> Response:
    return Response(
        status=resp.status_code,
        content=resp.content,
        headers=Headers.from_mapping(resp.headers),
        request=req,
    )


def _transport_error(request: Request, error: RequestError) -> SupabaseTransportError:
    if isinstance(error, TimeoutException):
        return RequestTimeoutError(request)
    return SupabaseTransportError(request)


def _sync_body(request: Request, response: HttpxResponse) -> Iterator[bytes]:
    try:
        yield from response.iter_bytes()
    except RequestError as error:
        raise _transport_error(request, error) from error


async def _async_body(
    request: Request, response: HttpxResponse
) -> AsyncIterator[bytes]:
    try:
        async for chunk in response.aiter_bytes():
            yield chunk
    except RequestError as error:
        raise _transport_error(request, error) from error


def redirect_request(
    origin: URL, request: HttpxRequest, redirects: int, max_redirects: int
) -> HttpxRequest:
    if redirects > max_redirects:
        raise TooManyRedirects("Exceeded maximum allowed redirects.", request=request)
    if not keeps_credentials(origin, URL(str(request.url))):
        for name in CREDENTIAL_HEADERS:
            request.headers.pop(name, None)
    return request


class HttpxSession:
    """Sends the requests with an httpx client.

    Leaving the session closes `client` unless `owns_client` is false, for a
    client that its owner closes.
    """

    def __init__(self, client: Client, *, owns_client: bool = True) -> None:
        self.client = client
        self.owns_client = owns_client

    def send(self, request: Request) -> Response:
        try:
            return to_supabase_response(request, self._send(request, stream=False))
        except RequestError as error:
            raise _transport_error(request, error) from error

    @contextmanager
    def stream(self, request: Request) -> Generator[StreamedResponse]:
        try:
            response = self._send(request, stream=True)
        except RequestError as error:
            raise _transport_error(request, error) from error
        try:
            yield StreamedResponse(
                headers=Headers.from_mapping(response.headers),
                status=response.status_code,
                request=request,
                body=_sync_body(request, response),
            )
        finally:
            response.close()

    def _send(self, request: Request, *, stream: bool) -> HttpxResponse:
        httpx_request = to_httpx_request(request)
        response = self.client.send(
            httpx_request,
            auth=_request_auth(self.client, httpx_request),
            follow_redirects=False,
            stream=stream,
        )
        redirects = 0
        while (
            self.client.follow_redirects
            and (next_request := response.next_request)
            and _follows(request, response)
        ):
            redirects += 1
            response.close()
            response = self.client.send(
                redirect_request(
                    request.url, next_request, redirects, self.client.max_redirects
                ),
                auth=None,
                follow_redirects=False,
                stream=stream,
            )
        return response

    def __enter__(self) -> "HttpxSession":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if self.owns_client:
            self.client.close()


class AsyncHttpxSession:
    """Sends the requests with an httpx client.

    Leaving the session closes `client` unless `owns_client` is false, for a
    client that its owner closes.
    """

    def __init__(self, client: AsyncClient, *, owns_client: bool = True) -> None:
        self.client = client
        self.owns_client = owns_client

    async def send(self, request: Request) -> Response:
        try:
            response = await self._send(request, stream=False)
        except RequestError as error:
            raise _transport_error(request, error) from error
        return to_supabase_response(request, response)

    @asynccontextmanager
    async def stream(self, request: Request) -> AsyncGenerator[AsyncStreamedResponse]:
        try:
            response = await self._send(request, stream=True)
        except RequestError as error:
            raise _transport_error(request, error) from error
        try:
            yield AsyncStreamedResponse(
                headers=Headers.from_mapping(response.headers),
                status=response.status_code,
                request=request,
                body=_async_body(request, response),
            )
        finally:
            await response.aclose()

    async def _send(self, request: Request, *, stream: bool) -> HttpxResponse:
        httpx_request = to_async_httpx_request(request)
        response = await self.client.send(
            httpx_request,
            auth=_request_auth(self.client, httpx_request),
            follow_redirects=False,
            stream=stream,
        )
        redirects = 0
        while (
            self.client.follow_redirects
            and (next_request := response.next_request)
            and _follows(request, response)
        ):
            redirects += 1
            await response.aclose()
            response = await self.client.send(
                redirect_request(
                    request.url, next_request, redirects, self.client.max_redirects
                ),
                auth=None,
                follow_redirects=False,
                stream=stream,
            )
        return response

    async def __aenter__(self) -> "AsyncHttpxSession":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        if self.owns_client:
            await self.client.aclose()
