from dataclasses import dataclass, field, replace
from datetime import date
from typing import Any

import pytest
from pydantic import BaseModel

from postgrest import (
    Column,
    Embed,
    EmbeddedCount,
    EmbeddedScope,
    NullableColumn,
    PartialRow,
    Selectable,
    Table,
    TableOperation,
    TableRequest,
    TableResult,
    ToManyRelation,
    ToOneRelation,
    TypedQueryBuilder,
)
from postgrest.table_executor import _render


class AuthorsRow(BaseModel):
    id: int
    name: str
    born_on: date | None = None


class NovelsRow(BaseModel):
    id: int
    title: str
    author_id: int | None = None


class ReviewsRow(BaseModel):
    id: int
    novel_id: int
    rating: int


class Authors:
    id = Column[AuthorsRow, int]("id")
    name = Column[AuthorsRow, str]("name")
    born_on = NullableColumn[AuthorsRow, date]("born_on")
    novels = ToManyRelation[AuthorsRow, NovelsRow]("novels", NovelsRow)
    table = Table("authors", AuthorsRow, primary_key=(id,))


class Novels:
    id = Column[NovelsRow, int]("id")
    title = Column[NovelsRow, str]("title")
    author_id = NullableColumn[NovelsRow, int]("author_id")
    author = ToOneRelation[NovelsRow, AuthorsRow](
        "authors", AuthorsRow, constraint="novels_author_id_fkey"
    )
    reviews = ToManyRelation[NovelsRow, ReviewsRow]("reviews", ReviewsRow)
    editor = ToOneRelation[NovelsRow, AuthorsRow](
        "authors", AuthorsRow, constraint="novels_editor_id_fkey", alias="editor"
    )
    table = Table[NovelsRow, dict[str, Any], dict[str, Any]](
        "novels", NovelsRow, primary_key=(id,)
    )


class Reviews:
    id = Column[ReviewsRow, int]("id")
    rating = Column[ReviewsRow, int]("rating")
    novel = ToOneRelation[ReviewsRow, NovelsRow]("novels", NovelsRow)


@dataclass
class Recording:
    result: TableResult = field(default_factory=TableResult)
    requests: list[TableRequest] = field(default_factory=list)

    def execute(self, request: TableRequest) -> TableResult:
        self.requests.append(request)
        return self.result


def select(
    *columns: Selectable[Any],
    scopes: tuple[EmbeddedScope[Any], ...] = (),
    table: Table[Any, Any, Any] = Novels.table,
) -> TableRequest:
    return TableRequest(
        table=table,
        operation=TableOperation.SELECT,
        columns=columns,
        embedded_scopes=scopes,
    )


def query(request: TableRequest) -> dict[str, str]:
    rendered = _render(request).query
    return {key: rendered[key] for key in rendered._map}


def select_list(*columns: Selectable[Any]) -> str | None:
    return _render(select(*columns)).query.get("select")


def select_list_of(request: TableRequest) -> str | None:
    return _render(request).query.get("select")


def novels() -> tuple[
    Recording, TypedQueryBuilder[Any, NovelsRow, dict[str, Any], dict[str, Any]]
]:
    executor = Recording(TableResult(data=[]))
    return executor, TypedQueryBuilder(Novels.table, executor)


class TestSelectList:
    def test_an_embed_renders_its_columns_in_parentheses(self) -> None:
        embed = Authors.novels.select([Novels.id, Novels.title])

        assert embed == Embed(Authors.novels, (Novels.id, Novels.title))
        assert embed.response_key == "novels"
        assert select_list(Authors.name, embed) == "name,novels(id,title)"

    def test_an_embed_without_columns_selects_every_column(self) -> None:
        assert select_list(Authors.novels.select()) == "novels(*)"

    def test_the_constraint_is_sent_as_a_hint(self) -> None:
        embed = Novels.author.select([Authors.name])

        assert embed.response_key == "authors"
        assert select_list(Novels.title, embed) == (
            "title,authors!novels_author_id_fkey(name)"
        )

    def test_an_alias_tells_two_relations_to_one_table_apart(self) -> None:
        scope = EmbeddedScope(Novels.editor, requires_match=True).where(
            Authors.id.eq(1)
        )
        request = replace(
            select(
                Novels.author.select([Authors.name]),
                Novels.editor.select([Authors.name]),
                scopes=(scope,),
            ),
            filter=Novels.editor.is_null(),
        )

        assert Novels.editor.response_key == "editor"
        assert query(request) == {
            "select": (
                "authors!novels_author_id_fkey(name),"
                "editor:authors!novels_editor_id_fkey!inner(name)"
            ),
            "editor": "is.null",
            "editor.id": "eq.1",
        }

    def test_embeds_nest(self) -> None:
        embed = Authors.novels.select(
            [Novels.title, Novels.reviews.select([Reviews.rating])]
        )

        assert select_list(embed) == "novels(title,reviews(rating))"

    def test_a_count_comes_back_under_its_own_key_after_the_embeds(self) -> None:
        count = Authors.novels.count()

        assert count == EmbeddedCount(Authors.novels)
        assert count.response_key == "novels(count)"
        assert select_list(count, Authors.name, Authors.novels.select()) == (
            'name,novels(*),"novels(count)":novels(count)'
        )

    def test_an_empty_list_of_columns_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="at least one column"):
            Authors.novels.select([])

    def test_an_embed_twice_is_rejected(self) -> None:
        _, builder = novels()

        with pytest.raises(ValueError, match="embedded twice"):
            builder.select_only(
                [Novels.author.select([Authors.id]), Novels.author.select()]
            )
        with pytest.raises(ValueError, match="embedded twice"):
            Authors.novels.select([Novels.reviews.select(), Novels.reviews.select()])


