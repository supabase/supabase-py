"""The tables of the typed query builder tests, declared by hand the way the
generator will declare them, over the schema of
`infra/supabase/migrations/20240102000000_typed_api.sql`."""

from __future__ import annotations

from datetime import date
from typing import Never, NotRequired, TypedDict

from pydantic import BaseModel, JsonValue

from postgrest import Column, ComputedField, NullableColumn, Table


class BooksRow(BaseModel):
    id: int
    title: str
    isbn: str | None = None
    pages: int
    published_on: date | None = None
    tags: list[str]
    metadata: dict[str, JsonValue] | None = None


class BooksInsert(TypedDict):
    id: NotRequired[int]
    title: str
    isbn: NotRequired[str | None]
    pages: NotRequired[int]
    published_on: NotRequired[date | None]
    tags: NotRequired[list[str]]
    metadata: NotRequired[dict[str, JsonValue] | None]


class BooksUpdate(TypedDict, total=False):
    id: int
    title: str
    isbn: str | None
    pages: int
    published_on: date | None
    tags: list[str]
    metadata: dict[str, JsonValue] | None


class Books:
    id = Column[BooksRow, int]("id")
    title = Column[BooksRow, str]("title")
    isbn = NullableColumn[BooksRow, str]("isbn")
    pages = Column[BooksRow, int]("pages")
    published_on = NullableColumn[BooksRow, date]("published_on")
    tags = Column[BooksRow, list[str]]("tags")
    metadata = NullableColumn[BooksRow, JsonValue]("metadata")
    title_upper = ComputedField[BooksRow, str]("title_upper")
    table = Table[BooksRow, BooksInsert, BooksUpdate](
        "books",
        BooksRow,
        primary_key=(id,),
        computed_fields=(title_upper,),
        schema="public",
    )


class BookTitlesRow(BaseModel):
    id: int
    title: str


class BookTitles:
    id = Column[BookTitlesRow, int]("id")
    title = Column[BookTitlesRow, str]("title")
    table = Table[BookTitlesRow, Never, Never]("book_titles", BookTitlesRow)


class PlacesRow(BaseModel):
    id: int
    name: str
    location: dict[str, JsonValue] | None = None


class Places:
    id = Column[PlacesRow, int]("id")
    name = Column[PlacesRow, str]("name")
    table = Table[PlacesRow, Never, Never]("places", PlacesRow, primary_key=(id,))
