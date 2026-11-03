import json
import re
from collections.abc import AsyncIterator
from typing import Any
from unittest.mock import patch

import pytest
from httpx import (
    AsyncClient,
    AsyncHTTPTransport,
    BasicAuth,
    Headers,
    Limits,
    MockTransport,
    Request,
    Response,
    Timeout,
)

from postgrest import AsyncPostgrestClient
from postgrest.base_request_builder import MAX_RETRIES
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
async def postgrest_client() -> AsyncIterator[AsyncPostgrestClient]:
    async with AsyncPostgrestClient("https://example.com") as client:
        yield client


class TestXClientInfo:
    def test_structured_metadata_format(
        self, postgrest_client: AsyncPostgrestClient
    ) -> None:
        x_client_info = postgrest_client.session.headers.get("X-Client-Info")
        assert x_client_info is not None
        assert re.match(
            r"^supabase-py/postgrest-py v[\d.]+; platform=.+; platform-version=.+; runtime=python; runtime-version=\S+$",
            x_client_info,
        ), f"X-Client-Info format is wrong: {x_client_info}"


class TestConstructor:
    def test_simple(self, postgrest_client: AsyncPostgrestClient) -> None:
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
    async def test_default_timeout_uses_postgrest_constant(self) -> None:
        async with AsyncPostgrestClient("https://example.com") as client:
            assert client.timeout == DEFAULT_POSTGREST_CLIENT_TIMEOUT
            assert client.session.timeout == Timeout(
                timeout=DEFAULT_POSTGREST_CLIENT_TIMEOUT
            )

    @pytest.mark.asyncio
    async def test_custom_headers(self) -> None:
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

    def test_invalid_base_url_raises(self) -> None:
        with pytest.raises(ValueError, match="base_url must be a valid HTTP URL"):
            AsyncPostgrestClient("ftp://example.com")

    @pytest.mark.parametrize("url", ["http://example.com", "https://example.com"])
    def test_valid_http_base_url_constructs(self, url: str) -> None:
        client = AsyncPostgrestClient(url)
        assert str(client.base_url) == url


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
    def test_auth_token(self, postgrest_client: AsyncPostgrestClient) -> None:
        postgrest_client.auth(TOKEN)
        assert postgrest_client.headers["Authorization"] == BEARER_AUTHORIZATION

    def test_auth_basic(self, postgrest_client: AsyncPostgrestClient) -> None:
        postgrest_client.auth(None, username=USERNAME, password=PASSWORD)

        assert isinstance(postgrest_client.basic_auth, BasicAuth)
        assert postgrest_client.basic_auth._auth_header == BASIC_AUTHORIZATION


def test_schema(postgrest_client: AsyncPostgrestClient) -> None:
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
async def test_response_status_code_outside_ok(
    postgrest_client: AsyncPostgrestClient,
) -> None:
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
) -> None:
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
        assert exc_response.get("message") == "Bad Gateway"
        assert exc_response.get("code") == "502"
        assert exc_response.get("hint") is None
        assert (
            exc_response.get("details")
            == '"gateway error: Error: Network connection lost."'
        )


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "headers, code",
    [
        ([("Proxy-Status", "PostgREST; error=PGRST301")], "PGRST301"),
        ([("Proxy-Status", "cdn; error=connection_timeout")], "502"),
        ([], "502"),
    ],
)
async def test_response_client_non_json_error_body(
    postgrest_client: AsyncPostgrestClient,
    headers: list[tuple[str, str]],
    code: str,
) -> None:
    with patch(
        "httpx._client.AsyncClient.request",
        return_value=Response(
            status_code=502,
            headers=[*headers, ("Content-Type", "text/html; charset=utf-8")],
            content="<html><body>Bad gateway ü</body></html>".encode(),
            request=Request(method="GET", url="http://example.com"),
        ),
    ):
        with pytest.raises(APIError) as exc_info:
            await postgrest_client.from_("test").select("a").execute()
        assert exc_info.value.message == "Bad Gateway"
        assert exc_info.value.code == code
        assert exc_info.value.hint is None
        assert exc_info.value.details == "<html><body>Bad gateway ü</body></html>"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "headers, code",
    [
        ([("Proxy-Status", "PostgREST; error=PGRST108")], "PGRST108"),
        ([("Proxy-Status", 'PostgREST; error="42703"')], "42703"),
        ([("Proxy-Status", 'PostgREST; error="a\\"b"')], 'a"b'),
        (
            [
                (
                    "Proxy-Status",
                    "PostgREST; error=PGRST108, cdn; error=http_request_error",
                )
            ],
            "PGRST108",
        ),
        (
            [("Proxy-Status", "cdn; error=connection_timeout, PostgREST; error=57014")],
            "57014",
        ),
        (
            [
                ("Proxy-Status", "cdn; error=connection_timeout"),
                ("Proxy-Status", "PostgREST; error=PGRST301"),
            ],
            "PGRST301",
        ),
        (
            [("Proxy-Status", 'PostgREST; details="a; b, error=x"; error=PGRST116')],
            "PGRST116",
        ),
        ([("Proxy-Status", "cdn; error=connection_timeout")], "400"),
        ([("Proxy-Status", "PostgREST; error=")], "400"),
        ([("Proxy-Status", "PostgREST")], "400"),
        ([], "400"),
    ],
)
async def test_response_client_empty_error_body(
    postgrest_client: AsyncPostgrestClient,
    headers: list[tuple[str, str]],
    code: str,
) -> None:
    with patch(
        "httpx._client.AsyncClient.request",
        return_value=Response(
            status_code=400,
            headers=headers,
            request=Request(method="HEAD", url="http://example.com"),
        ),
    ):
        client = postgrest_client.from_("test").select("*", head=True)
        with pytest.raises(APIError) as exc_info:
            await client.execute()
        assert exc_info.value.code == code
        assert exc_info.value.message == "Bad Request"
        assert exc_info.value.details is None


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
) -> None:
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
) -> None:
    params: Any = {"ids": [1, 2, 3], "name": "x"}
    builder = postgrest_client.rpc("sum_ids", params, head=head, get=not head)

    assert builder.request.params.get_list("ids") == ["{1,2,3}"]
    assert builder.request.params["name"] == "x"


