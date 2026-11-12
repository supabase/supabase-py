from dataclasses import FrozenInstanceError
from datetime import datetime

import pytest
from supabase_utils.http.io import SyncHttpIO

from postgrest import Column, ComputedField, NullableColumn, Ordering
from postgrest.request_builder import SelectRequestBuilder


class BookRow:
    pass


class Books:
    id = Column[BookRow, int]("id")
    title = Column[BookRow, str]("title")
    published_on = NullableColumn[BookRow, datetime]("published_on")
    full_title = ComputedField[BookRow, str]("full_title")


def test_a_bare_column_orders_with_no_direction() -> None:
    assert Books.title.order_key == "title"
    assert Books.published_on.order_key == "published_on"
    assert Books.full_title.order_key == "full_title"


def test_a_column_is_an_ordering() -> None:
    assert isinstance(Books.title, Ordering)
    assert isinstance(Books.title.asc(), Ordering)


def test_a_direction_follows_the_expression() -> None:
    assert Books.title.asc().order_key == "title.asc"
    assert Books.title.desc().order_key == "title.desc"
    assert Books.full_title.desc().order_key == "full_title.desc"


def test_a_null_placement_follows_the_direction() -> None:
    assert Books.published_on.asc().nulls_first().order_key == (
        "published_on.asc.nullsfirst"
    )
    assert Books.published_on.desc().nulls_last().order_key == (
        "published_on.desc.nullslast"
    )


def test_a_null_placement_alone_leaves_the_direction_to_postgrest() -> None:
    assert Books.published_on.nulls_first().order_key == "published_on.nullsfirst"
    assert Books.published_on.nulls_last().order_key == "published_on.nullslast"


def test_the_order_of_the_calls_does_not_matter() -> None:
    assert (
        Books.published_on.nulls_first().desc()
        == Books.published_on.desc().nulls_first()
    )
    assert Books.published_on.nulls_first().desc().order_key == (
        "published_on.desc.nullsfirst"
    )


def test_a_later_call_replaces_an_earlier_one() -> None:
    assert Books.title.asc().desc().order_key == "title.desc"
    assert Books.published_on.nulls_first().nulls_last().order_key == (
        "published_on.nullslast"
    )


def test_an_ordering_is_a_value() -> None:
    assert Books.title.asc() == Books.title.asc()
    assert Books.title.asc() != Books.title.desc()
    assert Books.title.asc() != Books.id.asc()
    assert hash(Books.title.asc()) == hash(Books.title.asc())
    assert Books.title.asc() != Books.title


def test_an_ordering_is_frozen() -> None:
    ordering = Books.title.asc()

    with pytest.raises(FrozenInstanceError):
        ordering.direction = "desc"  # pyrefly: ignore[missing-attribute, read-only]


def test_chaining_leaves_the_earlier_ordering_unchanged() -> None:
    ascending = Books.title.asc()
    ascending.nulls_first()

    assert ascending.order_key == "title.asc"


def test_an_ad_hoc_column_orders() -> None:
    assert Column("created_at").desc().order_key == "created_at.desc"


class TestEqualsTheStringBuilder:
    @pytest.mark.parametrize("desc", [False, True])
    @pytest.mark.parametrize("nullsfirst", [None, True, False])
    def test_order(
        self,
        select_builder: SelectRequestBuilder[SyncHttpIO],
        desc: bool,
        nullsfirst: bool | None,
    ) -> None:
        expected = select_builder.order(
            "x", desc=desc, nullsfirst=nullsfirst
        ).request.query.get("order")
        ordering = Column("x").desc() if desc else Column("x").asc()
        if nullsfirst is True:
            ordering = ordering.nulls_first()
        elif nullsfirst is False:
            ordering = ordering.nulls_last()

        assert ordering.order_key == expected
