from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from typing import Any

import pytest
from supabase_utils.http.headers import Headers
from supabase_utils.http.query import URLQuery

from postgrest.request_builder import BaseFilterRequestBuilder, PostgrestRequest
from postgrest.utils import sanitize_param


@pytest.fixture
def filter_request_builder() -> BaseFilterRequestBuilder:
    request = PostgrestRequest(
        path=["example_table"],
        method="GET",
        headers=Headers.empty(),
        query=URLQuery.empty(),
        body={},
    )
    return BaseFilterRequestBuilder(
        request=request,
        negate_next=False,
    )


def test_filter(filter_request_builder: BaseFilterRequestBuilder) -> None:
    builder = filter_request_builder.filter(":col.name", "eq", "val")

    assert builder.request.query['":col.name"'] == "eq.val"


@pytest.mark.parametrize(
    ("col_name", "expected_query_prefix"),
    [
        ("col:name", "%22col%3Aname%22"),
        ("col.name", "col.name"),
    ],
)
def test_filter_special_characters(
    filter_request_builder: BaseFilterRequestBuilder,
    col_name: str,
    expected_query_prefix: str,
) -> None:
    builder = filter_request_builder.filter(col_name, "eq", "val")

    assert builder.request.query.get(sanitize_param(col_name)) == "eq.val"


def test_multivalued_param(
    filter_request_builder: BaseFilterRequestBuilder,
) -> None:
    builder = filter_request_builder.lte("x", "a").gte("x", "b")

    assert builder.request.query.get_list("x") == ["lte.a", "gte.b"]


def test_match(filter_request_builder: BaseFilterRequestBuilder) -> None:
    builder = filter_request_builder.match({"id": "1", "done": "false"})
    assert builder.request.query.get("id") == "eq.1"
    assert builder.request.query.get("done") == "eq.false"


def test_equals(filter_request_builder: BaseFilterRequestBuilder) -> None:
    builder = filter_request_builder.eq("x", "a")

    assert builder.request.query.get("x") == "eq.a"


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, "eq.null"),
        (True, "eq.true"),
        (False, "eq.false"),
        ({"key": "value"}, 'eq.{"key":"value"}'),
        (["a", "b"], 'eq.["a","b"]'),
        ("a", "eq.a"),
        (42, "eq.42"),
    ],
)
def test_eq_serializes_values(
    filter_request_builder: BaseFilterRequestBuilder, value: Any, expected: str
) -> None:
    builder = filter_request_builder.eq("x", value)

    assert builder.request.query.get("x") == expected


@pytest.mark.parametrize("method", ["neq", "gt", "gte", "lt", "lte"])
@pytest.mark.parametrize(
    ("value", "expected"),
    [
        (None, "null"),
        (True, "true"),
        (False, "false"),
        ({"key": "value"}, '{"key":"value"}'),
        (["a", "b"], '["a","b"]'),
        ("a", "a"),
        (42, "42"),
    ],
)
def test_comparison_filters_serialize_values(
    filter_request_builder: BaseFilterRequestBuilder,
    method: str,
    value: Any,
    expected: str,
) -> None:
    builder = getattr(filter_request_builder, method)("x", value)

    assert builder.request.query.get("x") == f"{method}.{expected}"


def test_not_equal(filter_request_builder: BaseFilterRequestBuilder) -> None:
    builder = filter_request_builder.neq("x", "a")

    assert builder.request.query.get("x") == "neq.a"


def test_greater_than(filter_request_builder: BaseFilterRequestBuilder) -> None:
    builder = filter_request_builder.gt("x", "a")

    assert builder.request.query.get("x") == "gt.a"


def test_greater_than_or_equals_to(
    filter_request_builder: BaseFilterRequestBuilder,
) -> None:
    builder = filter_request_builder.gte("x", "a")

    assert builder.request.query.get("x") == "gte.a"


def test_contains(filter_request_builder: BaseFilterRequestBuilder) -> None:
    builder = filter_request_builder.contains("x", "a")

    assert builder.request.query.get("x") == "cs.a"


def test_contains_dictionary(filter_request_builder: BaseFilterRequestBuilder) -> None:
    builder = filter_request_builder.contains("x", {"a": "b"})

    # {"a":"b"}
    assert builder.request.query.get("x") == 'cs.{"a": "b"}'


