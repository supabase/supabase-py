"""Projection models as the type checkers see them.

`test_typecheck.py` runs mypy, pyright and pyrefly on this file and asserts
that each reports an error on every line marked `# error:` and on no other
line. The pyrefly check of the package excludes this directory.
"""

from __future__ import annotations

from collections.abc import Awaitable
from typing import Any, assert_type

from httpx import AsyncClient, Client
from pydantic import BaseModel
from supabase_utils.http.adapters.httpx import AsyncHttpxSession, HttpxSession

from postgrest import (
    AsyncPostgrestClient,
    Column,
    SyncPostgrestClient,
    Table,
    ToOneRelation,
)


class BooksRow:
    pass


class AuthorsRow:
    pass


class Authors:
    name = Column[AuthorsRow, str]("name")
    table = Table[AuthorsRow, Any, Any]("authors", AuthorsRow)


class Books:
    id = Column[BooksRow, int]("id")
    title = Column[BooksRow, str]("title")
    author = ToOneRelation[BooksRow, AuthorsRow](
        "authors", AuthorsRow, target_table=lambda: Authors.table
    )
    table = Table[BooksRow, Any, Any]("books", BooksRow, relations=(author,))


class AuthorName(BaseModel):
    name: str


class BookCard(BaseModel):
    id: int
    title: str
    author: AuthorName


class NotAModel:
    pass


sync_client = SyncPostgrestClient(
    "https://example.com", http_session=HttpxSession(client=Client())
)
async_client = AsyncPostgrestClient(
    "https://example.com", http_session=AsyncHttpxSession(client=AsyncClient())
)
books = sync_client.table(Books.table)

assert_type(books.select_as(BookCard).execute(), list[BookCard])
assert_type(books.select_as(BookCard).single().execute(), BookCard)
assert_type(books.select_as(BookCard).maybe_single().execute(), BookCard | None)
assert_type(
    books.select_as(BookCard).where(Books.id.eq(1)).order(Books.title).execute(),
    list[BookCard],
)
assert_type(
    books.insert({"title": "Dune"}).select_as(BookCard).single().execute(), BookCard
)
assert_type(
    async_client.table(Books.table).select_as(BookCard).execute(),
    Awaitable[list[BookCard]],
)
for card in books.select_as(BookCard).execute():
    assert_type(card.author.name, str)

books.select_as(NotAModel)  # error:
books.select_as(BookCard).where(Authors.name.eq("Frank"))  # error:
