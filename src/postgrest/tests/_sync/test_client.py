import re
from typing import Any, Iterator
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
from postgrest.constants import DEFAULT_POSTGREST_CLIENT_TIMEOUT
from postgrest.exceptions import APIError

from ..credentials import (
    BASIC_AUTHORIZATION,
    BEARER_AUTHORIZATION,
    PASSWORD,
    TOKEN,
    USERNAME,
)


@pytest.fixture
def postgrest_client() -> Iterator[SyncPostgrestClient]:
    with SyncPostgrestClient("https://example.com") as client:
        yield client


class TestXClientInfo:
    def test_structured_metadata_format(
        self, postgrest_client: SyncPostgrestClient
    ) -> None:
        x_client_info = postgrest_client.session.headers.get("X-Client-Info")
        assert x_client_info is not None
        assert re.match(
            r"^supabase-py/postgrest-py v[\d.]+; platform=.+; platform-version=.+; runtime=python; runtime-version=\S+$",
            x_client_info,
        ), f"X-Client-Info format is wrong: {x_client_info}"


class TestConstructor:
    def test_simple(self, postgrest_client: SyncPostgrestClient) -> None:
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

    def test_default_timeout_uses_postgrest_constant(self) -> None:
        with SyncPostgrestClient("https://example.com") as client:
            assert client.timeout == DEFAULT_POSTGREST_CLIENT_TIMEOUT
            assert client.session.timeout == Timeout(
                timeout=DEFAULT_POSTGREST_CLIENT_TIMEOUT
            )

    def test_custom_headers(self) -> None:
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

    def test_invalid_base_url_raises(self) -> None:
        with pytest.raises(ValueError, match="base_url must be a valid HTTP URL"):
            SyncPostgrestClient("ftp://example.com")

    @pytest.mark.parametrize("url", ["http://example.com", "https://example.com"])
    def test_valid_http_base_url_constructs(self, url: str) -> None:
        client = SyncPostgrestClient(url)
        assert str(client.base_url) == url


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
    def test_auth_token(self, postgrest_client: SyncPostgrestClient) -> None:
        postgrest_client.auth(TOKEN)
        assert postgrest_client.headers["Authorization"] == BEARER_AUTHORIZATION

    def test_auth_basic(self, postgrest_client: SyncPostgrestClient) -> None:
        postgrest_client.auth(None, username=USERNAME, password=PASSWORD)

        assert isinstance(postgrest_client.basic_auth, BasicAuth)
        assert postgrest_client.basic_auth._auth_header == BASIC_AUTHORIZATION


def test_schema(postgrest_client: SyncPostgrestClient) -> None:
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


def test_response_status_code_outside_ok(
    postgrest_client: SyncPostgrestClient,
) -> None:
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
) -> None:
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


@pytest.mark.parametrize(
    "body, message, details",
    [
        (b'{"message": "JWT expired"}', "JWT expired", None),
        (
            b'{"code": "PGRST201", "details": [{"x": 1}], "hint": null, "message": "m"}',
            "m",
            [{"x": 1}],
        ),
    ],
)
def test_response_error_json_missing_or_non_string_fields(
    postgrest_client: SyncPostgrestClient, body, message, details
) -> None:
    with patch(
        "httpx._client.Client.request",
        return_value=Response(
            status_code=400,
            content=body,
            request=Request(method="GET", url="http://example.com"),
        ),
    ):
        with pytest.raises(APIError) as exc_info:
            postgrest_client.from_("test").select("a").execute()
        assert exc_info.value.message == message
        assert exc_info.value.details == details


@pytest.mark.parametrize("head", [False, True])
def test_rpc_query_params_send_lists_as_array_literals(
    postgrest_client: SyncPostgrestClient, head: bool
) -> None:
    params: Any = {"ids": [1, 2, 3], "name": "x"}
    builder = postgrest_client.rpc("sum_ids", params, head=head, get=not head)

    assert builder.request.params.get_list("ids") == ["{1,2,3}"]
    assert builder.request.params["name"] == "x"


@pytest.mark.parametrize("head", [False, True])
def test_rpc_query_params_quote_array_elements(
    postgrest_client: SyncPostgrestClient, head: bool
) -> None:
    params: Any = {"tags": ["a,b", "c d", "", 'say "hi"', "x}", "null", None]}
    builder = postgrest_client.rpc("tag_fn", params, head=head, get=not head)

    assert builder.request.params.get_list("tags") == [
        '{"a,b","c d","","say \\"hi\\"","x}","null",NULL}'
    ]
