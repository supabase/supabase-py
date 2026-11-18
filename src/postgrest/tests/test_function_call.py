import json
from dataclasses import dataclass, field
from typing import Any

import pytest
from httpx import AsyncClient, Client, MockTransport
from httpx import Request as HttpxRequest
from httpx import Response as HttpxResponse
from pydantic import ValidationError
from supabase_utils.http.adapters.httpx import AsyncHttpxSession, HttpxSession
from supabase_utils.types import JSON

from postgrest import (
    AsyncHttpTableExecutor,
    AsyncPostgrestClient,
    CountedResponse,
    CountMethod,
    FunctionCall,
    HttpTableExecutor,
    ResultShape,
    SyncPostgrestClient,
    TableOperation,
    TypedBuilder,
    TypedFilterBuilder,
)
from tests.typed_schema import Books, BooksRow

REST_URL = "https://example.com/rest/v1"
DUNE = {
    "id": 1,
    "title": "Dune",
    "isbn": None,
    "pages": 412,
    "published_on": "1965-08-01",
    "tags": ["science fiction"],
    "metadata": None,
}
SEARCH = FunctionCall.rows("search_books", BooksRow, arguments={"query": "dune"})


@dataclass
class Transport:
    content: bytes = b"[]"
    headers: dict[str, str] = field(default_factory=dict)
    seen: list[HttpxRequest] = field(default_factory=list)

    def handler(self, request: HttpxRequest) -> HttpxResponse:
        self.seen.append(request)
        return HttpxResponse(200, content=self.content, headers=self.headers)

    @property
    def only_request(self) -> HttpxRequest:
        (request,) = self.seen
        return request


def sync_client(transport: Transport) -> SyncPostgrestClient:
    return SyncPostgrestClient(
        REST_URL,
        http_session=HttpxSession(
            client=Client(transport=MockTransport(transport.handler))
        ),
    )


def async_client(transport: Transport) -> AsyncPostgrestClient:
    return AsyncPostgrestClient(
        REST_URL,
        http_session=AsyncHttpxSession(
            client=AsyncClient(transport=MockTransport(transport.handler))
        ),
    )


class TestFunctionCall:
    def test_rows_describes_a_call_that_returns_rows(self) -> None:
        call = FunctionCall.rows(
            "search_books",
            BooksRow,
            arguments={"query": "dune"},
            schema="library",
            read_only=True,
        )

        assert call == FunctionCall(
            "search_books",
            BooksRow,
            shape=ResultShape.ROWS,
            arguments={"query": "dune"},
            schema="library",
            read_only=True,
        )

    def test_value_describes_a_call_that_returns_a_value(self) -> None:
        call = FunctionCall.value("count_books", int)

        assert call == FunctionCall(
            "count_books", int, shape=ResultShape.VALUE, arguments={}
        )


class TestBuilds:
    def test_a_rows_call_gives_the_filter_builder_over_the_http_executor(
        self,
    ) -> None:
        client = sync_client(Transport())

        builder = client.rpc(SEARCH)

        assert isinstance(builder, TypedFilterBuilder)
        assert builder.executor == HttpTableExecutor(client)
        assert builder.request.operation is TableOperation.RPC
        assert builder.request.table.name == "search_books"
        assert builder.request.table.row_type is BooksRow
        assert builder.request.payload == {"query": "dune"}
        assert builder.request.shape is ResultShape.ROWS
        assert not builder.request.read_only

    def test_a_value_call_gives_a_builder_without_filters(self) -> None:
        client = sync_client(Transport())

        builder = client.rpc(FunctionCall.value("count_books", int, read_only=True))

        assert type(builder) is TypedBuilder
        assert builder.request.shape is ResultShape.VALUE
        assert builder.request.read_only

    async def test_the_async_client_gives_the_async_executor(self) -> None:
        client = async_client(Transport())

        assert client.rpc(SEARCH).executor == AsyncHttpTableExecutor(client)

    @pytest.mark.parametrize(
        "options",
        [{"params": {}}, {"head": True}, {"count": CountMethod.exact}, {"get": True}],
    )
    def test_a_call_rejects_the_options_of_a_name(
        self, options: dict[str, Any]
    ) -> None:
        client: Any = sync_client(Transport())

        with pytest.raises(TypeError):
            client.rpc(SEARCH, **options)

    def test_a_read_only_call_with_misread_arguments_rejects_head(self) -> None:
        client = sync_client(Transport())
        call = FunctionCall.rows(
            "search_books", BooksRow, arguments={"limit": 1}, read_only=True
        )

        with pytest.raises(ValueError, match="head"):
            client.rpc(call).head().execute()

    def test_a_name_without_params_is_rejected(self) -> None:
        client = sync_client(Transport())
        name: Any = "search_books"

        with pytest.raises(TypeError):
            client.rpc(name)