def test_contains_any_item(filter_request_builder: BaseFilterRequestBuilder) -> None:
    builder = filter_request_builder.contains("x", ["a", "b"])

    # {a,b}
    assert builder.request.query.get("x") == "cs.{a,b}"


def test_contains_non_string_items(
    filter_request_builder: BaseFilterRequestBuilder,
) -> None:
    builder = filter_request_builder.contains("x", [1, 2, 3])

    assert builder.request.query.get("x") == "cs.{1,2,3}"


def test_cs_non_string_items(filter_request_builder: BaseFilterRequestBuilder) -> None:
    builder = filter_request_builder.cs("x", [1, 2, 3])

    assert builder.request.query.get("x") == "cs.{1,2,3}"


def test_cd_non_string_items(filter_request_builder: BaseFilterRequestBuilder) -> None:
    builder = filter_request_builder.cd("x", [1, 2, 3])

    assert builder.request.query.get("x") == "cd.{1,2,3}"


def test_contained_by_non_string_items(
    filter_request_builder: BaseFilterRequestBuilder,
) -> None:
    builder = filter_request_builder.contained_by("x", [1, 2, 3])

    assert builder.request.query.get("x") == "cd.{1,2,3}"


def test_overlaps_non_string_items(
    filter_request_builder: BaseFilterRequestBuilder,
) -> None:
    builder = filter_request_builder.overlaps("x", [1, 2, 3])

    assert builder.request.query.get("x") == "ov.{1,2,3}"


def test_contains_in_list(filter_request_builder: BaseFilterRequestBuilder) -> None:
    builder = filter_request_builder.contains("x", '[{"a": "b"}]')

    # [{"a":+"b"}] (the + represents the space)
    assert builder.request.query.get("x") == 'cs.[{"a": "b"}]'


def test_contained_by_mixed_items(
    filter_request_builder: BaseFilterRequestBuilder,
) -> None:
    builder = filter_request_builder.contained_by("x", ["a", '["b", "c"]'])

    assert builder.request.query.get("x") == 'cd.{a,"[\\"b\\", \\"c\\"]"}'


def test_contains_quotes_element_containing_the_delimiter(
    filter_request_builder: BaseFilterRequestBuilder,
) -> None:
    builder = filter_request_builder.contains("x", ["a,b", "c"])

    assert builder.request.query.get("x") == 'cs.{"a,b",c}'


def test_cs_quotes_element_containing_the_delimiter(
    filter_request_builder: BaseFilterRequestBuilder,
) -> None:
    builder = filter_request_builder.cs("x", ["a,b"])

    assert builder.request.query.get("x") == 'cs.{"a,b"}'


def test_cd_quotes_element_containing_the_delimiter(
    filter_request_builder: BaseFilterRequestBuilder,
) -> None:
    builder = filter_request_builder.cd("x", ["a,b"])

    assert builder.request.query.get("x") == 'cd.{"a,b"}'


def test_overlaps_quotes_element_containing_the_delimiter(
    filter_request_builder: BaseFilterRequestBuilder,
) -> None:
    builder = filter_request_builder.overlaps("x", ["a,b"])

    assert builder.request.query.get("x") == 'ov.{"a,b"}'


def test_contains_quotes_braces_quotes_whitespace_empty_and_null(
    filter_request_builder: BaseFilterRequestBuilder,
) -> None:
    builder = filter_request_builder.contains("x", ["a}b", 'x"y', "a b", "", "NULL"])

    assert builder.request.query.get("x") == 'cs.{"a}b","x\\"y","a b","","NULL"}'


def test_range_greater_than(filter_request_builder: BaseFilterRequestBuilder) -> None:
    builder = filter_request_builder.range_gt(
        "x", "2000-01-02 08:30", "2000-01-02 09:30"
    )

    assert builder.request.query.get("x") == "sr.(2000-01-02 08:30,2000-01-02 09:30)"


def test_range_greater_than_or_equal_to(
    filter_request_builder: BaseFilterRequestBuilder,
) -> None:
    builder = filter_request_builder.range_gte(
        "x", "2000-01-02 08:30", "2000-01-02 09:30"
    )

    # {a,["b",+"c"]}
    assert builder.request.query.get("x") == "nxl.(2000-01-02 08:30,2000-01-02 09:30)"


def test_range_less_than(filter_request_builder: BaseFilterRequestBuilder) -> None:
    builder = filter_request_builder.range_lt(
        "x", "2000-01-02 08:30", "2000-01-02 09:30"
    )

    # {a,["b",+"c"]}
    assert builder.request.query.get("x") == "sl.(2000-01-02 08:30,2000-01-02 09:30)"


