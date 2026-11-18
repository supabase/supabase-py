from typing import TYPE_CHECKING, Any, TypedDict, assert_type

import httpx
import pytest
from httpx import AsyncClient as AsyncHttpxClient
from httpx import Client as SyncHttpxClient
from postgrest import TypedBuilder, TypedFilterBuilder, TypedQueryBuilder
from pydantic import BaseModel

from supabase import (
    AsyncTableExecutor,
    Column,
    FunctionCall,
    Table,
    TableExecutor,
)
from supabase.httpx import create_async_client, create_client

if TYPE_CHECKING:
    from collections.abc import Callable

URL = "https://example.supabase.co"
KEY = "header.payload.signature"
DUNE = {"id": 1, "title": "Dune"}


class BooksRow(BaseModel):
    id: int
    title: str


class BooksInsert(TypedDict):
    title: str


class BooksUpdate(TypedDict, total=False):
    title: str


class Books:
    id = Column[BooksRow, int]("id")
    title = Column[BooksRow, str]("title")
    table = Table("books", BooksRow, insert_type=BooksInsert, update_type=BooksUpdate)


LIBRARY_BOOKS = Table(
    "books",
    BooksRow,
    insert_type=BooksInsert,
    update_type=BooksUpdate,
    schema="library",
)
SEARCH_BOOKS = FunctionCall.rows("search_books", BooksRow, arguments={"q": "dune"})
COUNT_BOOKS = FunctionCall.value("count_books", int)


def transport(
    requests: list[httpx.Request], answer: object = (DUNE,)
) -> httpx.MockTransport:
    def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=answer)

    return httpx.MockTransport(handler)


def test_sync_table_queries_a_typed_table() -> None:
    requests: list[httpx.Request] = []
    with SyncHttpxClient(transport=transport(requests)) as http_client:
        client = create_client(URL, KEY, http_client=http_client)
        builder = client.table(Books.table)
        assert_type(
            builder,
            TypedQueryBuilder[TableExecutor, BooksRow, BooksInsert, BooksUpdate],
        )
        books = builder.select().where(Books.id.eq(1)).execute()
    assert_type(books, list[BooksRow])
    assert books == [BooksRow(id=1, title="Dune")]
    (request,) = requests
    assert request.method == "GET"
    assert request.url.path == "/rest/v1/books"
    assert request.url.params["id"] == "eq.1"
    assert request.headers["apikey"] == KEY


async def test_async_table_queries_a_typed_table() -> None:
    requests: list[httpx.Request] = []
    async with (
        AsyncHttpxClient(transport=transport(requests)) as http_client,
        create_async_client(URL, KEY, http_client=http_client) as client,
    ):
        builder = client.table(Books.table)
        assert_type(
            builder,
            TypedQueryBuilder[AsyncTableExecutor, BooksRow, BooksInsert, BooksUpdate],
        )
        books = await builder.select().where(Books.id.eq(1)).execute()
    assert_type(books, list[BooksRow])
    assert books == [BooksRow(id=1, title="Dune")]
    (request,) = requests
    assert request.url.path == "/rest/v1/books"
    assert request.url.params["id"] == "eq.1"


def test_table_with_a_schema_queries_that_schema() -> None:
    requests: list[httpx.Request] = []
    with SyncHttpxClient(transport=transport(requests)) as http_client:
        client = create_client(URL, KEY, http_client=http_client)
        client.table(LIBRARY_BOOKS).select().execute()
    (request,) = requests
    assert request.headers["Accept-Profile"] == "library"


def test_table_of_a_name_returns_the_string_builder() -> None:
    requests: list[httpx.Request] = []
    with SyncHttpxClient(transport=transport(requests)) as http_client:
        client = create_client(URL, KEY, http_client=http_client)
        response = client.table("books").select("*").execute()
    assert response.data == [DUNE]


def test_sync_rpc_calls_a_typed_function() -> None:
    requests: list[httpx.Request] = []
    with SyncHttpxClient(transport=transport(requests)) as http_client:
        client = create_client(URL, KEY, http_client=http_client)
        builder = client.rpc(SEARCH_BOOKS)
        assert_type(
            builder, TypedFilterBuilder[TableExecutor, BooksRow, list[BooksRow]]
        )
        books = builder.where(Books.id.eq(1)).execute()
    assert_type(books, list[BooksRow])
    assert books == [BooksRow(id=1, title="Dune")]
    (request,) = requests
    assert request.method == "POST"
    assert request.url.path == "/rest/v1/rpc/search_books"
    assert request.url.params["id"] == "eq.1"
    assert request.read() == b'{"q":"dune"}'


async def test_async_rpc_calls_a_typed_function() -> None:
    requests: list[httpx.Request] = []
    async with (
        AsyncHttpxClient(transport=transport(requests, 3)) as http_client,
        create_async_client(URL, KEY, http_client=http_client) as client,
    ):
        builder = client.rpc(COUNT_BOOKS)
        assert_type(builder, TypedBuilder[AsyncTableExecutor, int | None])
        count = await builder.execute()
    assert_type(count, int | None)
    assert count == 3
    (request,) = requests
    assert request.url.path == "/rest/v1/rpc/count_books"


@pytest.mark.parametrize(
    "options",
    [{"params": {"q": "dune"}}, {"head": True}, {"count": "exact"}, {"get": True}],
)
def test_rpc_of_a_function_call_rejects_the_options_of_a_name(
    options: dict[str, Any],
) -> None:
    with create_client(URL, KEY) as client:
        rpc: Callable[..., object] = client.rpc
        with pytest.raises(TypeError, match="takes no params"):
            rpc(SEARCH_BOOKS, **options)
