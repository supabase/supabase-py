"""The typed query builder as the type checkers see it.

`test_typecheck.py` runs mypy, pyright and pyrefly on this file and asserts
that each reports an error on every line marked `# error:` and on no other
line. The pyrefly check of the package excludes this directory.
"""

from __future__ import annotations

from datetime import date
from typing import Any, Never, NotRequired, TypedDict, assert_type

from httpx import AsyncClient, Client
from supabase_utils.http.adapters.httpx import AsyncHttpxSession, HttpxSession
from supabase_utils.http.io import AsyncHttpIO, SyncHttpIO
from supabase_utils.types import JSON

from postgrest import (
    AsyncPostgrestClient,
    AsyncTableExecutor,
    Column,
    ComputedField,
    CountedResponse,
    CountMethod,
    NullableColumn,
    PartialRow,
    SyncPostgrestClient,
    Table,
    TableExecutor,
    TypedQueryBuilder,
)
from postgrest.request_builder import RequestBuilder


class BooksRow:
    pass


class BooksInsert(TypedDict):
    id: NotRequired[int]
    title: str
    published_on: NotRequired[date | None]


class BooksUpdate(TypedDict, total=False):
    title: str
    published_on: date | None


class AuthorsRow:
    pass


class Books:
    id = Column[BooksRow, int]("id")
    title = Column[BooksRow, str]("title")
    published_on = NullableColumn[BooksRow, date]("published_on")
    full_title = ComputedField[BooksRow, str]("full_title")
    next_publication = ComputedField[BooksRow, date]("next_publication", date)
    table = Table[BooksRow, BooksInsert, BooksUpdate](
        "books",
        BooksRow,
        primary_key=(id,),
        computed_fields=(full_title, next_publication),
    )


class Authors:
    id = Column[AuthorsRow, int]("id")
    name = Column[AuthorsRow, str]("name")


class BookTitlesRow:
    pass


class BookTitles:
    id = Column[BookTitlesRow, int]("id")
    title = Column[BookTitlesRow, str]("title")
    table = Table[BookTitlesRow, Never, Never]("book_titles", BookTitlesRow)


sync_client = SyncPostgrestClient(
    "https://example.com", http_session=HttpxSession(client=Client())
)
async_client = AsyncPostgrestClient(
    "https://example.com", http_session=AsyncHttpxSession(client=AsyncClient())
)

books = sync_client.table(Books.table)
assert_type(books, TypedQueryBuilder[TableExecutor, BooksRow, BooksInsert, BooksUpdate])
assert_type(sync_client.table("books"), RequestBuilder[SyncHttpIO])
assert_type(async_client.table("books"), RequestBuilder[AsyncHttpIO])

assert_type(books.select().execute(), list[BooksRow])
assert_type(
    books.select()
    .where(Books.id.gt(1) & ~Books.published_on.is_null())
    .where(Books.full_title.eq("x"))
    .order(Books.title.desc().nulls_last())
    .order(Books.id)
    .limit(10)
    .range(0, 9)
    .strip_nulls()
    .dry_run()
    .max_affected(10)
    .retry(False)
    .request_timeout(3)
    .execute(),
    list[BooksRow],
)
books.select().where(Authors.id.eq(1))  # error:
books.select().order(Authors.name)  # error:
books.select().where(Books.id.eq("one"))  # error:

assert_type(books.select().single().execute(), BooksRow)
assert_type(books.select().maybe_single().execute(), BooksRow | None)
assert_type(books.select().count().execute(), CountedResponse[list[BooksRow]])
assert_type(books.select().count(CountMethod.planned).execute().count, int)
assert_type(books.select().single().count().execute().data, BooksRow)
assert_type(books.select().head().execute(), None)
assert_type(books.select().csv().execute(), str)
assert_type(books.select().csv().order(Books.id).execute(), str)
assert_type(books.select().explain().execute(), str)
assert_type(books.select().explain(analyze=True, format="text").execute(), str)
assert_type(books.select().explain(format="json").execute(), JSON)
assert_type(books.select().geojson().execute(), dict[str, JSON])
assert_type(books.count().execute(), int)
assert_type(books.count(CountMethod.estimated).where(Books.id.gt(1)).execute(), int)
books.select().csv().where(Books.id.eq(1))  # error:
books.select().single().single()  # error:
books.count().order(Books.id)  # error:

