from dataclasses import dataclass, field
from datetime import date
from typing import Annotated, Any

import pytest
from pydantic import AliasChoices, BaseModel, ConfigDict, Field, JsonValue

from postgrest import (
    Column,
    ComputedField,
    NullableColumn,
    Table,
    TableRequest,
    TableResult,
    ToManyRelation,
    ToOneRelation,
    TypedQueryBuilder,
)
from postgrest._projection import _declared_projection
from postgrest.table_executor import _render


class AuthorsRow(BaseModel):
    id: int
    name: str
    born_on: date | None = None


class NovelsRow(BaseModel):
    id: int
    title: Annotated[str, Field(max_length=200)]
    author_id: int | None = None


class ReviewsRow(BaseModel):
    id: int
    rating: int


class Authors:
    id = Column[AuthorsRow, int]("id")
    name = Column[AuthorsRow, str]("name")
    novels = ToManyRelation[AuthorsRow, NovelsRow](
        "novels", NovelsRow, target_table=lambda: Novels.table
    )
    table = Table("authors", AuthorsRow, primary_key=(id,), relations=(novels,))


class Novels:
    id = Column[NovelsRow, int]("id")
    title = Column[NovelsRow, str]("title")
    author_id = NullableColumn[NovelsRow, int]("author_id")
    title_upper = ComputedField[NovelsRow, str]("title_upper", str)
    word_count = ComputedField[NovelsRow, Any]("word_count")
    author = ToOneRelation[NovelsRow, AuthorsRow](
        "authors",
        AuthorsRow,
        constraint="novels_author_id_fkey",
        target_table=lambda: Authors.table,
    )
    editor = ToOneRelation[NovelsRow, AuthorsRow](
        "authors", AuthorsRow, constraint="novels_editor_id_fkey", alias="editor"
    )
    translator = ToOneRelation[NovelsRow, AuthorsRow](
        "authors", AuthorsRow, constraint="novels_translator_id_fkey"
    )
    reviews = ToManyRelation[NovelsRow, ReviewsRow]("reviews", ReviewsRow)
    table = Table[NovelsRow, dict[str, Any], dict[str, Any]](
        "novels",
        NovelsRow,
        primary_key=(id,),
        computed_fields=(title_upper, word_count),
        relations=(author, editor, translator, reviews),
    )


@dataclass
class Recording:
    result: TableResult = field(default_factory=TableResult)
    requests: list[TableRequest] = field(default_factory=list)

    def execute(self, request: TableRequest) -> TableResult:
        self.requests.append(request)
        return self.result


def novels(
    result: TableResult | None = None,
) -> tuple[
    Recording, TypedQueryBuilder[Any, NovelsRow, dict[str, Any], dict[str, Any]]
]:
    executor = Recording(result or TableResult(data=[]))
    return executor, TypedQueryBuilder(Novels.table, executor)


def select_list(
    model: type[BaseModel], table: Table[Any, Any, Any] = Novels.table
) -> str | None:
    executor = Recording(TableResult(data=[]))
    TypedQueryBuilder(table, executor).select_as(model).execute()
    (request,) = executor.requests
    return _render(request).query.get("select")


class AuthorName(BaseModel):
    name: str


class EarlyCard(BaseModel):
    id: int
    author: "LateAuthor"


class LateAuthor(BaseModel):
    name: str


class Shadowed:
    author = ToOneRelation[NovelsRow, AuthorsRow](
        "authors", AuthorsRow, constraint="novels_author_id_fkey"
    )
    editor = ToOneRelation[NovelsRow, AuthorsRow](
        "authors", AuthorsRow, constraint="novels_editor_id_fkey", alias="author"
    )
    table = Table[Any, Any, Any]("novels", NovelsRow, relations=(author, editor))


