"""The tables of the typed query builder tests, declared by hand the way the
generator will declare them, over the schema of
`infra/supabase/migrations/20240102000000_typed_api.sql` and
`20240106000000_relations.sql`."""

from __future__ import annotations

from datetime import date
from typing import Any, Never, NotRequired, TypedDict

from pydantic import BaseModel, JsonValue

from postgrest import (
    Column,
    ComputedField,
    NullableColumn,
    Table,
    ToManyRelation,
    ToOneRelation,
)


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
    next_publication = ComputedField[BooksRow, date]("next_publication", date)
    table = Table(
        "books",
        BooksRow,
        insert_type=BooksInsert,
        update_type=BooksUpdate,
        primary_key=(id,),
        computed_fields=(title_upper, next_publication),
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


class AuthorsRow(BaseModel):
    id: int
    name: str
    born_on: date | None = None


class NovelsRow(BaseModel):
    id: int
    title: str
    author_id: int | None = None


class Authors:
    id = Column[AuthorsRow, int]("id")
    name = Column[AuthorsRow, str]("name")
    born_on = NullableColumn[AuthorsRow, date]("born_on")
    novels = ToManyRelation[AuthorsRow, NovelsRow](
        "novels", NovelsRow, target_table=lambda: Novels.table
    )
    table = Table[AuthorsRow, Never, Never](
        "authors", AuthorsRow, primary_key=(id,), relations=(novels,)
    )


class Novels:
    id = Column[NovelsRow, int]("id")
    title = Column[NovelsRow, str]("title")
    author_id = NullableColumn[NovelsRow, int]("author_id")
    author = ToOneRelation[NovelsRow, AuthorsRow](
        "authors",
        AuthorsRow,
        constraint="novels_author_id_fkey",
        target_table=lambda: Authors.table,
    )
    table = Table[NovelsRow, Never, dict[str, Any]](
        "novels", NovelsRow, primary_key=(id,), relations=(author,)
    )
