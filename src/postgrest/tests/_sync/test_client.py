import datetime
import json
import re
import uuid
from collections.abc import Iterator
from typing import Annotated, Any, NotRequired, TypedDict
from unittest.mock import patch

import pytest
from httpx import (
    BasicAuth,
    Client,
    ConnectError,
    Headers,
    HTTPTransport,
    Limits,
    MockTransport,
    ReadError,
    ReadTimeout,
    RemoteProtocolError,
    Request,
    Response,
    Timeout,
)
from pydantic import Field, JsonValue

from postgrest import SyncPostgrestClient
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


def test_schema_keeps_custom_http_client() -> None:
    sent: list[Request] = []

    def handler(request: Request) -> Response:
        sent.append(request)
        return Response(200, json=[])

    http_client = Client(transport=MockTransport(handler))
    client = SyncPostgrestClient("https://example.com", http_client=http_client)

    private = client.schema("private")
    assert private.session is http_client

    private.from_("countries").select("*").execute()
    assert len(sent) == 1
    assert sent[0].headers["accept-profile"] == "private"
    client.aclose()


def test_closing_schema_client_keeps_shared_session_open() -> None:
    http_client = Client(transport=MockTransport(lambda _: Response(200)))
    client = SyncPostgrestClient("https://example.com", http_client=http_client)

    with client.schema("private"):
        pass
    assert not http_client.is_closed

    client.aclose()
    assert http_client.is_closed


def test_schema_keeps_basic_auth(postgrest_client: SyncPostgrestClient) -> None:
    postgrest_client.auth(None, username="admin", password="s3cr3t")

    private = postgrest_client.schema("private")

    assert private.basic_auth is postgrest_client.basic_auth


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
        assert exc_response.get("message") == "Bad Gateway"
        assert exc_response.get("code") == "502"
        assert exc_response.get("hint") is None
        assert (
            exc_response.get("details")
            == '"gateway error: Error: Network connection lost."'
        )


