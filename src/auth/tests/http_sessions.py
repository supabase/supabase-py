from collections.abc import Callable

from aiohttp import ClientSession
from httpx import AsyncClient, Client
from supabase_utils.http.adapters.aiohttp import AsyncAiohttpSession
from supabase_utils.http.adapters.httpx import AsyncHttpxSession, HttpxSession
from supabase_utils.http.io import AsyncHttpSession, HttpSession


def async_httpx() -> AsyncHttpxSession:
    return AsyncHttpxSession(client=AsyncClient(http2=True, verify=True))


def async_aiohttp() -> AsyncAiohttpSession:
    return AsyncAiohttpSession(client=ClientSession())


def sync_httpx() -> HttpxSession:
    return HttpxSession(client=Client(http2=True, verify=True))


async_http_sessions: list[Callable[[], AsyncHttpSession]] = [
    async_httpx,
    async_aiohttp,
]
sync_http_sessions: list[Callable[[], HttpSession]] = [sync_httpx]
