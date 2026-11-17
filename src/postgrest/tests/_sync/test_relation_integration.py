from datetime import date

import pytest

from postgrest import SyncPostgrestClient
from tests.typed_schema import Authors, AuthorsRow, Novels


def test_a_to_one_embed_reads_as_a_nested_row(
    postgrest_client: SyncPostgrestClient,
) -> None:
    rows = (
        postgrest_client.table(Novels.table)
        .select_only(
            [Novels.title, Novels.author.select([Authors.name, Authors.born_on])]
        )
        .order(Novels.id)
        .execute()
    )

    authors = [row[Novels.author] for row in rows]
    assert [None if author is None else author[Authors.name] for author in authors] == [
        "Frank Herbert",
        "Frank Herbert",
        "William Gibson",
        None,
    ]
    first = authors[0]
    assert first is not None
    assert first[Authors.born_on] == date(1920, 10, 8)


def test_a_to_many_embed_reads_as_a_list(
    postgrest_client: SyncPostgrestClient,
) -> None:
    rows = (
        postgrest_client.table(Authors.table)
        .select_only(
            [Authors.id, Authors.novels.select([Novels.title]), Authors.novels.count()]
        )
        .order(Authors.id)
        .embedded(Authors.novels, lambda novels: novels.order(Novels.title.desc()))
        .execute()
    )

    assert [[novel[Novels.title] for novel in row[Authors.novels]] for row in rows] == [
        ["Dune Messiah", "Dune"],
        ["Neuromancer"],
        [],
    ]
    assert [row[Authors.novels.count()] for row in rows] == [2, 1, 0]


def test_an_embed_of_every_column_converts_into_the_row(
    postgrest_client: SyncPostgrestClient,
) -> None:
    row = (
        postgrest_client.table(Novels.table)
        .select_only([Novels.title, Novels.author.select()])
        .where(Novels.id.eq(3))
        .single()
        .execute()
    )

    author = row[Novels.author]
    assert author is not None
    assert author.to_row() == AuthorsRow(
        id=2, name="William Gibson", born_on=date(1948, 3, 17)
    )


def test_a_scope_filters_and_windows_the_embedded_rows(
    postgrest_client: SyncPostgrestClient,
) -> None:
    rows = (
        postgrest_client.table(Authors.table)
        .select_only([Authors.id, Authors.novels.select([Novels.title])])
        .order(Authors.id)
        .embedded(
            Authors.novels,
            lambda novels: novels.where(Novels.title.like("Dune%"))
            .order(Novels.id)
            .range(1, 1),
        )
        .execute()
    )

    assert [[novel[Novels.title] for novel in row[Authors.novels]] for row in rows] == [
        ["Dune Messiah"],
        [],
        [],
    ]


def test_requiring_drops_the_rows_without_a_match(
    postgrest_client: SyncPostgrestClient,
) -> None:
    rows = (
        postgrest_client.table(Authors.table)
        .select_only([Authors.name, Authors.novels.select([Novels.title])])
        .requiring(
            Authors.novels, lambda novels: novels.where(Novels.title.eq("Neuromancer"))
        )
        .execute()
    )

    assert [row[Authors.name] for row in rows] == ["William Gibson"]


def test_nested_embeds_and_scopes(
    postgrest_client: SyncPostgrestClient,
) -> None:
    rows = (
        postgrest_client.table(Authors.table)
        .select_only(
            [
                Authors.id,
                Authors.novels.select(
                    [Novels.title, Novels.author.select([Authors.name])]
                ),
            ]
        )
        .where(Authors.id.eq(1))
        .embedded(
            Authors.novels,
            lambda novels: novels.where(Novels.id.eq(2)).requiring(
                Novels.author, lambda author: author.where(Authors.id.eq(1))
            ),
        )
        .execute()
    )

    ((novel,),) = [row[Authors.novels] for row in rows]
    assert novel[Novels.title] == "Dune Messiah"
    author = novel[Novels.author]
    assert author is not None
    assert author[Authors.name] == "Frank Herbert"


def test_is_null_filters_on_the_absence_of_an_embedded_row(
    postgrest_client: SyncPostgrestClient,
) -> None:
    novels = postgrest_client.table(Novels.table)
    without = (
        novels.select_only([Novels.title, Novels.author.select([Authors.id])])
        .where(Novels.author.is_null() | Novels.id.eq(3))
        .order(Novels.id)
        .execute()
    )
    authors = (
        postgrest_client.table(Authors.table)
        .select_only([Authors.name, Authors.novels.select([Novels.id])])
        .where(Authors.novels.is_null())
        .execute()
    )

    assert [row[Novels.title] for row in without] == ["Neuromancer", "Anonymous"]
    assert [row[Authors.name] for row in authors] == ["Nobody"]


def test_a_returning_write_embeds(
    postgrest_client: SyncPostgrestClient,
) -> None:
    rows = (
        postgrest_client.table(Novels.table)
        .delete()
        .where(Novels.id.eq(1))
        .select_only([Novels.title, Novels.author.select([Authors.name])])
        .dry_run()
        .execute()
    )

    (row,) = rows
    author = row[Novels.author]
    assert author is not None
    assert author[Authors.name] == "Frank Herbert"


def test_a_relation_filter_on_a_delete_is_rejected(
    postgrest_client: SyncPostgrestClient,
) -> None:
    delete = (
        postgrest_client.table(Novels.table)
        .delete()
        .where(Novels.id.eq(1) & Novels.author.is_null())
    )

    with pytest.raises(ValueError, match="applies to a read only"):
        delete.execute()
