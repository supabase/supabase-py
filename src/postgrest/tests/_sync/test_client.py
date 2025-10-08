from unittest.mock import patch

import pytest
from httpx import (
    BasicAuth,
    Client,
    Headers,
    HTTPTransport,
    Limits,
    Request,
    Response,
    Timeout,
)

from postgrest import SyncPostgrestClient
from postgrest.exceptions import APIError


@pytest.fixture
def postgrest_client():
    with SyncPostgrestClient("https://example.com") as client:
        yield client


class TestConstructor:
    def test_simple(self, postgrest_client: SyncPostgrestClient):
        session = postgrest_client.session

        assert session.base_url == "https://example.com"
        headers = Headers(
            {
                "Accept": "application/json",
                "Content-Type": "application/json",
                "Accept-Profile": "public",
                "Content-Profile": "public",
            }
        )
        assert session.headers.items() >= headers.items()

    def test_custom_headers(self):
        with SyncPostgrestClient(
            "https://example.com", schema="pub", headers={"Custom-Header": "value"}
        ) as client:
            session = client.session

            assert session.base_url == "https://example.com"
            headers = Headers(
                {
                    "Accept-Profile": "pub",
                    "Content-Profile": "pub",
                    "Custom-Header": "value",
                }
            )
            assert session.headers.items() >= headers.items()


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
            "https://example.com", http_client=http_client, timeout=20.0
        ) as client:
            assert str(client.base_url) == "https://example.com"
            assert client.session.timeout == Timeout(
                timeout=5.0
            )  # Should be the default 5 since we use custom httpx client
            assert client.session.headers.get("x-user-agent") == "my-app/0.0.1"
            assert isinstance(client.session, Client)


class TestAuth:
    def test_auth_token(self, postgrest_client: SyncPostgrestClient):
        postgrest_client.auth("s3cr3t")
        assert postgrest_client.headers["Authorization"] == "Bearer s3cr3t"

    def test_auth_basic(self, postgrest_client: SyncPostgrestClient):
        postgrest_client.auth(None, username="admin", password="s3cr3t")

        assert isinstance(postgrest_client.basic_auth, BasicAuth)
        assert (
            postgrest_client.basic_auth._auth_header
            == BasicAuth("admin", "s3cr3t")._auth_header
        )


def test_schema(postgrest_client: SyncPostgrestClient):
    client = postgrest_client.schema("private")
    subheaders = {
        "accept-profile": "private",
        "content-profile": "private",
    }

    assert subheaders.items() < client.headers.items()


def test_params_purged_after_execute(postgrest_client: SyncPostgrestClient):
    assert len(postgrest_client.session.params) == 0
    with pytest.raises(APIError):
        postgrest_client.from_("test").select("a", "b").eq("c", "d").execute()
    assert len(postgrest_client.session.params) == 0


def test_response_status_code_outside_ok(postgrest_client: SyncPostgrestClient):
    with patch(
        "postgrest._sync.request_builder.SyncSelectRequestBuilder.execute",
        side_effect=APIError(
            {
                "message": "mock error",
                "code": "400",
                "hint": "mock",
                "details": "mock",
                "errors": [{"code": 400}],
            }
        ),
    ):
        with pytest.raises(APIError) as exc_info:
            (
                postgrest_client.from_("test").select("a", "b").eq("c", "d").execute()
            )  # gives status_code = 400
        exc_response = exc_info.value.json()
        assert not exc_response.get("success")
        assert isinstance(exc_response.get("errors"), list)
        assert (
            isinstance(exc_response["errors"][0], dict)
            and "code" in exc_response["errors"][0]
        )
        assert exc_response["errors"][0].get("code") == 400


def test_response_maybe_single(postgrest_client: SyncPostgrestClient):
    with patch(
        "postgrest._sync.request_builder.SyncSingleRequestBuilder.execute",
        side_effect=APIError(
            {"message": "mock error", "code": "400", "hint": "mock", "details": "mock"}
        ),
    ):
        client = (
            postgrest_client.from_("test").select("a", "b").eq("c", "d").maybe_single()
        )
        assert "Accept" in client.request.headers
        assert (
            client.request.headers.get("Accept") == "application/vnd.pgrst.object+json"
        )
        with pytest.raises(APIError) as exc_info:
            client.execute()
        assert isinstance(exc_info, pytest.ExceptionInfo)
        exc_response = exc_info.value.json()
        assert isinstance(exc_response.get("message"), str)
        assert "code" in exc_response and int(exc_response["code"]) == 204


# https://github.com/supabase/postgrest-py/issues/595


def test_response_client_invalid_response_but_valid_json(
    postgrest_client: SyncPostgrestClient,
):
    with patch(
        "httpx._client.Client.request",
        return_value=Response(
            status_code=502,
            text='"gateway error: Error: Network connection lost."',  # quotes makes this text a valid non-dict JSON object
            request=Request(method="GET", url="http://example.com"),
        ),
    ):
        client = postgrest_client.from_("test").select("a", "b").eq("c", "d").single()
        assert "Accept" in client.request.headers
        assert (
            client.request.headers.get("Accept") == "application/vnd.pgrst.object+json"
        )
        with pytest.raises(APIError) as exc_info:
            client.execute()
        assert isinstance(exc_info, pytest.ExceptionInfo)
        exc_response = exc_info.value.json()
        assert isinstance(exc_response.get("message"), str)
        assert exc_response.get("message") == "JSON could not be generated"
        assert "code" in exc_response and int(exc_response["code"]) == 502