class TestScopes:
    def test_a_scope_renders_under_the_key_of_its_embed(self) -> None:
        scope = (
            EmbeddedScope(Authors.novels)
            .where(Novels.title.like("D%") | Novels.id.eq(2))
            .where(Novels.id.gt(0))
            .order(Novels.title.desc())
            .order(Novels.id)
            .range(1, 3)
        )

        assert query(
            select(
                Authors.name,
                Authors.novels.select([Novels.title]),
                scopes=(scope,),
                table=Authors.table,
            )
        ) == {
            "select": "name,novels(title)",
            "novels.or": "(title.like.D%,id.eq.2)",
            "novels.id": "gt.0",
            "novels.order": "title.desc,id",
            "novels.offset": "1",
            "novels.limit": "3",
        }

    def test_a_hinted_embed_is_scoped_by_its_key(self) -> None:
        scope = EmbeddedScope(Novels.author).where(Authors.name.eq("Ada"))

        assert query(select(Novels.author.select(), scopes=(scope,))) == {
            "select": "authors!novels_author_id_fkey(*)",
            "authors.name": "eq.Ada",
        }

    def test_scopes_on_one_embed_combine(self) -> None:
        scopes = (
            EmbeddedScope(Authors.novels, requires_match=True)
            .order(Novels.title)
            .range(2, 5)
            .embedded(Novels.reviews, lambda reviews: reviews.limit(1)),
            EmbeddedScope(Authors.novels)
            .where(Novels.id.gt(1))
            .order(Novels.id.desc())
            .limit(2)
            .embedded(Novels.reviews, lambda reviews: reviews.limit(3)),
        )
        embed = Authors.novels.select([Novels.reviews.select()])

        assert query(select(embed, scopes=scopes, table=Authors.table)) == {
            "select": "novels!inner(reviews(*))",
            "novels.id": "gt.1",
            "novels.order": "title,id.desc",
            "novels.offset": "2",
            "novels.limit": "2",
            "novels.reviews.limit": "3",
        }

    def test_requiring_joins_the_embed_as_inner(self) -> None:
        scope = EmbeddedScope(Novels.author, requires_match=True)

        assert select_list_of(select(Novels.author.select(), scopes=(scope,))) == (
            "authors!novels_author_id_fkey!inner(*)"
        )

    def test_nested_scopes_render_under_a_dotted_path(self) -> None:
        scope = EmbeddedScope(Authors.novels).requiring(
            Novels.reviews, lambda reviews: reviews.where(Reviews.rating.gte(4))
        )
        embed = Authors.novels.select([Novels.reviews.select([Reviews.rating])])
        nested = EmbeddedScope(Authors.novels).embedded(
            Novels.reviews, lambda reviews: reviews.limit(2)
        )

        assert query(select(embed, scopes=(scope, nested), table=Authors.table)) == {
            "select": "novels(reviews!inner(rating))",
            "novels.reviews.rating": "gte.4",
            "novels.reviews.limit": "2",
        }

    def test_a_scope_on_an_embed_the_list_leaves_out_is_rejected(self) -> None:
        scope = EmbeddedScope(Novels.reviews).limit(1)

        with pytest.raises(ValueError, match="reviews is not embedded"):
            _render(select(Novels.title, scopes=(scope,)))
        with pytest.raises(ValueError, match="reviews is not embedded"):
            _render(select(scopes=(scope,)))

    def test_a_nested_scope_on_an_embed_the_list_leaves_out_is_rejected(
        self,
    ) -> None:
        scope = EmbeddedScope(Authors.novels).embedded(
            Novels.reviews, lambda reviews: reviews.limit(1)
        )

        with pytest.raises(ValueError, match="reviews is not embedded"):
            _render(
                select(Authors.novels.select(), scopes=(scope,), table=Authors.table)
            )

    def test_a_to_one_embed_takes_no_order_or_row_window(self) -> None:
        scope = EmbeddedScope(Novels.author)

        with pytest.raises(ValueError, match="to-many"):
            scope.order(Authors.name)
        with pytest.raises(ValueError, match="to-many"):
            scope.limit(1)
        with pytest.raises(ValueError, match="to-many"):
            scope.range(0, 1)

    def test_a_range_ending_before_it_starts_is_rejected(self) -> None:
        with pytest.raises(ValueError, match="at least start"):
            EmbeddedScope(Authors.novels).range(3, 2)

    def test_a_write_that_returns_no_rows_takes_no_scope(self) -> None:
        request = TableRequest(
            table=Novels.table,
            operation=TableOperation.DELETE,
            filter=Novels.id.eq(1),
            embedded_scopes=(EmbeddedScope(Novels.author, requires_match=True),),
        )

        with pytest.raises(ValueError, match="returns no rows"):
            _render(request)

    def test_a_returning_write_scopes_its_embeds(self) -> None:
        request = TableRequest(
            table=Novels.table,
            operation=TableOperation.DELETE,
            filter=Novels.id.eq(1),
            columns=(Novels.id, Authors.novels.select()),
            returning=True,
            embedded_scopes=(EmbeddedScope(Authors.novels).limit(1),),
        )

        assert query(request) == {
            "id": "eq.1",
            "select": "id,novels(*)",
            "novels.limit": "1",
        }


class TestIsNull:
    def test_it_renders_under_the_key_of_the_embed(self) -> None:
        filter = Novels.author.is_null() | Novels.title.eq("Dune")
        request = replace(
            select(Novels.title, Novels.author.select()),
            filter=filter & ~Novels.reviews.is_null(),
        )

        assert Novels.author.is_null()._query_parameters() == [("authors", "is.null")]
        assert Novels.author.is_null().comparison is None
        assert query(
            replace(request, columns=(*request.columns, Novels.reviews.select()))
        ) == {
            "select": "title,authors!novels_author_id_fkey(*),reviews(*)",
            "or": "(authors.is.null,title.eq.Dune)",
            "reviews": "not.is.null",
        }

    def test_it_needs_the_embed_in_the_select_list(self) -> None:
        request = replace(select(Novels.title), filter=Novels.author.is_null())

        with pytest.raises(ValueError, match="authors is not embedded"):
            _render(request)

    @pytest.mark.parametrize(
        "operation",
        [TableOperation.UPDATE, TableOperation.DELETE, TableOperation.COUNT],
    )
    def test_it_is_rejected_on_a_write_and_a_count(
        self, operation: TableOperation
    ) -> None:
        request = TableRequest(
            table=Novels.table,
            operation=operation,
            filter=Novels.id.eq(1) & ~Novels.author.is_null(),
            payload={"title": "x"} if operation is TableOperation.UPDATE else None,
        )

        with pytest.raises(ValueError, match="applies to a read only"):
            _render(request)

    def test_a_filter_on_an_embedded_column_is_rejected_on_a_delete(self) -> None:
        request = TableRequest(
            table=Novels.table,
            operation=TableOperation.DELETE,
            filter=Column[NovelsRow, str]("authors.name").eq("Ada"),
        )

        with pytest.raises(ValueError, match="names no rows"):
            _render(request)

    def test_in_a_scope_it_tests_a_nested_embed(self) -> None:
        scope = EmbeddedScope(Authors.novels).where(~Novels.reviews.is_null())
        embed = Authors.novels.select([Novels.title, Novels.reviews.select()])

        assert query(select(embed, scopes=(scope,), table=Authors.table)) == {
            "select": "novels(title,reviews(*))",
            "novels.reviews": "not.is.null",
        }

    def test_in_a_scope_it_needs_the_nested_embed(self) -> None:
        scope = EmbeddedScope(Authors.novels).where(Novels.reviews.is_null())

        with pytest.raises(ValueError, match="reviews is not embedded in novels"):
            _render(
                select(Authors.novels.select(), scopes=(scope,), table=Authors.table)
            )


