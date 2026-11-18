"""Embedded relations and their scopes as the type checkers see them.

`test_typecheck.py` runs mypy, pyright and pyrefly on this file and asserts
that each reports an error on every line marked `# error:` and on no other
line. The pyrefly check of the package excludes this directory.
"""

from __future__ import annotations

from datetime import date
from typing import Any, assert_type

from httpx import AsyncClient, Client
from supabase_utils.http.adapters.httpx import AsyncHttpxSession, HttpxSession

from postgrest import (
    AsyncPostgrestClient,
    AsyncTableExecutor,
    Column,
    Embed,
    EmbeddedCount,
    EmbeddedScope,
    Filter,
    NullableColumn,
    PartialRow,
    SyncPostgrestClient,
    Table,
    ToManyRelation,
    ToOneRelation,
    TypedFilterBuilder,
)


class AuthorsRow:
    pass


class BooksRow:
    pass


class ReviewsRow:
    pass


class Authors:
    id = Column[AuthorsRow, int]("id")
    name = Column[AuthorsRow, str]("name")
    books = ToManyRelation[AuthorsRow, BooksRow]("books", BooksRow)
    table = Table[AuthorsRow, Any, Any]("authors", AuthorsRow)


class Books:
    id = Column[BooksRow, int]("id")
    title = Column[BooksRow, str]("title")
    published_on = NullableColumn[BooksRow, date]("published_on")
    author = ToOneRelation[BooksRow, AuthorsRow](
        "authors", AuthorsRow, constraint="books_author_id_fkey"
    )
    reviews = ToManyRelation[BooksRow, ReviewsRow]("reviews", ReviewsRow)
    table = Table[BooksRow, Any, Any]("books", BooksRow)


class Reviews:
    rating = Column[ReviewsRow, int]("rating")


sync_client = SyncPostgrestClient(
    "https://example.com", http_session=HttpxSession(client=Client())
)
async_client = AsyncPostgrestClient(
    "https://example.com", http_session=AsyncHttpxSession(client=AsyncClient())
)
books = sync_client.table(Books.table)
authors = async_client.table(Authors.table)

assert_type(Books.author.select([Authors.name]), Embed[BooksRow, AuthorsRow])
assert_type(Authors.books.select(), Embed[AuthorsRow, BooksRow])
assert_type(Authors.books.count(), EmbeddedCount[AuthorsRow])
assert_type(Books.author.is_null(), Filter[BooksRow])
Books.author.select([Books.title])  # error:
Books.author.count()  # error:

rows = books.select_only(
    [
        Books.title,
        Books.author.select([Authors.name]),
        Books.reviews.select(),
        Books.reviews.count(),
    ]
).execute()
row = rows[0]
author = row[Books.author]
assert_type(author, PartialRow[AuthorsRow] | None)
assert_type(row[Books.reviews], list[PartialRow[ReviewsRow]])
assert_type(row[Books.reviews.count()], int)
if author is not None:
    assert_type(author[Authors.name], str)
    author[Books.title]  # error:
row[Authors.books]  # error:
books.select_only([Authors.books.select()])  # error:

nested = authors.select_only(
    [Authors.books.select([Books.title, Books.author.select([Authors.id])])]
)
scoped: TypedFilterBuilder[AsyncTableExecutor, AuthorsRow, list[PartialRow[AuthorsRow]]]
scoped = nested.embedded(
    Authors.books,
    lambda scope: scope.where(Books.title.eq("Dune"))
    .order(Books.published_on.desc())
    .range(0, 9)
    .requiring(Books.author, lambda inner: inner.where(Authors.id.gt(1)))
    .embedded(Books.reviews, lambda inner: inner.limit(3)),
)
nested.requiring(Authors.books)
nested.embedded(Authors.books, lambda scope: scope.where(Authors.id.eq(1)))  # error:
nested.embedded(Books.author, lambda scope: scope)  # error:
nested.requiring(Authors.books, lambda scope: scope.order(Authors.name))  # error:
books.select().where(Books.author.is_null() | Books.title.eq("Dune"))
books.select().where(Authors.books.is_null())  # error:

scope = EmbeddedScope(Authors.books)
assert_type(scope, EmbeddedScope[BooksRow])
assert_type(scope.where(Books.id.eq(1)).limit(1), EmbeddedScope[BooksRow])
scope.embedded(Authors.books, lambda inner: inner)  # error:
