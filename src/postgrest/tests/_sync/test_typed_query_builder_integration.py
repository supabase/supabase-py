from collections.abc import Iterator
from datetime import date

import pytest

from postgrest import (
    APIError,
    CountedResponse,
    CountMethod,
    SyncPostgrestClient,
    TableExecutor,
    TypedQueryBuilder,
)
from tests.typed_schema import (
    Books,
    BooksInsert,
    BooksRow,
    BooksUpdate,
    BookTitles,
    BookTitlesRow,
    Places,
)

type TypedBooks = TypedQueryBuilder[TableExecutor, BooksRow, BooksInsert, BooksUpdate]

DUNE = BooksRow(
    id=1,
    title="Dune",
    isbn="9780441013593",
    pages=412,
    published_on=date(1965, 8, 1),
    tags=["science fiction"],
    metadata={"awards": ["Hugo", "Nebula"]},
)


@pytest.fixture
def books(postgrest_client: SyncPostgrestClient) -> Iterator[TypedBooks]:
    """The typed builder of `books`, which forgets the rows a test wrote: the
    seeded rows have ids below 100 and the written ones from 100 on."""
    builder = postgrest_client.table(Books.table)
    yield builder
    builder.delete().where(Books.id.gte(100)).execute()


def test_select_decodes_every_row(books: TypedBooks) -> None:
    rows = books.select().order(Books.id).execute()

    assert [row.id for row in rows] == [1, 2, 3]
    assert rows[0] == DUNE
    assert rows[2].published_on is None


def test_select_only_reads_through_the_entries(books: TypedBooks) -> None:
    rows = (
        books.select_only(
            [Books.id, Books.published_on, Books.title_upper, Books.next_publication]
        )
        .where(Books.id.eq(1))
        .execute()
    )

    (row,) = rows
    assert row[Books.id] == 1
    assert row[Books.published_on] == date(1965, 8, 1)
    assert row[Books.title_upper] == "DUNE"
    assert row[Books.next_publication] == date(1966, 8, 1)
    with pytest.raises(KeyError):
        row[Books.title]


def test_select_only_of_every_column_converts_into_the_row(
    books: TypedBooks,
) -> None:
    rows = (
        books.select_only(
            [
                Books.id,
                Books.title,
                Books.isbn,
                Books.pages,
                Books.published_on,
                Books.tags,
                Books.metadata,
            ]
        )
        .where(Books.id.eq(3))
        .execute()
    )

    assert rows[0].to_row() == BooksRow(id=3, title="Untitled", pages=0, tags=[])


def test_where_composes_filters(books: TypedBooks) -> None:
    rows = (
        books.select()
        .where((Books.pages.gt(300) | Books.isbn.is_null()) & ~Books.id.eq(1))
        .execute()
    )
    assert [row.id for row in rows] == [3]

    rows = (
        books.select()
        .where(Books.pages.gte(0))
        .where(Books.id.lte(2))
        .order(Books.id)
        .execute()
    )
    assert [row.id for row in rows] == [1, 2]


def test_array_and_json_filters(books: TypedBooks) -> None:
    rows = books.select().where(Books.tags.contains(["cyberpunk"])).execute()
    assert [row.id for row in rows] == [2]

    rows = (
        books.select()
        .where(Books.metadata.contains({"awards": ["Nebula"]}))
        .order(Books.id)
        .execute()
    )
    assert [row.id for row in rows] == [1, 2]


def test_order_limit_and_range(books: TypedBooks) -> None:
    rows = books.select().order(Books.pages.desc()).execute()
    assert [row.id for row in rows] == [1, 2, 3]

    rows = books.select().order(Books.published_on.desc().nulls_first()).execute()
    assert [row.id for row in rows] == [3, 2, 1]

    rows = books.select().order(Books.id).limit(2).execute()
    assert [row.id for row in rows] == [1, 2]

    rows = books.select().order(Books.id).range(1, 2).execute()
    assert [row.id for row in rows] == [2, 3]


def test_single_and_maybe_single(books: TypedBooks) -> None:
    row = books.select().where(Books.id.eq(2)).single().execute()
    assert row.title == "Neuromancer"

    maybe = books.select().where(Books.id.eq(2)).maybe_single().execute()
    assert maybe is not None
    assert maybe.title == "Neuromancer"

    assert books.select().where(Books.id.eq(999)).maybe_single().execute() is None

    with pytest.raises(APIError) as error:
        books.select().where(Books.id.lte(2)).maybe_single().execute()
    assert error.value.code == "406"

    with pytest.raises(APIError):
        books.select().where(Books.id.lte(2)).single().execute()


def test_count(books: TypedBooks) -> None:
    response = books.select().order(Books.id).limit(1).count().execute()
    assert response.count == 3
    assert [row.id for row in response.data] == [1]

    assert books.count().where(Books.isbn.is_null()).execute() == 1
    assert books.count(CountMethod.estimated).execute() == 3
    assert isinstance(books.count(CountMethod.planned).execute(), int)


def test_head(books: TypedBooks) -> None:
    assert books.select().where(Books.id.eq(1)).head().execute() is None


def test_csv(books: TypedBooks) -> None:
    text = books.select_only([Books.id, Books.title]).order(Books.id).csv().execute()

    assert text.splitlines() == ["id,title", "1,Dune", "2,Neuromancer", "3,Untitled"]


def test_explain(books: TypedBooks) -> None:
    plan = books.select().where(Books.id.eq(1)).explain().execute()
    assert "Aggregate" in plan

    plan_json = books.select().explain(analyze=True, format="json").execute()
    assert isinstance(plan_json, list)


