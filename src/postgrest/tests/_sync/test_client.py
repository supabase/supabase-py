import re
from unittest.mock import Mock, patch

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
from postgrest.base_request_builder import MAX_RETRIES
from postgrest.exceptions import APIError


@pytest.fixture
def postgrest_client():
    with SyncPostgrestClient("https://example.com") as client:
        yield client


class TestXClientInfo:
    def test_structured_metadata_format(self, postgrest_client: SyncPostgrestClient):
        x_client_info = postgrest_client.session.headers.get("X-Client-Info")
        assert x_client_info is not None
        assert re.match(
            r"^supabase-py/postgrest-py v[\d.]+; platform=.+; platform-version=.+; runtime=python; runtime-version=\S+$",
            x_client_info,
        ), f"X-Client-Info format is wrong: {x_client_info}"


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


#
# async def test_params_purged_after_execute(postgrest_client: SyncPostgrestClient):
#     assert len(postgrest_client.session.params) == 0
#     with pytest.raises(APIError):
#         await postgrest_client.from_("test").select("a", "b").eq("c", "d").execute()
#     assert len(postgrest_client.session.params) == 0


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


class TestRetryEnabled:
    def test_default_enabled(self, postgrest_client: SyncPostgrestClient):
        assert postgrest_client.retry_enabled is True
        assert postgrest_client.from_("test").select("*").request.retry_enabled is True

    def test_client_level_disable_propagates(self):
        with SyncPostgrestClient("https://example.com", retry_enabled=False) as client:
            assert client.from_("test").select("*").request.retry_enabled is False
            assert client.rpc("test_fn", {}).request.retry_enabled is False
            assert client.schema("other").retry_enabled is False

    def test_request_level_override(self):
        with SyncPostgrestClient("https://example.com", retry_enabled=False) as client:
            builder = client.from_("test").select("*").retry(True)
            assert builder.request.retry_enabled is True

    def test_client_level_disable_does_not_retry_on_503(self):
        calls = 0

        def fake_send(request: Request, **kwargs):
            nonlocal calls
            calls += 1
            return Response(503)

        with SyncPostgrestClient("https://example.com", retry_enabled=False) as client:
            with patch.object(client.session, "send", wraps=fake_send):
                with pytest.raises(APIError):
                    client.from_("test").select("*").execute()

        assert calls == 1

    def test_client_level_disable_request_override_retries(self):
        calls = 0

        def fake_send(request: Request, **kwargs):
            nonlocal calls
            if calls > 0:
                assert request.headers["X-Retry-Count"] == str(calls)
            calls += 1
            return Response(503)

        with SyncPostgrestClient("https://example.com", retry_enabled=False) as client:
            with (
                patch.object(client.session, "send", wraps=fake_send),
                patch("time.sleep", new=Mock()),
            ):
                with pytest.raises(APIError):
                    client.from_("test").select("*").retry(True).execute()

        assert calls == 1 + MAX_RETRIES

    def test_default_retries_on_503(self):
        calls = 0

        def fake_send(request: Request, **kwargs):
            nonlocal calls
            calls += 1
            return Response(503)

        with SyncPostgrestClient("https://example.com") as client:
            with (
                patch.object(client.session, "send", wraps=fake_send),
                patch("time.sleep", new=Mock()),
            ):
                with pytest.raises(APIError):
                    client.from_("test").select("*").execute()

        assert calls == 1 + MAX_RETRIES