class TestSends:
    def test_a_call_posts_its_arguments(self) -> None:
        transport = Transport()

        sync_client(transport).rpc(SEARCH).execute()

        request = transport.only_request
        assert request.method == "POST"
        assert request.url.path == "/rest/v1/rpc/search_books"
        assert json.loads(request.content) == {"query": "dune"}

    def test_filters_order_and_window_go_into_the_query(self) -> None:
        transport = Transport()

        (
            sync_client(transport)
            .rpc(SEARCH)
            .where(Books.pages.gt(300))
            .order(Books.title.desc())
            .range(1, 2)
            .execute()
        )

        assert sorted(transport.only_request.url.params.multi_items()) == [
            ("limit", "2"),
            ("offset", "1"),
            ("order", "title.desc"),
            ("pages", "gt.300"),
        ]

    def test_a_read_only_call_sends_a_get_with_the_arguments_as_query(
        self,
    ) -> None:
        transport = Transport()
        call = FunctionCall.rows(
            "search_books", BooksRow, arguments={"ids": [1, 2]}, read_only=True
        )

        sync_client(transport).rpc(call).execute()

        request = transport.only_request
        assert request.method == "GET"
        assert request.url.params["ids"] == "{1,2}"
        assert request.content == b""

    def test_the_schema_of_the_call_is_sent(self) -> None:
        transport = Transport(content=b"1")
        call = FunctionCall.value("count_books", int, schema="library")

        sync_client(transport).rpc(call).execute()

        assert transport.only_request.headers["Content-Profile"] == "library"
        assert transport.only_request.headers["Accept-Profile"] == "library"


class TestDecodes:
    def test_rows_decode_into_the_row_type(self) -> None:
        transport = Transport(content=json.dumps([DUNE]).encode())

        rows = sync_client(transport).rpc(SEARCH).execute()

        assert rows == [BooksRow.model_validate(DUNE)]

    def test_count_comes_next_to_the_rows(self) -> None:
        transport = Transport(
            content=json.dumps([DUNE]).encode(), headers={"Content-Range": "0-0/5"}
        )

        response = sync_client(transport).rpc(SEARCH).count().execute()

        assert response == CountedResponse([BooksRow.model_validate(DUNE)], 5)

    @pytest.mark.parametrize(
        ("body", "expected"), [(b"42", 42), (b"null", None), (b"", None)]
    )
    def test_a_value_decodes_into_its_type_or_none(
        self, body: bytes, expected: int | None
    ) -> None:
        transport = Transport(content=body)

        value = sync_client(transport).rpc(FunctionCall.value("count", int)).execute()

        assert value == expected

    def test_a_single_row_decodes_into_its_type(self) -> None:
        transport = Transport(content=json.dumps(DUNE).encode())

        book = sync_client(transport).rpc(FunctionCall.value("latest", BooksRow))

        assert book.execute() == BooksRow.model_validate(DUNE)

    def test_a_value_of_another_type_raises(self) -> None:
        transport = Transport(content=b'"many"')

        with pytest.raises(ValidationError):
            sync_client(transport).rpc(FunctionCall.value("count", int)).execute()

    async def test_the_async_client_decodes_the_same(self) -> None:
        transport = Transport(content=b"[1, 2]")

        call = FunctionCall.value("ids", list[int])
        assert await async_client(transport).rpc(call).execute() == [1, 2]


@pytest.mark.parametrize(
    "arguments",
    [
        {"limit": 1},
        {"select": "x"},
        {"author.name": "x"},
        {"name": None},
        {"name": "eq.x"},
        {"name": "not.in.(1)"},
        {"name": "like(any).x"},
        {"name": "fts(english).x"},
    ],
)
def test_a_read_only_call_postgrest_would_misread_is_posted(
    arguments: dict[str, JSON],
) -> None:
    transport = Transport()
    call = FunctionCall.rows(
        "search_books", BooksRow, arguments=arguments, read_only=True
    )

    sync_client(transport).rpc(call).execute()

    request = transport.only_request
    assert request.method == "POST"
    assert not request.url.params
    assert json.loads(request.content) == arguments


@pytest.mark.parametrize(
    "arguments",
    [{"name": "equal.x"}, {"name": "eq"}, {"name": 1}, {"ids": [1, None]}],
)
def test_a_read_only_call_postgrest_reads_as_arguments_is_a_get(
    arguments: dict[str, JSON],
) -> None:
    transport = Transport()
    call = FunctionCall.rows(
        "search_books", BooksRow, arguments=arguments, read_only=True
    )

    sync_client(transport).rpc(call).execute()

    assert transport.only_request.method == "GET"