def test_range_less_than_or_equal_to(
    filter_request_builder: BaseFilterRequestBuilder,
) -> None:
    builder = filter_request_builder.range_lte(
        "x", "2000-01-02 08:30", "2000-01-02 09:30"
    )

    # {a,["b",+"c"]}
    assert builder.request.query.get("x") == "nxr.(2000-01-02 08:30,2000-01-02 09:30)"


def test_range_adjacent(filter_request_builder: BaseFilterRequestBuilder) -> None:
    builder = filter_request_builder.range_adjacent(
        "x", "2000-01-02 08:30", "2000-01-02 09:30"
    )

    # {a,["b",+"c"]}
    assert builder.request.query.get("x") == "adj.(2000-01-02 08:30,2000-01-02 09:30)"


def test_overlaps(filter_request_builder: BaseFilterRequestBuilder) -> None:
    builder = filter_request_builder.overlaps("x", ["is:closed", "severity:high"])

    # {a,["b",+"c"]}
    assert builder.request.query.get("x") == "ov.{is:closed,severity:high}"


def test_overlaps_with_timestamp_range(
    filter_request_builder: BaseFilterRequestBuilder,
) -> None:
    builder = filter_request_builder.overlaps(
        "x", "[2000-01-01 12:45, 2000-01-01 13:15)"
    )

    # {a,["b",+"c"]}
    assert builder.request.query.get("x") == "ov.[2000-01-01 12:45, 2000-01-01 13:15)"


def test_like(filter_request_builder: BaseFilterRequestBuilder) -> None:
    builder = filter_request_builder.like("x", "%a%")

    assert builder.request.query.get("x") == "like.%a%"


def test_ilike(filter_request_builder: BaseFilterRequestBuilder) -> None:
    builder = filter_request_builder.ilike("x", "%a%")

    assert builder.request.query.get("x") == "ilike.%a%"


def test_like_all_of(filter_request_builder: BaseFilterRequestBuilder) -> None:
    builder = filter_request_builder.like_all_of("x", "A*,*b")

    assert builder.request.query.get("x") == "like(all).{A*,*b}"


def test_like_any_of(filter_request_builder: BaseFilterRequestBuilder) -> None:
    builder = filter_request_builder.like_any_of("x", "a*,*b")

    assert builder.request.query.get("x") == "like(any).{a*,*b}"


def test_ilike_all_of(filter_request_builder: BaseFilterRequestBuilder) -> None:
    builder = filter_request_builder.ilike_all_of("x", "A*,*b")

    assert builder.request.query.get("x") == "ilike(all).{A*,*b}"


def test_ilike_any_of(filter_request_builder: BaseFilterRequestBuilder) -> None:
    builder = filter_request_builder.ilike_any_of("x", "A*,*b")

    assert builder.request.query.get("x") == "ilike(any).{A*,*b}"


def test_is_(filter_request_builder: BaseFilterRequestBuilder) -> None:
    builder = filter_request_builder.is_("x", "a")

    assert builder.request.query.get("x") == "is.a"


def test_is_true(filter_request_builder: BaseFilterRequestBuilder) -> None:
    builder = filter_request_builder.is_("x", True)

    assert builder.request.query.get("x") == "is.true"


def test_is_false(filter_request_builder: BaseFilterRequestBuilder) -> None:
    builder = filter_request_builder.is_("x", False)

    assert builder.request.query.get("x") == "is.false"


def test_is_none(filter_request_builder: BaseFilterRequestBuilder) -> None:
    builder = filter_request_builder.is_("x", None)

    assert builder.request.query.get("x") == "is.null"


def test_in_(filter_request_builder: BaseFilterRequestBuilder) -> None:
    builder = filter_request_builder.in_("x", ["a", "b"])

    assert builder.request.query.get("x") == "in.(a,b)"


def test_in_renders_datetimes_as_iso_8601(
    filter_request_builder: BaseFilterRequestBuilder,
) -> None:
    values: Any = [datetime(2024, 1, 1, 12, tzinfo=UTC)]
    builder = filter_request_builder.in_("x", values)

    assert builder.request.query.get("x") == 'in.("2024-01-01T12:00:00+00:00")'


def test_or_(filter_request_builder: BaseFilterRequestBuilder) -> None:
    builder = filter_request_builder.or_("x.eq.1")

    assert builder.request.query.get("or") == "(x.eq.1)"


