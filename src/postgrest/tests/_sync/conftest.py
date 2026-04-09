from typing import Iterable

import pytest
from httpx import Client, HTTPTransport, Limits
from supabase_utils.http.adapters.httpx import HttpxSession

from postgrest import SyncPostgrestClient

REST_URL = "http://127.0.0.1:3000"


def httpx_client() -> Client:
    transport = HTTPTransport(
        retries=4,
        limits=Limits(
            max_connections=1,
            max_keepalive_connections=1,
            keepalive_expiry=None,
        ),
    )
    headers = {"x-user-agent": "my-app/0.0.1"}
    http_client = Client(transport=transport, headers=headers, http2=True, verify=True)
    return http_client


def httpx() -> HttpxSession:
    return HttpxSession(client=httpx_client())


@pytest.fixture(params=[httpx])
def postgrest_client(
    request: pytest.FixtureRequest,
) -> Iterable[SyncPostgrestClient]:
    with SyncPostgrestClient(
        base_url=REST_URL,
        http_session=request.param(),
    ) as client:
        yield client
