from unittest.mock import patch

import pytest
from httpx import (
    AsyncClient,
    AsyncHTTPTransport,
    BasicAuth,
    Headers,
    Limits,
    Request,
    Response,
    Timeout,
)

from postgrest import AsyncPostgrestClient
from postgrest.exceptions import APIError


@pytest.fixture
async def postgrest_client():
    async with AsyncPostgrestClient("https://example.com") as client:
        yield client


class TestConstructor:
    def test_simple(self, postgrest_client: AsyncPostgrestClient):
        assert str(postgrest_client.base_url) == "https://example.com"
        headers = Headers(
            {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Accept-Profile": "public",
                "Content-Profile": "public",
            }
        )
        assert postgrest_client.default_headers.items() >= headers.items()

    async def test_custom_headers(self):
        async with AsyncPostgrestClient(
            "https://example.com", schema="pub", headers={"Custom-Header": "value"}
        ) as client:
            assert str(client.base_url) == "https://example.com"
            headers = Headers(
                {
                    "Accept-Profile": "pub",
                    "Content-Profile": "pub",
                    "Custom-Header": "value",
                }
            )
            assert client.default_headers.items() >= headers.items()


class TestHttpxClientConstructor:
    async def test_custom_httpx_client(self) -> None:
        transport = AsyncHTTPTransport(
            retries=10,
            limits=Limits(
                max_connections=1,
                max_keepalive_connections=1,
                keepalive_expiry=None,
            ),
        )
        headers = {"x-user-agent": "my-app/0.0.1"}
        http_client = AsyncClient(transport=transport, headers=headers)
        async with AsyncPostgrestClient(
            "https://example.com", http_client=http_client
        ) as client:
            assert str(client.base_url) == "https://example.com"
            assert client.executor.session.timeout == Timeout(
                timeout=5.0
            )  # Should be the default 5 since we use custom httpx client
            assert client.executor.session.headers.get("x-user-agent") == "my-app/0.0.1"
            assert isinstance(client.executor.session, AsyncClient)


class TestAuth:
    def test_auth_token(self, postgrest_client: AsyncPostgrestClient):
        postgrest_client.set_auth("s3cr3t")
        assert postgrest_client.default_headers["Authorization"] == "Bearer s3cr3t"

    def test_auth_basic(self, postgrest_client: AsyncPostgrestClient):
        postgrest_client.set_auth_with_password(username="admin", password="s3cr3t")

        assert (
            postgrest_client.default_headers["Authorization"]
            == "Basic YWRtaW46czNjcjN0"
        )


def test_schema(postgrest_client: AsyncPostgrestClient):
    client = postgrest_client.schema("private")
    subheaders = {
        "accept-profile": "private",
        "content-profile": "private",
    }

    assert subheaders.items() < client.default_headers.items()
