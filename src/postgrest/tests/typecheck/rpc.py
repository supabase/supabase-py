"""The RPC builders as the type checkers see them.

`test_typecheck.py` runs mypy, pyright and pyrefly on this file and asserts
that each reports an error on every line marked `# error:` and on no other
line. The pyrefly check of the package excludes this directory.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Never, assert_type

from supabase_utils.http.io import AsyncHttpIO, SyncHttpIO

from postgrest import (
    AsyncTableExecutor,
    Column,
    CountedResponse,
    FunctionCall,
    TableExecutor,
    TextAPIResponse,
    TypedBuilder,
    TypedFilterBuilder,
)
from postgrest.request_builder import RPCCountRequestBuilder, TextRequestBuilder
from postgrest.types import CountMethod

if TYPE_CHECKING:
    from postgrest import AsyncPostgrestClient, SyncPostgrestClient


class BooksRow:
    pass


class AuthorsRow:
    pass


book_id = Column[BooksRow, int]("id")
author_id = Column[AuthorsRow, int]("id")
search_books = FunctionCall.rows("search_books", BooksRow, arguments={"q": "x"})
count_books = FunctionCall.value("count_books", int)
latest_book = FunctionCall.value("latest_book", BooksRow, read_only=True)


def sync_rpc(client: SyncPostgrestClient) -> None:
    query = client.rpc("fn", {}).csv()
    assert_type(query, TextRequestBuilder[SyncHttpIO])
    assert_type(query.execute(), TextAPIResponse)
    counted = client.rpc("fn", {}, count=CountMethod.exact).csv()
    assert_type(counted, TextRequestBuilder[SyncHttpIO])
    assert_type(
        client.rpc("fn", {}, count=CountMethod.exact, head=True),
        RPCCountRequestBuilder[SyncHttpIO],
    )


async def async_rpc(client: AsyncPostgrestClient) -> None:
    query = client.rpc("fn", {}).csv()
    assert_type(query, TextRequestBuilder[AsyncHttpIO])
    assert_type(await query.execute(), TextAPIResponse)


def rejected(client: SyncPostgrestClient) -> None:
    client.rpc("fn", {}).csv().strip_nulls()  # error: nothing chains after csv()
    client.rpc("fn", {}).csv().eq("id", 1)  # error: nothing chains after csv()
    client.rpc("fn", {}, head=True, count=None, get=False).csv()  # error: no csv()
    client.rpc("fn", {}, count=CountMethod.exact, head=True).csv()  # error: no csv()


def sync_typed_rpc(client: SyncPostgrestClient) -> None:
    assert_type(search_books, FunctionCall[BooksRow, list[BooksRow]])
    assert_type(count_books, FunctionCall[Never, int | None])
    rows = client.rpc(search_books)
    assert_type(rows, TypedFilterBuilder[TableExecutor, BooksRow, list[BooksRow]])
    assert_type(rows.where(book_id.gt(1)).order(book_id).execute(), list[BooksRow])
    assert_type(rows.limit(2).range(0, 1).single().execute(), BooksRow)
    assert_type(rows.maybe_single().execute(), BooksRow | None)
    assert_type(rows.count().execute(), CountedResponse[list[BooksRow]])
    value = client.rpc(count_books)
    assert_type(value, TypedBuilder[TableExecutor, int | None])
    assert_type(value.execute(), int | None)
    assert_type(client.rpc(latest_book).execute(), BooksRow | None)


async def async_typed_rpc(client: AsyncPostgrestClient) -> None:
    rows = client.rpc(search_books)
    assert_type(rows, TypedFilterBuilder[AsyncTableExecutor, BooksRow, list[BooksRow]])
    assert_type(await rows.where(book_id.eq(1)).execute(), list[BooksRow])
    assert_type(await client.rpc(count_books).execute(), int | None)


def rejected_typed(client: SyncPostgrestClient) -> None:
    client.rpc(search_books).where(author_id.eq(1))  # error: filter on another row
    client.rpc(count_books).where(book_id.eq(1))  # error: a value has no rows
    client.rpc(count_books).single()  # error: a value has no rows
    client.rpc(search_books, {})  # error: a call takes no params
    FunctionCall.rows("fn", BooksRow, arguments={"q": object()})  # error: not JSON
