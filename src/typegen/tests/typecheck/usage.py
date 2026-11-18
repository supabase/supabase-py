"""The generated module of the shared fixture as the type checkers see it,
through every method of the typed query builder.

`test_typecheck.py` runs mypy, pyright and pyrefly on this file and the
goldens, and asserts that each reports an error on every line marked
`# error:` and on no other line.
"""

from __future__ import annotations

import datetime
from typing import Never, assert_type

from httpx import AsyncClient, Client
from postgrest import (
    AsyncPostgrestClient,
    CountedResponse,
    FunctionCall,
    PartialRow,
    SyncPostgrestClient,
)
from supabase_utils.http.adapters.httpx import AsyncHttpxSession, HttpxSession

from tests.goldens.supabase_schema import (
    Authors,
    AuthorsRow,
    AuthorStats,
    AuthorStatsRow,
    BookPrices,
    Books,
    BooksInsert,
    BooksRow,
    BookSubmissions,
    BookSummaries,
    BooksUpdate,
    BookTitles,
    BookTitlesRow,
    Functions,
    InventoryCondition,
    InventoryStock,
    InventoryStockRow,
    Mood,
)

client = SyncPostgrestClient(
    "https://example.com", http_session=HttpxSession(client=Client())
)
async_client = AsyncPostgrestClient(
    "https://example.com", http_session=AsyncHttpxSession(client=AsyncClient())
)
books = client.table(Books.table)

assert_type(books.select().execute(), list[BooksRow])
assert_type(
    books.select()
    .where(
        (Books.mood.eq(Mood.HAPPY) | Books.title.like("%Python%"))
        & ~Books.published_on.is_null()
        & Books.tags.contains(["fiction"])
        & Books.created_at.gte(datetime.datetime(2024, 1, 1, tzinfo=datetime.UTC))
    )
    .order(Books.created_at.desc())
    .limit(10)
    .range(0, 9)
    .execute(),
    list[BooksRow],
)
assert_type(books.select().where(Books.id.eq(1)).single().execute(), BooksRow)
assert_type(books.select().maybe_single().execute(), BooksRow | None)
assert_type(books.select().count().execute(), CountedResponse[list[BooksRow]])
assert_type(books.count().where(Books.in_print.eq(True)).execute(), int)
books.select().where(Books.id.eq("one"))  # error: an int column
books.select().where(Books.mood.eq("happy"))  # error: a Mood column
books.select().where(Authors.id.eq(1))  # error: a column of another table
books.select().where(Books.title.is_null())  # error: title is NOT NULL

partial = books.select_only(
    [
        Books.title,
        Books.title_upper,
        Books.mood_or_default,
        Books.authors.select([Authors.name]),
    ]
).execute()[0]
assert_type(partial, PartialRow[BooksRow])
assert_type(partial[Books.title], str)
assert_type(partial[Books.title_upper], str | None)
assert_type(partial[Books.mood_or_default], Mood | None)
author = partial[Books.authors]
assert_type(author, PartialRow[AuthorsRow] | None)
assert_type(None if author is None else author[Authors.name], str | None)
recent = client.table(Authors.table).select_only([Authors.recent_books.select()])
assert_type(recent.execute()[0][Authors.recent_books], list[PartialRow[BooksRow]])
assert_type(
    client.table(Authors.table)
    .select_only([Authors.name, Authors.latest_book.select([Books.title])])
    .execute()[0][Authors.latest_book],
    PartialRow[BooksRow] | None,
)

new_book: BooksInsert = {"title": "Dune", "author_id": 1, "mood": Mood.VERY_HAPPY}
assert_type(books.insert(new_book).execute(), None)
assert_type(books.insert([new_book]).select().execute(), list[BooksRow])
assert_type(books.upsert(new_book, on_conflict=[Books.id]).execute(), None)
changes: BooksUpdate = {"published_on": datetime.date(2024, 5, 1), "price": None}
assert_type(books.update(changes).where(Books.id.eq(1)).execute(), None)
assert_type(books.delete().where(Books.id.eq(1)).select().execute(), list[BooksRow])
books.insert({"title": "Dune"})  # error: author_id is required
books.insert({"title": "Dune", "author_id": 1, "rating": "5"})  # error: a float
books.update({"pages": 1})  # error: no such column

stock = client.table(InventoryStock.table)
assert_type(stock.select().execute(), list[InventoryStockRow])
stock.insert({"book_id": 1, "copy_id": 1, "condition": InventoryCondition.USED})
stock.insert({"book_id": 1, "copy_id": 1, "id": 2})  # error: id is always generated

stats = client.table(AuthorStats.table)
assert_type(stats.select().execute(), list[AuthorStatsRow])
stats.insert({"author_id": 1})  # error: a view that is not insertable
stats.update({"author_id": 1})  # error: a view that is not updatable
client.table(BookPrices.table).update({"price": 1.0}).where(BookPrices.id.eq(1))
client.table(BookPrices.table).update({"discounted_price": 1.0})  # error: computed
client.table(BookSubmissions.table).insert({"title": "x", "author_name": "y"})
client.table(BookSubmissions.table).update({"title": "x"})  # error: insert only
client.table(BookSummaries.table).insert({"title": "x"})  # error: materialized

search = client.rpc(Functions.search_books(query="dune", mood=Mood.HAPPY))
assert_type(
    search.where(Books.price.lt(10.0)).order(Books.title).limit(5).execute(),
    list[BooksRow],
)
assert_type(
    client.rpc(Functions.book_titles(read_only=True))
    .where(BookTitles.id.gt(1) & ~BookTitles.author_name.is_null())
    .execute(),
    list[BookTitlesRow],
)
assert_type(client.rpc(Functions.book_titles()).execute(), list[BookTitlesRow])
assert_type(client.rpc(Functions.book_by_id(book_id=1)).execute(), BooksRow | None)
assert_type(client.rpc(Functions.count_books()).execute(), int | None)
assert_type(
    client.rpc(Functions.publication_dates(author_id=1)).execute(),
    list[datetime.date] | None,
)
assert_type(client.rpc(Functions.touch_book(book_id=1)).execute(), None)
assert_type(client.rpc(Functions.echo({"hello": ["world"]})).execute(), object)
assert_type(
    Functions.inventory_restock(amount=1, stock_id=2), FunctionCall[Never, int | None]
)
Functions.search_books()  # error: query is required
Functions.search_books(query=1)  # error: query is text
Functions.books_of(author_name="x")  # error: the other overload has its own method
Functions.touch_book(book_id=1, read_only=True)  # error: volatile, no read_only
client.rpc(Functions.count_books()).where(Books.id.eq(1))  # error: a value


async def main() -> None:
    async_books = async_client.table(Books.table)
    assert_type(await async_books.select().execute(), list[BooksRow])
    assert_type(
        await async_client.rpc(Functions.search_books(query="x")).execute(),
        list[BooksRow],
    )
