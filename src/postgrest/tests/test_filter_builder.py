from typing import Iterable

import pytest
from supabase_utils.http.headers import Headers
from supabase_utils.http.query import URLQuery
from supabase_utils.http.request import JSONRequest

from postgrest.request_builder import BaseFilterRequestBuilder
from postgrest.utils import sanitize_param


@pytest.fixture
def filter_request_builder() -> Iterable[BaseFilterRequestBuilder]:
    request = JSONRequest(
        path=["example_table"],
        method="GET",
        headers=Headers.empty(),
        query=URLQuery.empty(),
        body={},
    )
    yield BaseFilterRequestBuilder(
        request=request,
        negate_next=False,
    )


def test_filter(filter_request_builder: BaseFilterRequestBuilder) -> None:
    builder = filter_request_builder.filter(":col.name", "eq", "val")

    assert builder.request.query['":col.name"'] == "eq.val"


@pytest.mark.parametrize(
    "col_name, expected_query_prefix",
    [
        ("col:name", "%22col%3Aname%22"),
        ("col.name", "col.name"),
    ],
)
def test_filter_special_characters(
    filter_request_builder: BaseFilterRequestBuilder,
    col_name: str,
    expected_query_prefix: str,
):
    builder = filter_request_builder.filter(col_name, "eq", "val")

    assert builder.request.query.get(sanitize_param(col_name)) == "eq.val"


def test_multivalued_param(
    filter_request_builder: BaseFilterRequestBuilder,
) -> None:
    builder = filter_request_builder.lte("x", "a").gte("x", "b")

    assert builder.request.query.get_list("x") == ["lte.a", "gte.b"]


def test_match(filter_request_builder: BaseFilterRequestBuilder):
    builder = filter_request_builder.match({"id": "1", "done": "false"})
    assert builder.request.query.get("id") == "eq.1"
    assert builder.request.query.get("done") == "eq.false"


def test_equals(filter_request_builder: BaseFilterRequestBuilder):
    builder = filter_request_builder.eq("x", "a")

    assert builder.request.query.get("x") == "eq.a"


def test_not_equal(filter_request_builder: BaseFilterRequestBuilder):
    builder = filter_request_builder.neq("x", "a")

    assert builder.request.query.get("x") == "neq.a"


def test_greater_than(filter_request_builder: BaseFilterRequestBuilder):
    builder = filter_request_builder.gt("x", "a")

    assert builder.request.query.get("x") == "gt.a"


def test_greater_than_or_equals_to(
    filter_request_builder: BaseFilterRequestBuilder,
):
    builder = filter_request_builder.gte("x", "a")

    assert builder.request.query.get("x") == "gte.a"


def test_contains(filter_request_builder: BaseFilterRequestBuilder):
    builder = filter_request_builder.contains("x", "a")

    assert builder.request.query.get("x") == "cs.a"


def test_contains_dictionary(filter_request_builder: BaseFilterRequestBuilder):
    builder = filter_request_builder.contains("x", {"a": "b"})

    # {"a":"b"}
    assert builder.request.query.get("x") == 'cs.{"a": "b"}'


def test_contains_any_item(filter_request_builder: BaseFilterRequestBuilder):
    builder = filter_request_builder.contains("x", ["a", "b"])

    # {a,b}
    assert builder.request.query.get("x") == "cs.{a,b}"


def test_contains_in_list(filter_request_builder: BaseFilterRequestBuilder):
    builder = filter_request_builder.contains("x", '[{"a": "b"}]')

    # [{"a":+"b"}] (the + represents the space)
    assert builder.request.query.get("x") == 'cs.[{"a": "b"}]'


def test_contained_by_mixed_items(
    filter_request_builder: BaseFilterRequestBuilder,
):
    builder = filter_request_builder.contained_by("x", ["a", '["b", "c"]'])

    # {a,["b",+"c"]}
    assert builder.request.query.get("x") == 'cd.{a,["b", "c"]}'


def test_range_greater_than(filter_request_builder: BaseFilterRequestBuilder):
    builder = filter_request_builder.range_gt(
        "x", "2000-01-02 08:30", "2000-01-02 09:30"
    )

    assert builder.request.query.get("x") == "sr.(2000-01-02 08:30,2000-01-02 09:30)"


def test_range_greater_than_or_equal_to(
    filter_request_builder: BaseFilterRequestBuilder,
):
    builder = filter_request_builder.range_gte(
        "x", "2000-01-02 08:30", "2000-01-02 09:30"
    )

    # {a,["b",+"c"]}
    assert builder.request.query.get("x") == "nxl.(2000-01-02 08:30,2000-01-02 09:30)"


def test_range_less_than(filter_request_builder: BaseFilterRequestBuilder):
    builder = filter_request_builder.range_lt(
        "x", "2000-01-02 08:30", "2000-01-02 09:30"
    )

    # {a,["b",+"c"]}
    assert builder.request.query.get("x") == "sl.(2000-01-02 08:30,2000-01-02 09:30)"


