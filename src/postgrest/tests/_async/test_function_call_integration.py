from datetime import date
from typing import Never

import pytest
from pydantic import ValidationError

from postgrest import AsyncPostgrestClient, FunctionCall
from tests.typed_schema import Books, BooksRow

DUNE = BooksRow(
    id=1,
    title="Dune",
    isbn="9780441013593",
    pages=412,
    published_on=date(1965, 8, 1),
    tags=["science fiction"],
    metadata={"awards": ["Hugo", "Nebula"]},
)


def books_with_pages(
    min_pages: int, *, read_only: bool = False
) -> FunctionCall[BooksRow, list[BooksRow]]:
    return FunctionCall.rows(
        "books_with_pages",
        BooksRow,
        arguments={"min_pages": min_pages},
        read_only=read_only,
    )


@pytest.mark.parametrize("read_only", [False, True])
async def test_a_set_returning_function_decodes_its_rows(
    postgrest_client: AsyncPostgrestClient, read_only: bool
) -> None:
    call = books_with_pages(1, read_only=read_only)

    rows = await postgrest_client.rpc(call).order(Books.id).execute()

    assert [row.id for row in rows] == [1, 2]
    assert rows[0] == DUNE


async def test_the_rows_of_a_function_take_filters_order_and_a_window(
    postgrest_client: AsyncPostgrestClient,
) -> None:
    rows = (
        await postgrest_client.rpc(books_with_pages(0))
        .where(Books.tags.contains(["science fiction"]))
        .order(Books.pages.desc())
        .range(1, 1)
        .execute()
    )

    assert [row.title for row in rows] == ["Neuromancer"]


async def test_the_rows_of_a_function_read_as_one_row(
    postgrest_client: AsyncPostgrestClient,
) -> None:
    call = postgrest_client.rpc(books_with_pages(0)).where(Books.id.eq(1))

    assert await call.single().execute() == DUNE
    assert await call.maybe_single().execute() == DUNE


async def test_the_rows_of_a_function_are_counted(
    postgrest_client: AsyncPostgrestClient,
) -> None:
    response = (
        await postgrest_client.rpc(books_with_pages(0)).limit(1).count().execute()
    )

    assert len(response.data) == 1
    assert response.count == 3


async def test_a_function_that_returns_one_row_decodes_it(
    postgrest_client: AsyncPostgrestClient,
) -> None:
    call = FunctionCall.value("book_by_id", BooksRow, arguments={"book_id": 1})

    assert await postgrest_client.rpc(call).execute() == DUNE


@pytest.mark.parametrize("read_only", [False, True])
async def test_a_function_that_returns_a_scalar_decodes_it(
    postgrest_client: AsyncPostgrestClient, read_only: bool
) -> None:
    def book_title(book_id: int) -> FunctionCall[Never, str | None]:
        return FunctionCall.value(
            "book_title", str, arguments={"book_id": book_id}, read_only=read_only
        )

    assert await postgrest_client.rpc(book_title(1)).execute() == "Dune"
    assert await postgrest_client.rpc(book_title(99)).execute() is None


async def test_a_scalar_of_another_type_raises(
    postgrest_client: AsyncPostgrestClient,
) -> None:
    call = FunctionCall.value("book_title", int, arguments={"book_id": 1})

    with pytest.raises(ValidationError):
        await postgrest_client.rpc(call).execute()
