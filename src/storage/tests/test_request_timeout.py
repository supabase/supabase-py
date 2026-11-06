import pytest
from httpx import AsyncClient, Client, MockTransport, Request, Response
from supabase_utils.http.adapters.httpx import AsyncHttpxSession, HttpxSession

from storage3 import AsyncStorageClient, SyncStorageClient

from .utils import STORAGE_URL


def recording_transport(seen: list[Request]) -> MockTransport:
    def handler(request: Request) -> Response:
        seen.append(request)
        return Response(200, json=[])

    return MockTransport(handler)


def read_timeouts(seen: list[Request]) -> list[float | None]:
    return [request.extensions["timeout"]["read"] for request in seen]


def test_sync_client_uses_request_timeout() -> None:
    seen: list[Request] = []
    client = SyncStorageClient(
        STORAGE_URL,
        {},
        http_session=HttpxSession(Client(transport=recording_transport(seen))),
        request_timeout=40,
    )
    client.list_buckets()
    client.from_("photos").list()
    assert read_timeouts(seen) == [40, 40]


async def test_async_client_uses_request_timeout() -> None:
    seen: list[Request] = []
    client = AsyncStorageClient(
        STORAGE_URL,
        {},
        http_session=AsyncHttpxSession(
            AsyncClient(transport=recording_transport(seen))
        ),
        request_timeout=40,
    )
    await client.list_buckets()
    await client.from_("photos").list()
    assert read_timeouts(seen) == [40, 40]


def test_invalid_request_timeout_is_rejected() -> None:
    with pytest.raises(ValueError, match="positive number of seconds"):
        SyncStorageClient(
            STORAGE_URL,
            {},
            http_session=HttpxSession(Client()),
            request_timeout=-1,
        )