def test_range_less_than_or_equal_to(
    filter_request_builder: BaseFilterRequestBuilder,
):
    builder = filter_request_builder.range_lte(
        "x", "2000-01-02 08:30", "2000-01-02 09:30"
    )

    # {a,["b",+"c"]}
    assert builder.request.query.get("x") == "nxr.(2000-01-02 08:30,2000-01-02 09:30)"


def test_range_adjacent(filter_request_builder: BaseFilterRequestBuilder):
    builder = filter_request_builder.range_adjacent(
        "x", "2000-01-02 08:30", "2000-01-02 09:30"
    )

    # {a,["b",+"c"]}
    assert builder.request.query.get("x") == "adj.(2000-01-02 08:30,2000-01-02 09:30)"


def test_overlaps(filter_request_builder: BaseFilterRequestBuilder):
    builder = filter_request_builder.overlaps("x", ["is:closed", "severity:high"])

    # {a,["b",+"c"]}
    assert builder.request.query.get("x") == "ov.{is:closed,severity:high}"


def test_overlaps_with_timestamp_range(
    filter_request_builder: BaseFilterRequestBuilder,
):
    builder = filter_request_builder.overlaps(
        "x", "[2000-01-01 12:45, 2000-01-01 13:15)"
    )

    # {a,["b",+"c"]}
    assert builder.request.query.get("x") == "ov.[2000-01-01 12:45, 2000-01-01 13:15)"


def test_like(filter_request_builder: BaseFilterRequestBuilder):
    builder = filter_request_builder.like("x", "%a%")

    assert builder.request.query.get("x") == "like.%a%"


def test_ilike(filter_request_builder: BaseFilterRequestBuilder):
    builder = filter_request_builder.ilike("x", "%a%")

    assert builder.request.query.get("x") == "ilike.%a%"


def test_like_all_of(filter_request_builder: BaseFilterRequestBuilder):
    builder = filter_request_builder.like_all_of("x", "A*,*b")

    assert builder.request.query.get("x") == "like(all).{A*,*b}"


def test_like_any_of(filter_request_builder: BaseFilterRequestBuilder):
    builder = filter_request_builder.like_any_of("x", "a*,*b")

    assert builder.request.query.get("x") == "like(any).{a*,*b}"


def test_ilike_all_of(filter_request_builder: BaseFilterRequestBuilder):
    builder = filter_request_builder.ilike_all_of("x", "A*,*b")

    assert builder.request.query.get("x") == "ilike(all).{A*,*b}"


def test_ilike_any_of(filter_request_builder: BaseFilterRequestBuilder):
    builder = filter_request_builder.ilike_any_of("x", "A*,*b")

    assert builder.request.query.get("x") == "ilike(any).{A*,*b}"


def test_is_(filter_request_builder: BaseFilterRequestBuilder):
    builder = filter_request_builder.is_("x", "a")

    assert builder.request.query.get("x") == "is.a"


def test_in_(filter_request_builder: BaseFilterRequestBuilder):
    builder = filter_request_builder.in_("x", ["a", "b"])

    assert builder.request.query.get("x") == "in.(a,b)"


def test_or_(filter_request_builder: BaseFilterRequestBuilder):
    builder = filter_request_builder.or_("x.eq.1")

    assert builder.request.query.get("or") == "(x.eq.1)"


def test_or_in_contain(filter_request_builder: BaseFilterRequestBuilder):
    builder = filter_request_builder.or_("id.in.(5,6,7), arraycol.cs.{'a','b'}")

    assert builder.request.query.get("or") == "(id.in.(5,6,7), arraycol.cs.{'a','b'})"


def test_max_affected(filter_request_builder: BaseFilterRequestBuilder):
    builder = filter_request_builder.max_affected(5)

    assert builder.request.headers.get_list("prefer") == [
        "handling=strict",
        "max-affected=5",
    ]


def test_max_affected_with_existing_prefer_header(
    filter_request_builder: BaseFilterRequestBuilder,
):
    # Set an existing prefer header
    filter_request_builder.request.headers = filter_request_builder.request.headers.set(
        "prefer", "return=representation"
    )
    builder = filter_request_builder.max_affected(10)

    assert builder.request.headers.get_list("prefer") == [
        "return=representation",
        "handling=strict",
        "max-affected=10",
    ]


def test_max_affected_with_existing_handling_strict(
    filter_request_builder: BaseFilterRequestBuilder,
):
    # Set an existing prefer header with handling=strict
    filter_request_builder.request.headers = filter_request_builder.request.headers.set(
        "prefer", "handling=strict,return=minimal"
    )
    builder = filter_request_builder.max_affected(3)

    assert builder.request.headers.get_list("prefer") == [
        "handling=strict,return=minimal",
        "handling=strict",
        "max-affected=3",
    ]