partial = books.select_only([Books.id, Books.title, Books.published_on]).execute()
assert_type(partial, list[PartialRow[BooksRow]])
row = partial[0]
assert_type(row[Books.id], int)
assert_type(row[Books.title], str)
assert_type(row[Books.published_on], date | None)
assert_type(row[Books.full_title], str | None)
assert_type(row[Books.next_publication], date | None)
ComputedField[BooksRow, date]("next_publication", str)  # error:
assert_type(row[Column("legacy")], Any)
assert_type(row.to_row(), BooksRow)
row[Authors.id]  # error:
books.select_only([Books.id, Authors.name])  # error:

assert_type(books.insert({"title": "x"}).execute(), None)
assert_type(books.insert([{"title": "x"}, {"title": "y", "id": 2}]).execute(), None)
assert_type(books.insert({"title": "x"}).select().execute(), list[BooksRow])
assert_type(books.insert({"title": "x"}).select().single().execute(), BooksRow)
assert_type(
    books.insert({"title": "x"}).select_only([Books.id]).execute(),
    list[PartialRow[BooksRow]],
)
assert_type(books.insert({"title": "x"}).count().execute(), CountedResponse[None])
books.insert({"title": 1})  # error:
books.insert({"name": "x"})  # error:
books.insert({"title": "x"}).single()  # error:
books.insert({"title": "x"}).where(Books.id.eq(1))  # error:
books.insert({"title": "x"}).csv()  # error:
books.insert({"title": "x"}).geojson()  # error:
books.select().single().csv()  # error:

assert_type(
    books.upsert(
        {"title": "x"},
        on_conflict=[Books.title, Books.published_on],
        ignore_duplicates=True,
    ).execute(),
    None,
)
books.upsert({"title": "x"}, on_conflict=[Authors.id])  # error:

assert_type(books.update({"title": "x"}).where(Books.id.eq(1)).execute(), None)
assert_type(books.update({"title": "x"}).all().select().execute(), list[BooksRow])
assert_type(
    books.update({"title": "x"}).where(Books.id.eq(1)).max_affected(1).execute(),
    None,
)
books.update({"title": 1})  # error:
books.update({"title": "x"}).execute()  # error:
books.update({"title": "x"}).where(Authors.id.eq(1))  # error:

assert_type(books.delete().where(Books.id.eq(1)).execute(), None)
assert_type(books.delete().all().select().execute(), list[BooksRow])
books.delete().execute()  # error:

titles = sync_client.table(BookTitles.table)
assert_type(titles.select().execute(), list[BookTitlesRow])
titles.insert({"title": "x"})  # error:
titles.upsert({"title": "x"})  # error:
titles.update({"title": "x"})  # error:
titles.delete().all()  # error:
titles.delete().where(BookTitles.id.eq(1))  # error:


async def main() -> None:
    async_books = async_client.table(Books.table)
    assert_type(
        async_books,
        TypedQueryBuilder[AsyncTableExecutor, BooksRow, BooksInsert, BooksUpdate],
    )
    assert_type(await async_books.select().execute(), list[BooksRow])
    assert_type(await async_books.select().single().execute(), BooksRow)
    assert_type(await async_books.count().execute(), int)
    assert_type(await async_books.insert({"title": "x"}).execute(), None)
    assert_type(
        await async_books.select_only([Books.id]).execute(),
        list[PartialRow[BooksRow]],
    )
    await books.select().execute()  # error:
