import pytest
from httpx import (
    Client,
    Headers,
    HTTPTransport,
    Limits,
    Timeout,
)

from postgrest import SyncPostgrestClient


@pytest.fixture
def postgrest_client():
    with SyncPostgrestClient("https://example.com") as client:
        yield client


class TestConstructor:
    def test_simple(self, postgrest_client: SyncPostgrestClient):
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

    def test_custom_headers(self):
        with SyncPostgrestClient(
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
    def test_custom_httpx_client(self) -> None:
        transport = HTTPTransport(
            retries=10,
            limits=Limits(
                max_connections=1,
                max_keepalive_connections=1,
                keepalive_expiry=None,
            ),
        )
        headers = {"x-user-agent": "my-app/0.0.1"}
        http_client = Client(transport=transport, headers=headers)
        with SyncPostgrestClient(
            "https://example.com", http_client=http_client
        ) as client:
            assert str(client.base_url) == "https://example.com"
            assert client.executor.session.timeout == Timeout(
                timeout=5.0
            )  # Should be the default 5 since we use custom httpx client
            assert client.executor.session.headers.get("x-user-agent") == "my-app/0.0.1"
            assert isinstance(client.executor.session, Client)


class TestAuth:
    def test_auth_token(self, postgrest_client: SyncPostgrestClient):
        postgrest_client.set_auth("s3cr3t")
        assert postgrest_client.default_headers["Authorization"] == "Bearer s3cr3t"

    def test_auth_basic(self, postgrest_client: SyncPostgrestClient):
        postgrest_client.set_auth_with_password(username="admin", password="s3cr3t")

        assert (
            postgrest_client.default_headers["Authorization"]
            == "Basic YWRtaW46czNjcjN0"
        )


def test_schema(postgrest_client: SyncPostgrestClient):
    client = postgrest_client.schema("private")
    subheaders = {
        "accept-profile": "private",
        "content-profile": "private",
    }

    assert subheaders.items() < client.default_headers.items()