def test_geojson(postgrest_client: SyncPostgrestClient) -> None:
    collection = (
        postgrest_client.table(Places.table)
        .select()
        .order(Places.id)
        .geojson()
        .execute()
    )

    assert collection["type"] == "FeatureCollection"
    features = collection["features"]
    assert isinstance(features, list)
    assert len(features) == 2
    null_island = features[0]
    assert isinstance(null_island, dict)
    assert null_island["geometry"] == {"type": "Point", "coordinates": [0, 0]}


def test_strip_nulls(books: TypedBooks) -> None:
    rows = books.select().where(Books.id.eq(3)).strip_nulls().execute()
    assert rows[0].isbn is None
    assert rows[0].published_on is None

    partial = (
        books.select_only([Books.id, Books.isbn])
        .where(Books.id.eq(3))
        .strip_nulls()
        .execute()
    )
    assert partial[0].json == {"id": 3}
    assert partial[0][Books.isbn] is None


def test_a_view_reads_its_row_type(postgrest_client: SyncPostgrestClient) -> None:
    titles = (
        postgrest_client.table(BookTitles.table)
        .select()
        .order(BookTitles.id)
        .limit(2)
        .execute()
    )

    assert titles == [
        BookTitlesRow(id=1, title="Dune"),
        BookTitlesRow(id=2, title="Neuromancer"),
    ]


def test_insert_one_row(books: TypedBooks) -> None:
    assert books.insert({"title": "Emma", "pages": 474}).execute() is None

    row = (
        books.insert({"title": "Persuasion", "published_on": date(1817, 12, 20)})
        .select()
        .single()
        .execute()
    )
    assert row.id >= 100
    assert row.title == "Persuasion"
    assert row.pages == 0
    assert row.published_on == date(1817, 12, 20)
    assert row.tags == []

    assert books.count().where(Books.id.gte(100)).execute() == 2


def test_insert_rows_with_defaults(books: TypedBooks) -> None:
    rows = (
        books.insert(
            [{"title": "A"}, {"title": "B", "pages": 2}, {"title": "C", "isbn": None}]
        )
        .select()
        .order(Books.id)
        .execute()
    )

    assert [(row.title, row.pages, row.isbn) for row in rows] == [
        ("A", 0, None),
        ("B", 2, None),
        ("C", 0, None),
    ]


def test_insert_returns_some_columns(books: TypedBooks) -> None:
    rows = (
        books.insert({"title": "D"})
        .select_only([Books.id, Books.title_upper])
        .execute()
    )

    assert rows[0][Books.id] >= 100
    assert rows[0][Books.title_upper] == "D"


def test_upsert(books: TypedBooks) -> None:
    books.upsert({"id": 1000, "title": "E", "isbn": "isbn-1000"}).execute()

    row = books.upsert({"id": 1000, "title": "F"}).select().single().execute()
    assert (row.id, row.title, row.isbn) == (1000, "F", "isbn-1000")

    row = (
        books.upsert({"title": "G", "isbn": "isbn-1000"}, on_conflict=[Books.isbn])
        .select()
        .single()
        .execute()
    )
    assert (row.id, row.title) == (1000, "G")

    ignored = (
        books.upsert({"id": 1000, "title": "H"}, ignore_duplicates=True)
        .select()
        .execute()
    )
    assert ignored == []
    row = books.select().where(Books.id.eq(1000)).single().execute()
    assert row.title == "G"


def test_update(books: TypedBooks) -> None:
    inserted = books.insert({"title": "I"}).select().single().execute()

    assert books.update({"pages": 9}).where(Books.id.eq(inserted.id)).execute() is None

    rows = (
        books.update({"title": "J"}).where(Books.id.eq(inserted.id)).select().execute()
    )
    assert [(row.title, row.pages) for row in rows] == [("J", 9)]


def test_update_all_in_a_dry_run(books: TypedBooks) -> None:
    rows = books.update({"pages": 1}).all().dry_run().select().order(Books.id).execute()
    assert [row.pages for row in rows] == [1, 1, 1]

    row = books.select().where(Books.id.eq(1)).single().execute()
    assert row.pages == 412


def test_delete(books: TypedBooks) -> None:
    books.insert([{"title": "K"}, {"title": "L"}]).execute()

    deleted = (
        books.delete()
        .where(Books.title.in_(["K", "L"]))
        .select()
        .order(Books.title)
        .execute()
    )
    assert [row.title for row in deleted] == ["K", "L"]
    assert books.count().execute() == 3

    response = books.delete().all().dry_run().count().execute()
    assert response == CountedResponse(None, 3)
    assert books.count().execute() == 3


def test_max_affected(books: TypedBooks) -> None:
    books.insert([{"title": "M"}, {"title": "M"}]).execute()

    with pytest.raises(APIError) as error:
        books.delete().where(Books.title.eq("M")).max_affected(1).execute()
    assert error.value.code == "PGRST124"

    response = (
        books.delete().where(Books.title.eq("M")).max_affected(2).count().execute()
    )
    assert response == CountedResponse(None, 2)


def test_dry_run_of_an_insert(books: TypedBooks) -> None:
    row = books.insert({"title": "Ghost"}).select().single().dry_run().execute()
    assert row.title == "Ghost"

    assert books.count().where(Books.title.eq("Ghost")).execute() == 0


def test_request_options_apply(books: TypedBooks) -> None:
    rows = books.select().retry(False).request_timeout(10).execute()

    assert len(rows) == 3


def test_an_error_answer_raises(books: TypedBooks) -> None:
    with pytest.raises(APIError) as error:
        books.select().where(Books.title.raw("nonsense.x")).execute()

    assert error.value.status_code == 400