@pytest.mark.parametrize("head", [False, True])
def test_rpc_query_params_quote_array_elements(
    postgrest_client: AsyncPostgrestClient, head: bool
) -> None:
    params: Any = {"tags": ["a,b", "c d", "", 'say "hi"', "x}", "null", None]}
    builder = postgrest_client.rpc("tag_fn", params, head=head, get=not head)

    assert builder.request.params.get_list("tags") == [
        '{"a,b","c d","","say \\"hi\\"","x}","null",NULL}'
    ]


@pytest.mark.parametrize("method", ["GET", "HEAD", "POST"])
@pytest.mark.parametrize(
    ("options", "encoded"),
    [
        ({"enabled": True}, '{"enabled":true}'),
        (
            {"nested": {"items": [1, None, "a&b"]}},
            '{"nested":{"items":[1,null,"a&b"]}}',
        ),
        ({}, "{}"),
    ],
)
async def test_rpc_serializes_dictionary_arguments(
    method: str, options: dict, encoded: str
) -> None:
    requests: list[Request] = []

    def handler(request: Request) -> Response:
        requests.append(request)
        return Response(200, json=[])

    params: Any = {
        "options": options,
        "raw": '{"preserved": true}',
        "ids": [1, 2],
        "text": "keep",
    }
    async with AsyncClient(transport=MockTransport(handler)) as http:
        client = AsyncPostgrestClient("https://example.com", http_client=http)
        await client.rpc(
            "example", params, get=method == "GET", head=method == "HEAD"
        ).execute()

    assert len(requests) == 1
    request = requests[0]
    assert request.method == method
    if method == "POST":
        assert json.loads(request.content) == params
        assert "options" not in request.url.params
    else:
        assert request.url.params.get_list("options") == [encoded]
        assert request.url.params["raw"] == params["raw"]
        assert request.url.params["ids"] == "{1,2}"
        assert request.url.params["text"] == "keep"


class TestRetryEnabled:
    def test_default_enabled(self, postgrest_client: AsyncPostgrestClient) -> None:
        assert postgrest_client.retry_enabled is True
        assert postgrest_client.from_("test").select("*").request.retry_enabled is True

    async def test_client_level_disable_propagates(self) -> None:
        async with AsyncPostgrestClient(
            "https://example.com", retry_enabled=False
        ) as client:
            assert client.from_("test").select("*").request.retry_enabled is False
            assert client.rpc("test_fn", {}).request.retry_enabled is False
            assert client.schema("other").retry_enabled is False

    async def test_request_level_override(self) -> None:
        async with AsyncPostgrestClient(
            "https://example.com", retry_enabled=False
        ) as client:
            builder = client.from_("test").select("*").retry(True)
            assert builder.request.retry_enabled is True

    async def test_client_level_disable_does_not_retry_on_503(self) -> None:
        calls = 0

        async def fake_send(request: Request, **kwargs: Any) -> Response:
            nonlocal calls
            calls += 1
            return Response(503)

        async with AsyncPostgrestClient(
            "https://example.com", retry_enabled=False
        ) as client:
            with patch.object(client.session, "send", wraps=fake_send):
                with pytest.raises(APIError):
                    await client.from_("test").select("*").execute()

        assert calls == 1

    async def test_client_level_disable_request_override_retries(self) -> None:
        calls = 0

        async def fake_send(request: Request, **kwargs: Any) -> Response:
            nonlocal calls
            if calls > 0:
                assert request.headers["X-Retry-Count"] == str(calls)
            calls += 1
            return Response(503)

        async with AsyncPostgrestClient(
            "https://example.com", retry_enabled=False
        ) as client:
            with (
                patch.object(client.session, "send", wraps=fake_send),
                patch(
                    "postgrest._async.request_builder.get_retry_delay", return_value=0
                ),
            ):
                with pytest.raises(APIError):
                    await client.from_("test").select("*").retry(True).execute()

        assert calls == 1 + MAX_RETRIES

    async def test_default_retries_on_503(self) -> None:
        calls = 0

        async def fake_send(request: Request, **kwargs: Any) -> Response:
            nonlocal calls
            calls += 1
            return Response(503)

        async with AsyncPostgrestClient("https://example.com") as client:
            with (
                patch.object(client.session, "send", wraps=fake_send),
                patch(
                    "postgrest._async.request_builder.get_retry_delay", return_value=0
                ),
            ):
                with pytest.raises(APIError):
                    await client.from_("test").select("*").execute()

        assert calls == 1 + MAX_RETRIES