class TestBuilder:
    def test_embedded_and_requiring_collect_scopes(self) -> None:
        executor, builder = novels()

        builder.select_only([Novels.title, Novels.reviews.select()]).embedded(
            Novels.reviews, lambda reviews: reviews.order(Reviews.rating.desc())
        ).requiring(Novels.author).execute()

        (request,) = executor.requests
        assert request.embedded_scopes == (
            EmbeddedScope(Novels.reviews, orderings=(Reviews.rating.desc(),)),
            EmbeddedScope(Novels.author, requires_match=True),
        )

    def test_requiring_applies_its_scope(self) -> None:
        executor, builder = novels()

        builder.select_only([Novels.reviews.select()]).requiring(
            Novels.reviews, lambda reviews: reviews.where(Reviews.rating.eq(5))
        ).execute()

        (request,) = executor.requests
        assert query(request) == {
            "select": "reviews!inner(*)",
            "reviews.rating": "eq.5",
        }

    def test_a_returning_write_embeds(self) -> None:
        executor, builder = novels()

        builder.delete().where(Novels.id.eq(1)).select_only(
            [Novels.id, Novels.author.select([Authors.name])]
        ).execute()

        (request,) = executor.requests
        assert query(request)["select"] == ("id,authors!novels_author_id_fkey(name)")


class TestReads:
    def test_a_to_one_relation_reads_as_a_partial_row(self) -> None:
        embed = Novels.author.select([Authors.name, Authors.born_on])
        row = PartialRow(
            Novels.table,
            (Novels.title, embed),
            {"title": "Dune", "authors": {"name": "Frank", "born_on": "1920-10-08"}},
        )

        author = row[Novels.author]

        assert author is not None
        assert author[Authors.name] == "Frank"
        assert author[Authors.born_on] == date(1920, 10, 8)
        with pytest.raises(KeyError):
            author[Authors.id]

    def test_a_to_one_relation_without_a_row_reads_as_none(self) -> None:
        row = PartialRow(Novels.table, (Novels.author.select(),), {"authors": None})

        assert row[Novels.author] is None

    def test_a_to_many_relation_reads_as_a_list(self) -> None:
        embed = Authors.novels.select([Novels.title])
        row = PartialRow(
            Authors.table,
            (embed,),
            {"novels": [{"title": "Dune"}, {"title": "Emma"}]},
        )

        assert [novel[Novels.title] for novel in row[Authors.novels]] == [
            "Dune",
            "Emma",
        ]

    def test_an_embed_of_every_column_reads_every_stored_column(self) -> None:
        row = PartialRow(
            Novels.table,
            (Novels.title, Novels.author.select()),
            {"title": "Dune", "authors": {"id": 1, "name": "Frank", "born_on": None}},
        )

        author = row[Novels.author]

        assert author is not None
        assert author[Authors.id] == 1
        assert author.to_row() == AuthorsRow(id=1, name="Frank")

    def test_nested_embeds_read_through_their_relations(self) -> None:
        embed = Authors.novels.select([Novels.reviews.select([Reviews.rating])])
        row = PartialRow(
            Authors.table,
            (embed,),
            {"novels": [{"reviews": [{"rating": 5}, {"rating": "4"}]}]},
        )

        (novel,) = row[Authors.novels]
        assert [review[Reviews.rating] for review in novel[Novels.reviews]] == [5, 4]

    def test_a_count_reads_as_an_int(self) -> None:
        row = PartialRow(
            Authors.table,
            (Authors.novels.count(),),
            {"novels(count)": [{"count": 3}]},
        )

        assert row[Authors.novels.count()] == 3

    def test_a_relation_the_list_left_out_is_a_key_error(self) -> None:
        row = PartialRow(Novels.table, (Novels.title,), {"title": "Dune"})

        with pytest.raises(KeyError, match="authors was not selected"):
            row[Novels.author]
        with pytest.raises(KeyError, match="novels"):
            PartialRow(Authors.table, (Authors.name,), {"name": "Ada"})[
                Authors.novels.count()
            ]

    def test_an_embed_in_the_wrong_shape_is_rejected(self) -> None:
        row = PartialRow(Authors.table, (Authors.novels.select(),), {"novels": {}})

        with pytest.raises(ValueError, match="not a list of rows"):
            row[Authors.novels]

    def test_the_parent_row_leaves_its_embeds_out(self) -> None:
        row = PartialRow(
            Authors.table,
            (Authors.id, Authors.name, Authors.novels.select(), Authors.novels.count()),
            {"id": 1, "name": "Ada", "novels": [], "novels(count)": [{"count": 0}]},
        )

        assert row.to_row() == AuthorsRow(id=1, name="Ada")

    def test_a_select_only_with_embeds_reads_nested_rows(self) -> None:
        executor, builder = novels()
        executor.result = TableResult(
            data=[{"title": "Dune", "authors": {"name": "Frank"}}]
        )

        (row,) = builder.select_only(
            [Novels.title, Novels.author.select([Authors.name])]
        ).execute()

        author = row[Novels.author]
        assert author is not None
        assert author[Authors.name] == "Frank"