@pytest.mark.parametrize(
    "headers, code",
    [
        ([("Proxy-Status", "PostgREST; error=PGRST301")], "PGRST301"),
        ([("Proxy-Status", "cdn; error=connection_timeout")], "502"),
        ([], "502"),
    ],
)
def test_response_client_non_json_error_body(
    postgrest_client: SyncPostgrestClient,
    headers: list[tuple[str, str]],
    code: str,
) -> None:
    with patch(
        "httpx._client.Client.request",
        return_value=Response(
            status_code=502,
            headers=[*headers, ("Content-Type", "text/html; charset=utf-8")],
            content="<html><body>Bad gateway ü</body></html>".encode(),
            request=Request(method="GET", url="http://example.com"),
        ),
    ):
        with pytest.raises(APIError) as exc_info:
            postgrest_client.from_("test").select("a").execute()
        assert exc_info.value.message == "Bad Gateway"
        assert exc_info.value.code == code
        assert exc_info.value.hint is None
        assert exc_info.value.details == "<html><body>Bad gateway ü</body></html>"


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
def test_response_client_empty_error_body(
    postgrest_client: SyncPostgrestClient,
    headers: list[tuple[str, str]],
    code: str,
) -> None:
    with patch(
        "httpx._client.Client.request",
        return_value=Response(
            status_code=400,
            headers=headers,
            request=Request(method="HEAD", url="http://example.com"),
        ),
    ):
        client = postgrest_client.from_("test").select("*", head=True)
        with pytest.raises(APIError) as exc_info:
            client.execute()
        assert exc_info.value.code == code
        assert exc_info.value.message == "Bad Request"
        assert exc_info.value.details is None


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
def test_rpc_serializes_dictionary_arguments(
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
    with Client(transport=MockTransport(handler)) as http:
        client = SyncPostgrestClient("https://example.com", http_client=http)
        client.rpc(
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


class PublicEventsInsert(TypedDict):
    id: NotRequired[Annotated[uuid.UUID, Field(alias="id")]]
    created_at: NotRequired[Annotated[datetime.datetime, Field(alias="created_at")]]
    day: NotRequired[Annotated[datetime.date | None, Field(alias="day")]]
    starts_at: NotRequired[Annotated[datetime.time, Field(alias="starts_at")]]
    payload: NotRequired[Annotated[bytes | None, Field(alias="payload")]]
    data: NotRequired[Annotated[JsonValue | None, Field(alias="data")]]
    tags: NotRequired[Annotated[list[str], Field(alias="tags")]]
    name: Annotated[str, Field(alias="name")]


class PublicEventsUpdate(TypedDict):
    id: NotRequired[Annotated[uuid.UUID, Field(alias="id")]]
    created_at: NotRequired[Annotated[datetime.datetime, Field(alias="created_at")]]
    name: NotRequired[Annotated[str, Field(alias="name")]]


EVENT_ID = uuid.UUID("6f1b6c1e-1d2f-4e8b-9a43-6b3c2f0a7d11")
EVENT_ROW: PublicEventsInsert = {
    "id": EVENT_ID,
    "created_at": datetime.datetime(2024, 5, 1, 12, 30, tzinfo=datetime.UTC),
    "day": datetime.date(2024, 5, 1),
    "starts_at": datetime.time(9, 15),
    "payload": b"ab",
    "data": {"nested": [1, None, "x"]},
    "tags": ["a", "b"],
    "name": "launch",
}
ENCODED_EVENT_ROW = {
    "id": "6f1b6c1e-1d2f-4e8b-9a43-6b3c2f0a7d11",
    "created_at": "2024-05-01T12:30:00+00:00",
    "day": "2024-05-01",
    "starts_at": "09:15:00",
    "payload": "\\x6162",
    "data": {"nested": [1, None, "x"]},
    "tags": ["a", "b"],
    "name": "launch",
}


class TestGeneratedTypedDictBodies:
    @pytest.fixture
    def captured(
        self,
    ) -> Iterator[tuple[SyncPostgrestClient, list[Request]]]:
        requests: list[Request] = []

        def handler(request: Request) -> Response:
            requests.append(request)
            return Response(201, json=[])

        with Client(transport=MockTransport(handler)) as http:
            yield (
                SyncPostgrestClient("https://example.com", http_client=http),
                requests,
            )

    def test_insert(self, captured: tuple[SyncPostgrestClient, list[Request]]) -> None:
        client, requests = captured
        client.from_("events").insert(EVENT_ROW).execute()

        assert requests[0].method == "POST"
        assert requests[0].headers["Content-Type"] == "application/json"
        assert json.loads(requests[0].content) == ENCODED_EVENT_ROW

    def test_bulk_insert(
        self, captured: tuple[SyncPostgrestClient, list[Request]]
    ) -> None:
        client, requests = captured
        rows: list[PublicEventsInsert] = [EVENT_ROW, {"name": "other"}]
        client.from_("events").insert(rows).execute()

        assert json.loads(requests[0].content) == [ENCODED_EVENT_ROW, {"name": "other"}]
        assert set(requests[0].url.params["columns"].split(",")) == {
            f'"{key}"' for key in ENCODED_EVENT_ROW
        }

    def test_upsert(self, captured: tuple[SyncPostgrestClient, list[Request]]) -> None:
        client, requests = captured
        client.from_("events").upsert(EVENT_ROW, on_conflict="id").execute()

        assert requests[0].method == "POST"
        assert json.loads(requests[0].content) == ENCODED_EVENT_ROW

    def test_update(self, captured: tuple[SyncPostgrestClient, list[Request]]) -> None:
        client, requests = captured
        changes: PublicEventsUpdate = {
            "created_at": datetime.datetime(2024, 6, 1, tzinfo=datetime.UTC),
            "name": "renamed",
        }
        client.from_("events").update(changes).eq("id", str(EVENT_ID)).execute()

        assert requests[0].method == "PATCH"
        assert json.loads(requests[0].content) == {
            "created_at": "2024-06-01T00:00:00+00:00",
            "name": "renamed",
        }

    def test_bulk_insert_with_tuple_sends_columns(
        self, captured: tuple[SyncPostgrestClient, list[Request]]
    ) -> None:
        client, requests = captured
        rows: tuple[PublicEventsInsert, ...] = (
            {"name": "a"},
            {"name": "b", "id": EVENT_ID},
        )
        client.from_("events").insert(rows).execute()

        assert json.loads(requests[0].content) == [
            {"name": "a"},
            {"name": "b", "id": str(EVENT_ID)},
        ]
        assert set(requests[0].url.params["columns"].split(",")) == {'"name"', '"id"'}

    def test_rpc_encodes_generated_types(
        self, captured: tuple[SyncPostgrestClient, list[Request]]
    ) -> None:
        client, requests = captured
        params: Any = {"event_id": EVENT_ID, "day": datetime.date(2024, 5, 1)}
        client.rpc("events_on", params).execute()

        assert json.loads(requests[0].content) == {
            "event_id": str(EVENT_ID),
            "day": "2024-05-01",
        }

    def test_insert_scalar_list_sends_no_columns(
        self, captured: tuple[SyncPostgrestClient, list[Request]]
    ) -> None:
        client, requests = captured
        client.from_("events").insert([1, 2]).execute()

        assert json.loads(requests[0].content) == [1, 2]
        assert "columns" not in requests[0].url.params

    def test_custom_content_type_is_kept(
        self, captured: tuple[SyncPostgrestClient, list[Request]]
    ) -> None:
        client, requests = captured
        builder = client.from_("events").insert({"name": "launch"})
        builder.request.headers["Content-Type"] = "application/json; charset=utf-8"
        builder.execute()

        assert requests[0].headers["Content-Type"] == "application/json; charset=utf-8"

    def test_select_sends_no_body(
        self, captured: tuple[SyncPostgrestClient, list[Request]]
    ) -> None:
        client, requests = captured
        client.from_("events").select("*").execute()

        assert requests[0].content == b""


class TestRetryEnabled:
    def test_default_enabled(self, postgrest_client: SyncPostgrestClient) -> None:
        assert postgrest_client.retry_enabled is True
        assert postgrest_client.from_("test").select("*").request.retry_enabled is True

    def test_client_level_disable_propagates(self) -> None:
        with SyncPostgrestClient("https://example.com", retry_enabled=False) as client:
            assert client.from_("test").select("*").request.retry_enabled is False
            assert client.rpc("test_fn", {}).request.retry_enabled is False
            assert client.schema("other").retry_enabled is False

    def test_request_level_override(self) -> None:
        with SyncPostgrestClient("https://example.com", retry_enabled=False) as client:
            builder = client.from_("test").select("*").retry(True)
            assert builder.request.retry_enabled is True

    def test_client_level_disable_does_not_retry_on_503(self) -> None:
        calls = 0

        def fake_send(request: Request, **kwargs: Any) -> Response:
            nonlocal calls
            calls += 1
            return Response(503)

        with SyncPostgrestClient("https://example.com", retry_enabled=False) as client:
            with patch.object(client.session, "send", wraps=fake_send):
                with pytest.raises(APIError):
                    client.from_("test").select("*").execute()

        assert calls == 1

    def test_client_level_disable_request_override_retries(self) -> None:
        calls = 0

        def fake_send(request: Request, **kwargs: Any) -> Response:
            nonlocal calls
            if calls > 0:
                assert request.headers["X-Retry-Count"] == str(calls)
            calls += 1
            return Response(503)

        with SyncPostgrestClient("https://example.com", retry_enabled=False) as client:
            with (
                patch.object(client.session, "send", wraps=fake_send),
                patch(
                    "postgrest._sync.request_builder.get_retry_delay", return_value=0
                ),
            ):
                with pytest.raises(APIError):
                    client.from_("test").select("*").retry(True).execute()

        assert calls == 1 + MAX_RETRIES

    def test_default_retries_on_503(self) -> None:
        calls = 0

        def fake_send(request: Request, **kwargs: Any) -> Response:
            nonlocal calls
            calls += 1
            return Response(503)

        with SyncPostgrestClient("https://example.com") as client:
            with (
                patch.object(client.session, "send", wraps=fake_send),
                patch(
                    "postgrest._sync.request_builder.get_retry_delay", return_value=0
                ),
            ):
                with pytest.raises(APIError):
                    client.from_("test").select("*").execute()

        assert calls == 1 + MAX_RETRIES


class TestRetryOnNetworkError:
    @pytest.mark.parametrize(
        "error",
        [
            RemoteProtocolError("Server disconnected without sending a response."),
            ReadError("Connection reset by peer"),
            ConnectError("Connection refused"),
        ],
    )
    def test_select_is_retried_after_a_dropped_connection(
        self, error: Exception
    ) -> None:
        methods: list[str] = []

        def fake_send(request: Request, **kwargs: Any) -> Response:
            methods.append(request.method)
            if len(methods) == 1:
                raise error
            assert request.headers["X-Retry-Count"] == "1"
            return Response(200, json=[], request=request)

        with SyncPostgrestClient("https://example.com") as client:
            with (
                patch.object(client.session, "send", wraps=fake_send),
                patch(
                    "postgrest._sync.request_builder.get_retry_delay", return_value=0
                ),
            ):
                response = client.from_("test").select("*").execute()

        assert response.data == []
        assert methods == ["GET", "GET"]

    def test_head_is_retried_after_a_dropped_connection(self) -> None:
        methods: list[str] = []

        def fake_send(request: Request, **kwargs: Any) -> Response:
            methods.append(request.method)
            if len(methods) == 1:
                raise RemoteProtocolError("Server disconnected")
            return Response(200, headers={"Content-Range": "*/0"}, request=request)

        with SyncPostgrestClient("https://example.com") as client:
            with (
                patch.object(client.session, "send", wraps=fake_send),
                patch(
                    "postgrest._sync.request_builder.get_retry_delay", return_value=0
                ),
            ):
                client.from_("test").select("*", head=True).execute()

        assert methods == ["HEAD", "HEAD"]

    def test_gives_up_after_max_retries(self) -> None:
        calls = 0

        def fake_send(request: Request, **kwargs: Any) -> Response:
            nonlocal calls
            calls += 1
            raise RemoteProtocolError("Server disconnected")

        with SyncPostgrestClient("https://example.com") as client:
            with (
                patch.object(client.session, "send", wraps=fake_send),
                patch(
                    "postgrest._sync.request_builder.get_retry_delay", return_value=0
                ),
            ):
                with pytest.raises(RemoteProtocolError):
                    client.from_("test").select("*").execute()

        assert calls == 1 + MAX_RETRIES

    def test_write_is_not_retried(self) -> None:
        calls = 0

        def fake_send(request: Request, **kwargs: Any) -> Response:
            nonlocal calls
            calls += 1
            raise RemoteProtocolError("Server disconnected")

        with SyncPostgrestClient("https://example.com") as client:
            with patch.object(client.session, "send", wraps=fake_send):
                with pytest.raises(RemoteProtocolError):
                    client.from_("test").insert({"a": 1}).execute()

        assert calls == 1

    def test_retry_disabled(self) -> None:
        calls = 0

        def fake_send(request: Request, **kwargs: Any) -> Response:
            nonlocal calls
            calls += 1
            raise RemoteProtocolError("Server disconnected")

        with SyncPostgrestClient("https://example.com") as client:
            with patch.object(client.session, "send", wraps=fake_send):
                with pytest.raises(RemoteProtocolError):
                    client.from_("test").select("*").retry(False).execute()

        assert calls == 1

    def test_timeout_is_not_retried(self) -> None:
        calls = 0

        def fake_send(request: Request, **kwargs: Any) -> Response:
            nonlocal calls
            calls += 1
            raise ReadTimeout("timed out")

        with SyncPostgrestClient("https://example.com") as client:
            with patch.object(client.session, "send", wraps=fake_send):
                with pytest.raises(ReadTimeout):
                    client.from_("test").select("*").execute()

        assert calls == 1
