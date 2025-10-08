from httpx import AsyncClient, AsyncHTTPTransport, Limits

from postgrest import AsyncPostgrestClient

REST_URL = "http://127.0.0.1:3000"


def rest_client():
    return AsyncPostgrestClient(
        base_url=REST_URL,
    )


def rest_client_httpx() -> AsyncPostgrestClient:
    transport = AsyncHTTPTransport(
        retries=4,
        limits=Limits(
            max_connections=1,
            max_keepalive_connections=1,
            keepalive_expiry=None,
        ),
    )
    headers = {"x-user-agent": "my-app/0.0.1"}
    http_client = AsyncClient(transport=transport, headers=headers)
    return AsyncPostgrestClient(
        base_url=REST_URL,
        http_client=http_client,
    )