class TestSelectList:
    def test_a_flat_model_selects_its_fields(self) -> None:
        class NovelTitle(BaseModel):
            id: int
            title: str

        assert select_list(NovelTitle) == "id,title"

    def test_an_alias_names_the_column(self) -> None:
        class NovelTitle(BaseModel):
            key: int = Field(alias="id")
            heading: str = Field(alias="title")

        assert select_list(NovelTitle) == "id,title"

    def test_a_field_matched_by_name_reads_the_column_under_its_alias(
        self,
    ) -> None:
        class NovelTitle(BaseModel):
            title: str = Field(alias="heading")

        _, builder = novels(TableResult(data=[{"title": "Dune"}]))

        assert select_list(NovelTitle) == "title"
        assert builder.select_as(NovelTitle).execute() == [NovelTitle(heading="Dune")]

    def test_a_model_that_validates_by_name_reads_the_field_name(self) -> None:
        class NovelTitle(BaseModel):
            model_config = ConfigDict(validate_by_alias=False, validate_by_name=True)
            title: str = Field(alias="heading")

        _, builder = novels(TableResult(data=[{"title": "Dune"}]))

        assert builder.select_as(NovelTitle).execute() == [NovelTitle(title="Dune")]

    def test_a_model_that_validates_by_name_selects_its_alias_first(self) -> None:
        class NovelAuthor(BaseModel):
            model_config = ConfigDict(validate_by_alias=False, validate_by_name=True)
            id: int | None = Field(alias="author_id")

        _, builder = novels(TableResult(data=[{"author_id": 3}]))

        assert select_list(NovelAuthor) == "author_id"
        assert builder.select_as(NovelAuthor).execute() == [NovelAuthor(id=3)]

    def test_a_forward_reference_is_resolved_first(self) -> None:
        assert select_list(EarlyCard) == "id,authors!novels_author_id_fkey(name)"

    def test_a_computed_field_is_selected_by_name(self) -> None:
        class NovelTitle(BaseModel):
            title_upper: str | None
            word_count: int

        assert select_list(NovelTitle) == "title_upper,word_count"

    def test_a_nested_model_embeds_a_to_one_relation_under_the_field(self) -> None:
        class NovelCard(BaseModel):
            id: int
            author: AuthorName | None

        assert select_list(NovelCard) == ("id,authors!novels_author_id_fkey(name)")

    def test_a_field_named_after_the_response_key_needs_no_alias(self) -> None:
        class NovelCard(BaseModel):
            editor: AuthorName

        assert select_list(NovelCard) == "editor:authors!novels_editor_id_fkey(name)"

    def test_a_list_of_models_embeds_a_to_many_relation(self) -> None:
        class Rating(BaseModel):
            rating: int

        class NovelCard(BaseModel):
            reviews: list[Rating]

        assert select_list(NovelCard) == "reviews(rating)"

    def test_embeds_nest_through_the_target_table(self) -> None:
        class NovelTitle(BaseModel):
            title: str
            author: AuthorName

        class AuthorCard(BaseModel):
            name: str
            novels: list[NovelTitle]

        assert select_list(AuthorCard, Authors.table) == (
            "name,novels(title,authors!novels_author_id_fkey(name))"
        )

    def test_the_rows_decode_into_the_model(self) -> None:
        class NovelCard(BaseModel):
            id: int
            author: AuthorName | None

        _, builder = novels(
            TableResult(
                data=[
                    {"id": 1, "authors": {"name": "Frank Herbert"}},
                    {"id": 4, "authors": None},
                ]
            )
        )

        assert builder.select_as(NovelCard).execute() == [
            NovelCard(id=1, author=AuthorName(name="Frank Herbert")),
            NovelCard(id=4, author=None),
        ]

    def test_nested_rows_are_keyed_for_their_models(self) -> None:
        class NovelTitle(BaseModel):
            heading: str = Field(alias="title")
            author: AuthorName

        class AuthorCard(BaseModel):
            novels: list[NovelTitle]

        executor = Recording(
            TableResult(
                data=[
                    {
                        "novels": [
                            {"title": "Dune", "authors": {"name": "Frank Herbert"}}
                        ]
                    }
                ]
            )
        )

        cards = (
            TypedQueryBuilder(Authors.table, executor).select_as(AuthorCard).execute()
        )

        assert cards == [
            AuthorCard(
                novels=[
                    NovelTitle(title="Dune", author=AuthorName(name="Frank Herbert"))
                ]
            )
        ]

    def test_an_embed_can_be_scoped_and_filtered(self) -> None:
        class NovelCard(BaseModel):
            id: int
            author: AuthorName

        executor, builder = novels()

        builder.select_as(NovelCard).requiring(Novels.author).where(
            ~Novels.author.is_null()
        ).execute()

        (request,) = executor.requests
        rendered = _render(request).query
        assert rendered.get("select") == "id,authors!novels_author_id_fkey!inner(name)"
        assert rendered.get("authors") == "not.is.null"

    def test_nested_any_matches_any_type(self) -> None:
        class TaggedRow(BaseModel):
            tags: list[str] | None
            metadata: dict[str, JsonValue]

        class Tagged(BaseModel):
            tags: list[Any] | None
            metadata: dict[str, Any]

        assert select_list(Tagged, Table("tagged", TaggedRow)) == "tags,metadata"

    def test_single_decodes_one_model(self) -> None:
        class NovelTitle(BaseModel):
            title: str

        _, builder = novels(TableResult(data={"title": "Dune"}))

        assert builder.select_as(NovelTitle).single().execute() == NovelTitle(
            title="Dune"
        )

    def test_a_write_returns_the_affected_rows_as_models(self) -> None:
        class NovelTitle(BaseModel):
            title: str

        executor, builder = novels(TableResult(data=[{"title": "Dune"}]))

        rows = builder.delete().where(Novels.id.eq(1)).select_as(NovelTitle).execute()

        assert rows == [NovelTitle(title="Dune")]
        (request,) = executor.requests
        assert request.returning
        assert _render(request).query.get("select") == "title"

    def test_the_check_runs_once_per_table_and_model(self) -> None:
        class NovelTitle(BaseModel):
            title: str

        _declared_projection.cache_clear()
        select_list(NovelTitle)
        select_list(NovelTitle)

        assert _declared_projection.cache_info().hits == 1

    def test_equal_tables_keep_their_own_projection(self) -> None:
        class NovelTitle(BaseModel):
            title: str

        _declared_projection.cache_clear()
        select_list(NovelTitle, Table("novels", NovelsRow))
        select_list(NovelTitle, Table("novels", NovelsRow))

        assert _declared_projection.cache_info().misses == 2


