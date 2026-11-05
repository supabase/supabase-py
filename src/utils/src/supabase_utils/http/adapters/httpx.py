from types import TracebackType

from httpx import AsyncClient, Auth, Client, TooManyRedirects
from httpx import Request as HttpxRequest
from httpx import Response as HttpxResponse
from yarl import URL

from ..headers import Headers
from ..redirects import CREDENTIAL_HEADERS, keeps_credentials
from ..request import Request, Response


def to_httpx_request(req: Request) -> HttpxRequest:
    return HttpxRequest(
        method=req.method,
        url=str(req.url),
        headers=req.headers.iter_items(),
        content=req.content,
    )


def _request_auth(client: Client | AsyncClient, request: HttpxRequest) -> Auth | None:
    if "Authorization" in request.headers:
        return None
    return client.auth


def to_supabase_response(req: Request, resp: HttpxResponse) -> Response:
    return Response(
        status=resp.status_code,
        content=resp.content,
        headers=Headers.from_mapping(resp.headers),
        request=req,
    )


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
    def __init__(self, client: Client) -> None:
        self.client = client

    def send(self, request: Request) -> Response:
        httpx_request = to_httpx_request(request)
        response = self.client.send(
            httpx_request,
            auth=_request_auth(self.client, httpx_request),
            follow_redirects=False,
        )
        redirects = 0
        while self.client.follow_redirects and (next_request := response.next_request):
            redirects += 1
            response = self.client.send(
                redirect_request(
                    request.url, next_request, redirects, self.client.max_redirects
                ),
                auth=None,
                follow_redirects=False,
            )
        return to_supabase_response(request, response)

    def __enter__(self) -> "HttpxSession":
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.client.close()


class AsyncHttpxSession:
    def __init__(self, client: AsyncClient) -> None:
        self.client = client

    async def send(self, request: Request) -> Response:
        httpx_request = to_httpx_request(request)
        response = await self.client.send(
            httpx_request,
            auth=_request_auth(self.client, httpx_request),
            follow_redirects=False,
        )
        redirects = 0
        while self.client.follow_redirects and (next_request := response.next_request):
            redirects += 1
            response = await self.client.send(
                redirect_request(
                    request.url, next_request, redirects, self.client.max_redirects
                ),
                auth=None,
                follow_redirects=False,
            )
        return to_supabase_response(request, response)

    async def __aenter__(self) -> "AsyncHttpxSession":
        return self

    async def __aexit__(
        self,
        exc_type: type[BaseException] | None,
        exc: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        await self.client.aclose()