def test_not_or_(filter_request_builder: BaseFilterRequestBuilder) -> None:
    builder = filter_request_builder.not_.or_("x.eq.1")

    assert builder.request.query.get("not.or") == "(x.eq.1)"
    assert "or" not in builder.request.query
    assert builder.eq("y", "2").request.query.get("y") == "eq.2"

    foreign = filter_request_builder.not_.or_("x.eq.1", reference_table="cities")
    assert foreign.request.query.get("cities.not.or") == "(x.eq.1)"
    assert foreign.eq("y", "2").request.query.get("y") == "eq.2"


def test_not_leaves_the_receiver_unchanged(
    filter_request_builder: BaseFilterRequestBuilder,
) -> None:
    negated = filter_request_builder.not_

    assert negated.request == filter_request_builder.request
    assert filter_request_builder.eq("x", "a").request.query.get("x") == "eq.a"
    assert negated.eq("x", "a").request.query.get("x") == "not.eq.a"
    assert negated.or_("x.eq.1").request.query.get("not.or") == "(x.eq.1)"


def test_filters_branch_from_one_base(
    filter_request_builder: BaseFilterRequestBuilder,
) -> None:
    base = filter_request_builder.eq("account_id", "abc")
    first = base.in_("id", ["1", "2", "3"])
    second = base.in_("id", ["4", "5", "6"])

    assert "id" not in base.request.query
    assert first.request.query.get_list("id") == ["in.(1,2,3)"]
    assert second.request.query.get_list("id") == ["in.(4,5,6)"]
    assert "account_id" not in filter_request_builder.request.query


def test_builders_are_frozen(
    filter_request_builder: BaseFilterRequestBuilder,
) -> None:
    with pytest.raises(FrozenInstanceError):
        filter_request_builder.negate_next = True  # pyrefly: ignore[read-only]
    with pytest.raises(FrozenInstanceError):
        filter_request_builder.request.retry = False  # pyrefly: ignore[read-only]


def test_or_in_contain(filter_request_builder: BaseFilterRequestBuilder) -> None:
    builder = filter_request_builder.or_("id.in.(5,6,7), arraycol.cs.{'a','b'}")

    assert builder.request.query.get("or") == "(id.in.(5,6,7), arraycol.cs.{'a','b'})"


def test_max_affected(filter_request_builder: BaseFilterRequestBuilder) -> None:
    builder = filter_request_builder.max_affected(5)

    assert builder.request.headers.get_list("prefer") == [
        "handling=strict",
        "max-affected=5",
    ]
    assert "prefer" not in filter_request_builder.request.headers


def with_prefer_header(
    builder: BaseFilterRequestBuilder, prefer: str
) -> BaseFilterRequestBuilder:
    headers = builder.request.headers.set("prefer", prefer)
    return replace(builder, request=replace(builder.request, headers=headers))


def test_max_affected_with_existing_prefer_header(
    filter_request_builder: BaseFilterRequestBuilder,
) -> None:
    builder = with_prefer_header(
        filter_request_builder, "return=representation"
    ).max_affected(10)

    assert builder.request.headers.get_list("prefer") == [
        "return=representation",
        "handling=strict",
        "max-affected=10",
    ]


def test_max_affected_with_existing_handling_strict(
    filter_request_builder: BaseFilterRequestBuilder,
) -> None:
    builder = with_prefer_header(
        filter_request_builder, "handling=strict,return=minimal"
    ).max_affected(3)

    assert builder.request.headers.get_list("prefer") == [
        "return=minimal",
        "handling=strict",
        "max-affected=3",
    ]


def test_max_affected_called_twice_replaces_its_preferences(
    filter_request_builder: BaseFilterRequestBuilder,
) -> None:
    builder = (
        with_prefer_header(filter_request_builder, "return=representation")
        .max_affected(3)
        .max_affected(7)
    )

    assert builder.request.headers.get_list("prefer") == [
        "return=representation",
        "handling=strict",
        "max-affected=7",
    ]


def test_max_affected_replaces_another_handling_preference(
    filter_request_builder: BaseFilterRequestBuilder,
) -> None:
    builder = with_prefer_header(
        filter_request_builder, "handling=lenient, max-affected=1"
    ).max_affected(2)

    assert builder.request.headers.get_list("prefer") == [
        "handling=strict",
        "max-affected=2",
    ]