class TestRejections:
    def problems(
        self, model: type[BaseModel], table: Table[Any, Any, Any] = Novels.table
    ) -> list[str]:
        _, builder = novels()
        with pytest.raises(TypeError) as raised:
            TypedQueryBuilder(table, builder.executor).select_as(model)
        header, *problems = str(raised.value).splitlines()
        assert header == f"{model.__name__} does not match the {table.name} table:"
        return [problem.removeprefix("  - ") for problem in problems]

    def test_a_field_that_names_nothing(self) -> None:
        class Unknown(BaseModel):
            subtitle: str

        assert self.problems(Unknown) == [
            "Unknown.subtitle matches no column, computed field or relation of novels"
        ]

    def test_a_type_that_differs_from_the_column(self) -> None:
        class Mismatch(BaseModel):
            id: str
            title: list[str]

        assert self.problems(Mismatch) == [
            "Mismatch.id is str, but novels.id is int",
            "Mismatch.title is list[str], but novels.title is str",
        ]

    def test_a_non_nullable_field_on_a_nullable_column(self) -> None:
        class Mismatch(BaseModel):
            author_id: int
            title_upper: str

        assert self.problems(Mismatch) == [
            "Mismatch.author_id is int, but novels.author_id can be NULL; "
            "declare it as int | None",
            "Mismatch.title_upper is str, but novels.title_upper can be NULL; "
            "declare it as str | None",
        ]

    def test_a_single_model_on_a_to_many_relation(self) -> None:
        class Rating(BaseModel):
            rating: int

        class Mismatch(BaseModel):
            reviews: Rating

        assert self.problems(Mismatch) == [
            "Mismatch.reviews is one Rating, but novels.reviews is a to-many "
            "relation; declare it as list[Rating]"
        ]

    def test_a_list_on_a_to_one_relation(self) -> None:
        class Mismatch(BaseModel):
            author: list[AuthorName]

        assert self.problems(Mismatch) == [
            "Mismatch.author is a list, but novels.author is a to-one relation; "
            "declare it as AuthorName or AuthorName | None"
        ]

    def test_a_relation_read_as_a_plain_value(self) -> None:
        class Mismatch(BaseModel):
            author: str

        assert self.problems(Mismatch) == [
            "Mismatch.author is str, but novels.author embeds a row; declare it "
            "as a model"
        ]

    def test_problems_of_a_nested_model_carry_their_path(self) -> None:
        class AuthorBirth(BaseModel):
            born_on: date
            age: int

        class Mismatch(BaseModel):
            author: AuthorBirth

        assert self.problems(Mismatch) == [
            "Mismatch.author.born_on is date, but authors.born_on can be NULL; "
            "declare it as date | None",
            "Mismatch.author.age matches no column, computed field or relation "
            "of authors",
        ]

    def test_a_relation_without_a_target_table_maps_the_stored_columns(self) -> None:
        class Book(BaseModel):
            name: str
            novels: list[AuthorName]

        class Mismatch(BaseModel):
            editor: Book

        assert self.problems(Mismatch) == [
            "Mismatch.editor.novels matches no column, computed field or "
            "relation of authors"
        ]

    def test_a_model_embedded_in_itself(self) -> None:
        class Cycle(BaseModel):
            name: str
            novels: list["NovelOfCycle"]

        class NovelOfCycle(BaseModel):
            author: Cycle

        Cycle.model_rebuild(_types_namespace={"NovelOfCycle": NovelOfCycle})

        assert self.problems(Cycle, Authors.table) == [
            "Cycle.novels.author embeds Cycle inside itself, which has no end"
        ]

    def test_a_response_key_shared_by_two_relations(self) -> None:
        class Ambiguous(BaseModel):
            authors: AuthorName

        assert self.problems(Ambiguous) == [
            "Ambiguous.authors could embed any of 2 relations that come back as "
            "authors; name the field after the attribute of one of them"
        ]

    def test_an_attribute_named_like_the_alias_of_another_relation(self) -> None:
        class Ambiguous(BaseModel):
            editor: AuthorName = Field(alias="author")

        assert self.problems(Ambiguous, Shadowed.table) == [
            "Ambiguous.editor could embed any of 2 relations that come back as "
            "author; name the field after the attribute of one of them"
        ]

    def test_an_unaliased_field_takes_the_relation_declared_under_its_name(
        self,
    ) -> None:
        class Card(BaseModel):
            author: AuthorName

        assert select_list(Card, Shadowed.table) == (
            "authors!novels_author_id_fkey(name)"
        )

    def test_a_name_only_model_ignores_its_validation_alias_when_selecting(
        self,
    ) -> None:
        class Card(BaseModel):
            model_config = ConfigDict(validate_by_alias=False, validate_by_name=True)
            key: int | None = Field(alias="id", validation_alias="author_id")

        assert select_list(Card) == "id"

    def test_a_relation_embedded_twice(self) -> None:
        class Twice(BaseModel):
            author: AuthorName
            writer: AuthorName = Field(alias="author")

        assert self.problems(Twice) == [
            "Twice.writer reads authors, which another field reads as well; read "
            "it through one field"
        ]

    def test_a_column_and_an_embed_under_one_key(self) -> None:
        class Clash(BaseModel):
            author: AuthorName
            authors: str = Field(alias="authors")

        class AuthorsColumnRow(BaseModel):
            authors: str

        clash_table = Table[Any, Any, Any](
            "novels", AuthorsColumnRow, relations=(Novels.author,)
        )

        assert self.problems(Clash, clash_table) == [
            "Clash.authors reads authors, which another field reads as well; "
            "read it through one field"
        ]

    def test_two_fields_from_different_columns_under_one_key(self) -> None:
        class Clash(BaseModel):
            title: str = Field(alias="heading")
            id: int = Field(alias="heading")

        assert self.problems(Clash) == [
            "Clash.id is read from heading, as another field reading a different "
            "column is"
        ]

    def test_a_nested_type_that_differs(self) -> None:
        class Mismatch(BaseModel):
            title: list[int]

        assert self.problems(Mismatch) == [
            "Mismatch.title is list[int], but novels.title is str"
        ]

    def test_a_model_without_fields(self) -> None:
        class Empty(BaseModel):
            pass

        assert self.problems(Empty) == ["Empty has no fields to select"]

    def test_an_alias_choice(self) -> None:
        class Ambiguous(BaseModel):
            title: str = Field(validation_alias=AliasChoices("title", "heading"))

        assert self.problems(Ambiguous) == [
            "Ambiguous.title is read through an AliasPath or AliasChoices, which "
            "select_as() cannot select"
        ]

    def test_every_problem_is_listed_before_anything_is_sent(self) -> None:
        class Mismatch(BaseModel):
            id: str
            subtitle: str

        executor, builder = novels()

        with pytest.raises(TypeError):
            builder.select_as(Mismatch)
        assert executor.requests == []
