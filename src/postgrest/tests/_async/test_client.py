import re
from typing import Any
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


class TestXClientInfo:
    def test_structured_metadata_format(self, postgrest_client: AsyncPostgrestClient):
        x_client_info = postgrest_client.session.headers.get("X-Client-Info")
        assert x_client_info is not None
        assert re.match(
            r"^supabase-py/postgrest-py v[\d.]+; platform=.+; platform-version=.+; runtime=python; runtime-version=\S+$",
            x_client_info,
        ), f"X-Client-Info format is wrong: {x_client_info}"


class TestConstructor:
    def test_simple(self, postgrest_client: AsyncPostgrestClient):
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

    @pytest.mark.asyncio
    async def test_custom_headers(self):
        async with AsyncPostgrestClient(
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
    @pytest.mark.asyncio
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
            "https://example.com", http_client=http_client, timeout=20.0
        ) as client:
            assert str(client.base_url) == "https://example.com"
            assert client.session.timeout == Timeout(
                timeout=5.0
            )  # Should be the default 5 since we use custom httpx client
            assert client.session.headers.get("x-user-agent") == "my-app/0.0.1"
            assert isinstance(client.session, AsyncClient)


class TestAuth:
    def test_auth_token(self, postgrest_client: AsyncPostgrestClient):
        postgrest_client.auth("s3cr3t")
        assert postgrest_client.headers["Authorization"] == "Bearer s3cr3t"

    def test_auth_basic(self, postgrest_client: AsyncPostgrestClient):
        postgrest_client.auth(None, username="admin", password="s3cr3t")

        assert isinstance(postgrest_client.basic_auth, BasicAuth)
        assert (
            postgrest_client.basic_auth._auth_header
            == BasicAuth("admin", "s3cr3t")._auth_header
        )


def test_schema(postgrest_client: AsyncPostgrestClient):
    client = postgrest_client.schema("private")
    subheaders = {
        "accept-profile": "private",
        "content-profile": "private",
    }

    assert subheaders.items() < client.headers.items()


# @pytest.mark.asyncio
# async def test_params_purged_after_execute(postgrest_client: AsyncPostgrestClient):
#     assert len(postgrest_client.session.params) == 0
#     with pytest.raises(APIError):
#         await postgrest_client.from_("test").select("a", "b").eq("c", "d").execute()
#     assert len(postgrest_client.session.params) == 0


@pytest.mark.asyncio
async def test_response_status_code_outside_ok(postgrest_client: AsyncPostgrestClient):
    with patch(
        "postgrest._async.request_builder.AsyncSelectRequestBuilder.execute",
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
            await (
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
@pytest.mark.asyncio
async def test_response_client_invalid_response_but_valid_json(
    postgrest_client: AsyncPostgrestClient,
):
    with patch(
        "httpx._client.AsyncClient.request",
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
            await client.execute()
        assert isinstance(exc_info, pytest.ExceptionInfo)
        exc_response = exc_info.value.json()
        assert isinstance(exc_response.get("message"), str)
        assert exc_response.get("message") == "JSON could not be generated"
        assert "code" in exc_response and int(exc_response["code"]) == 502


@pytest.mark.asyncio
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
async def test_response_error_json_missing_or_non_string_fields(
    postgrest_client: AsyncPostgrestClient, body, message, details
):
    with patch(
        "httpx._client.AsyncClient.request",
        return_value=Response(
            status_code=400,
            content=body,
            request=Request(method="GET", url="http://example.com"),
        ),
    ):
        with pytest.raises(APIError) as exc_info:
            await postgrest_client.from_("test").select("a").execute()
        assert exc_info.value.message == message
        assert exc_info.value.details == details


@pytest.mark.parametrize("head", [False, True])
def test_rpc_query_params_send_lists_as_array_literals(
    postgrest_client: AsyncPostgrestClient, head: bool
):
    params: Any = {"ids": [1, 2, 3], "name": "x"}
    builder = postgrest_client.rpc("sum_ids", params, head=head, get=not head)

    assert builder.request.params.get_list("ids") == ["{1,2,3}"]
    assert builder.request.params["name"] == "x"


@pytest.mark.parametrize("head", [False, True])
def test_rpc_query_params_quote_array_elements(
    postgrest_client: AsyncPostgrestClient, head: bool
):
    params: Any = {"tags": ["a,b", "c d", "", 'say "hi"', "x}", "null", None]}
    builder = postgrest_client.rpc("tag_fn", params, head=head, get=not head)

    assert builder.request.params.get_list("tags") == [
        '{"a,b","c d","","say \\"hi\\"","x}","null",NULL}'
    ]


@pytest.mark.parametrize("head", [False, True])
def test_rpc_query_params_send_dicts_as_json(
    postgrest_client: AsyncPostgrestClient, head: bool
):
    params: Any = {"options": {"enabled": True}, "count": 1}
    builder = postgrest_client.rpc("custom_fn", params, head=head, get=not head)

    assert builder.request.params.get("options") == '{"enabled":true}'
    assert builder.request.params.get("count") == "1"


def test_rpc_post_sends_dict_in_body(postgrest_client: AsyncPostgrestClient):
    params: Any = {"options": {"enabled": True}, "count": 1}
    builder = postgrest_client.rpc("custom_fn", params)

    assert builder.request.http_method == "POST"
    assert builder.request.json == params
    assert len(builder.request.params) == 0


@pytest.mark.parametrize("head", [False, True])
async def test_rpc_query_params_mock_transport_decodes_json(head: bool):
    from httpx import AsyncClient, MockTransport, Response

    seen_params = []

    def handler(request):
        seen_params.append(dict(request.url.params))
        return Response(200, json=[])

    async with AsyncClient(transport=MockTransport(handler)) as http:
        client = AsyncPostgrestClient("https://example.com", http_client=http)
        await client.rpc(
            "example", {"options": {"enabled": True}}, head=head, get=not head
        ).execute()

    assert seen_params == [{"options": '{"enabled":true}'}]
