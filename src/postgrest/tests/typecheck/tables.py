"""The table definition, the request value and the executors as the type
checkers see them.

`test_typecheck.py` runs mypy, pyright and pyrefly on this file and asserts
that each reports an error on every line marked `# error:` and on no other
line. The pyrefly check of the package excludes this directory.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Never, NotRequired, TypedDict

from httpx import AsyncClient, Client
from supabase_utils.http.adapters.httpx import AsyncHttpxSession, HttpxSession

from postgrest import (
    AsyncHttpTableExecutor,
    AsyncPostgrestClient,
    AsyncTableExecutor,
    Column,
    ComputedField,
    HttpTableExecutor,
    NullableColumn,
    SyncPostgrestClient,
    Table,
    TableExecutor,
    TableOperation,
    TableRequest,
    TableResult,
)


class BooksRow:
    pass


class BooksInsert(TypedDict):
    id: NotRequired[int]
    title: str


class BooksUpdate(TypedDict):
    title: NotRequired[str]


class AuthorsRow:
    pass


class Books:
    id = Column[BooksRow, int]("id")
    title = Column[BooksRow, str]("title")
    published_on = NullableColumn[BooksRow, datetime]("published_on")
    full_title = ComputedField[BooksRow, str]("full_title")
    table = Table[BooksRow, BooksInsert, BooksUpdate](
        "books",
        BooksRow,
        primary_key=(id,),
        computed_fields=(full_title,),
        schema="public",
    )


class Authors:
    id = Column[AuthorsRow, int]("id")
    full_name = ComputedField[AuthorsRow, str]("full_name")


view = Table[BooksRow, Never, Never]("books_view", BooksRow)
keyless = Table[BooksRow, BooksInsert, BooksUpdate]("books", BooksRow)

wrong_row = Table[BooksRow, BooksInsert, BooksUpdate]("books", AuthorsRow)  # error:
foreign_key = Table[BooksRow, BooksInsert, BooksUpdate](
    "books",
    BooksRow,
    primary_key=(Authors.id,),  # error:
)
nullable_key = Table[BooksRow, BooksInsert, BooksUpdate](
    "books",
    BooksRow,
    primary_key=(Books.published_on,),  # error:
)
foreign_field = Table[BooksRow, BooksInsert, BooksUpdate](
    "books",
    BooksRow,
    computed_fields=(Authors.full_name,),  # error:
)

select = TableRequest(
    table=Books.table,
    operation=TableOperation.SELECT,
    columns=(Books.id, Books.full_title),
    filter=Books.id.gt(1) & ~Books.published_on.is_null(),
    orderings=(Books.title.desc(), Books.id),
    on_conflict=(Books.title, Books.published_on),
)
call = TableRequest(table=view, operation=TableOperation.RPC, payload={"query": "x"})

sync_client = SyncPostgrestClient(
    "https://example.com", http_session=HttpxSession(client=Client())
)
async_client = AsyncPostgrestClient(
    "https://example.com", http_session=AsyncHttpxSession(client=AsyncClient())
)

sync_executor: TableExecutor = HttpTableExecutor(sync_client)
async_executor: AsyncTableExecutor = AsyncHttpTableExecutor(async_client)
result: TableResult = sync_executor.execute(select)

not_sync: TableExecutor = AsyncHttpTableExecutor(async_client)  # error:
not_async: AsyncTableExecutor = HttpTableExecutor(sync_client)  # error:
wrong_client = HttpTableExecutor(async_client)  # error:


@dataclass
class Logging:
    inner: TableExecutor

    def execute(self, request: TableRequest) -> TableResult:
        return self.inner.execute(request)


@dataclass
class AsyncLogging:
    inner: AsyncTableExecutor

    async def execute(self, request: TableRequest) -> TableResult:
        return await self.inner.execute(request)


wrapped: TableExecutor = Logging(HttpTableExecutor(sync_client))
wrapped_async: AsyncTableExecutor = AsyncLogging(AsyncHttpTableExecutor(async_client))
