import json
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import StrEnum
from types import MappingProxyType
from typing import Any

import pytest
from pydantic import JsonValue

from postgrest import Column, Filter, FilterOperator, Filters, NullableColumn, Range
from postgrest.request_builder import BaseFilterRequestBuilder


class PostRow:
    pass


class Mood(StrEnum):
    HAPPY = "happy"
    VERY_HAPPY = "very happy"


class Posts:
    id = Column[PostRow, int]("id")
    content = Column[PostRow, str]("content")
    tags = Column[PostRow, list[str]]("tags")
    labels = NullableColumn[PostRow, list[str]]("labels")
    moods = Column[PostRow, list[Mood]]("moods")
    metadata = Column[PostRow, JsonValue]("metadata")
    scheduled = Column[PostRow, Range[int]]("scheduled")
    during = Column[PostRow, Range[datetime]]("during")
    season = Column[PostRow, Range[date]]("season")


def rendered(filter_: Filter[Any]) -> list[str]:
    return [f"{key}={value}" for key, value in filter_._query_parameters()]


def typed_values(filter_: Filter[Any], key: str) -> list[str]:
    return [value for name, value in filter_._query_parameters() if name == key]


class TestPatternOperators:
    def test_render_their_wire_operator(self) -> None:
        assert rendered(Posts.content.like("%a%")) == ["content=like.%a%"]
        assert rendered(Posts.content.ilike("%a%")) == ["content=ilike.%a%"]
        assert rendered(Posts.content.match_regex("^a")) == ["content=match.^a"]
        assert rendered(Posts.content.imatch_regex("^a")) == ["content=imatch.^a"]

    def test_the_quantified_forms_take_an_array_literal(self) -> None:
        assert rendered(Posts.content.like_all_of(["%a%", "%b%"])) == [
            "content=like(all).{%a%,%b%}"
        ]
        assert rendered(Posts.content.like_any_of(["%a%", "%b%"])) == [
            "content=like(any).{%a%,%b%}"
        ]
        assert rendered(Posts.content.ilike_all_of(["%a%", "%b%"])) == [
            "content=ilike(all).{%a%,%b%}"
        ]
        assert rendered(Posts.content.ilike_any_of(["%a%", "%b%"])) == [
            "content=ilike(any).{%a%,%b%}"
        ]

    def test_quantified_members_are_escaped_as_array_elements(self) -> None:
        assert rendered(Posts.content.like_any_of(["a,b", "c"])) == [
            'content=like(any).{"a,b",c}'
        ]
        assert rendered(Posts.content.like_all_of(["a{b", 'a"b'])) == [
            'content=like(all).{"a{b","a\\"b"}'
        ]

    def test_the_quantified_forms_accept_any_iterable(self) -> None:
        assert rendered(Posts.content.like_any_of(("%a%", "%b%"))) == [
            "content=like(any).{%a%,%b%}"
        ]
        assert rendered(
            Posts.content.ilike_all_of(f"%{letter}%" for letter in "ab")
        ) == ["content=ilike(all).{%a%,%b%}"]

    def test_an_empty_pattern_list_renders_empty_braces(self) -> None:
        assert rendered(Posts.content.like_all_of([])) == ["content=like(all).{}"]

    def test_the_quantified_forms_reject_one_string(self) -> None:
        with pytest.raises(TypeError, match="like_all_of\\(\\) takes an iterable"):
            Posts.content.like_all_of("%a%")  # pyrefly: ignore[string-as-iterable]
        with pytest.raises(TypeError, match="ilike_any_of\\(\\) takes an iterable"):
            Posts.content.ilike_any_of("%a%")  # pyrefly: ignore[string-as-iterable]

    def test_negate_and_group_like_a_comparison(self) -> None:
        assert rendered(~Posts.content.like("%a%")) == ["content=not.like.%a%"]
        assert rendered(Posts.content.ilike("%a%") | Posts.id.eq(1)) == [
            "or=(content.ilike.%a%,id.eq.1)"
        ]
        assert rendered(~Posts.content.like_any_of(["a,b"]) | Posts.id.eq(1)) == [
            'or=(content.not.like(any)."{\\"a,b\\"}",id.eq.1)'
        ]

    def test_a_pattern_with_reserved_characters_is_quoted_in_a_group(self) -> None:
        assert rendered(Posts.content.like("a(b)%")) == ["content=like.a(b)%"]
        assert rendered(Posts.content.like("a(b)%") | Posts.id.eq(1)) == [
            'or=(content.like."a(b)%",id.eq.1)'
        ]


class TestArrayOperators:
    def test_render_a_braced_array(self) -> None:
        assert rendered(Posts.tags.contains(["python"])) == ["tags=cs.{python}"]
        assert rendered(Posts.tags.contained_by(["python", "typing"])) == [
            "tags=cd.{python,typing}"
        ]
        assert rendered(Posts.tags.overlaps(["python"])) == ["tags=ov.{python}"]

    def test_members_are_escaped_as_array_elements(self) -> None:
        assert rendered(Posts.tags.contains(["a{b"])) == ['tags=cs.{"a{b"}']
        assert rendered(Posts.tags.contained_by(["a,b"])) == ['tags=cd.{"a,b"}']
        assert rendered(Posts.tags.overlaps(['a"b\\c'])) == ['tags=ov.{"a\\"b\\\\c"}']
        assert rendered(Posts.tags.contains(["a b", "", "null"])) == [
            'tags=cs.{"a b","","null"}'
        ]

    def test_a_none_member_is_sql_null(self) -> None:
        assert rendered(Posts.tags.contains(["a", None])) == ["tags=cs.{a,NULL}"]
        assert rendered(Posts.labels.overlaps([None])) == ["labels=ov.{NULL}"]

    def test_members_render_like_other_operands(self) -> None:
        assert rendered(Posts.moods.contains([Mood.HAPPY, Mood.VERY_HAPPY])) == [
            'moods=cs.{happy,"very happy"}'
        ]
        assert rendered(Column("ids").contains([1, 2])) == ["ids=cs.{1,2}"]
        assert rendered(Column("flags").contains([True, False])) == [
            "flags=cs.{true,false}"
        ]
        assert rendered(Column("items").contains([{"a": 1}])) == [
            'items=cs.{"{\\"a\\":1}"}'
        ]

    def test_a_mapping_of_any_kind_is_sent_as_json(self) -> None:
        assert rendered(Posts.metadata.contains(MappingProxyType({"a": 1}))) == [
            'metadata=cs.{"a":1}'
        ]

    def test_an_empty_array_renders_empty_braces(self) -> None:
        assert rendered(Posts.tags.contains([])) == ["tags=cs.{}"]

    def test_accept_any_iterable(self) -> None:
        assert rendered(Posts.tags.contains(("a", "b"))) == ["tags=cs.{a,b}"]
        assert rendered(Posts.tags.overlaps({"a"})) == ["tags=ov.{a}"]
        assert rendered(Posts.tags.contained_by(letter for letter in "ab")) == [
            "tags=cd.{a,b}"
        ]

    def test_reject_one_string(self) -> None:
        with pytest.raises(TypeError, match="contains\\(\\) takes an iterable"):
            Posts.tags.contains("abc")
        with pytest.raises(TypeError, match="overlaps\\(\\) takes an iterable"):
            Column("x").overlaps("[1,2)")

    def test_negate_as_not(self) -> None:
        assert rendered(~Posts.tags.contains(["a"])) == ["tags=not.cs.{a}"]

    def test_the_literal_is_quoted_inside_a_group(self) -> None:
        assert rendered(Posts.tags.contains(["a", "b"]) | Posts.id.eq(1)) == [
            'or=(tags.cs."{a,b}",id.eq.1)'
        ]
        assert rendered(~Posts.tags.overlaps(["a,b"]) | Posts.id.eq(1)) == [
            'or=(tags.not.ov."{\\"a,b\\"}",id.eq.1)'
        ]

    def test_an_array_column_compares_with_json_as_the_string_builder_does(
        self,
    ) -> None:
        assert rendered(Posts.tags.eq(["a", "b"])) == ['tags=eq.["a","b"]']


class TestRangeOperators:
    def test_render_their_abbreviation(self) -> None:
        range_ = Range(2, 25)
        assert rendered(Posts.scheduled.range_lt(range_)) == ["scheduled=sl.[2,25)"]
        assert rendered(Posts.scheduled.range_gt(range_)) == ["scheduled=sr.[2,25)"]
        assert rendered(Posts.scheduled.range_gte(range_)) == ["scheduled=nxl.[2,25)"]
        assert rendered(Posts.scheduled.range_lte(range_)) == ["scheduled=nxr.[2,25)"]
        assert rendered(Posts.scheduled.range_adjacent(range_)) == [
            "scheduled=adj.[2,25)"
        ]

    def test_containment_takes_a_range_or_a_single_value(self) -> None:
        assert rendered(Posts.scheduled.contains(Range(21, 22))) == [
            "scheduled=cs.[21,22)"
        ]
        assert rendered(Posts.scheduled.contains(21)) == ["scheduled=cs.21"]
        assert rendered(Posts.scheduled.contained_by(Range(21, 22, "[]"))) == [
            "scheduled=cd.[21,22]"
        ]
        assert rendered(Posts.scheduled.overlaps(Range(25, 35, "()"))) == [
            "scheduled=ov.(25,35)"
        ]

    def test_bounds_render_as_filter_values(self) -> None:
        assert rendered(
            Posts.during.overlaps(
                Range(
                    datetime(2024, 1, 1, tzinfo=UTC), datetime(2025, 1, 1, tzinfo=UTC)
                )
            )
        ) == ["during=ov.[2024-01-01 00:00:00+00:00,2025-01-01 00:00:00+00:00)"]
        assert rendered(Posts.during.contains(datetime(2024, 6, 1, tzinfo=UTC))) == [
            "during=cs.2024-06-01 00:00:00+00:00"
        ]
        assert rendered(
            Posts.season.contained_by(Range(date(2024, 1, 1), date(2024, 2, 1)))
        ) == ["season=cd.[2024-01-01,2024-02-01)"]

    def test_an_unbounded_side_renders_empty(self) -> None:
        assert rendered(Posts.scheduled.range_lt(Range(None, 25))) == [
            "scheduled=sl.[,25)"
        ]
        assert rendered(Posts.scheduled.range_gt(Range(2, None, "(]"))) == [
            "scheduled=sr.(2,]"
        ]

    def test_a_range_operand_is_quoted_inside_a_group(self) -> None:
        assert rendered(Posts.scheduled.overlaps(Range(25, 35)) | Posts.id.eq(3)) == [
            'or=(scheduled.ov."[25,35)",id.eq.3)'
        ]
        assert rendered(~Posts.scheduled.range_lt(Range(2, 25)) | Posts.id.eq(3)) == [
            'or=(scheduled.not.sl."[2,25)",id.eq.3)'
        ]

    def test_negates_as_not(self) -> None:
        assert rendered(~Posts.scheduled.range_adjacent(Range(2, 25))) == [
            "scheduled=not.adj.[2,25)"
        ]

    def test_a_range_column_compares_against_a_range(self) -> None:
        assert rendered(Posts.scheduled.eq(Range(2, 25))) == ["scheduled=eq.[2,25)"]
        assert rendered(Posts.scheduled.in_([Range(2, 25), Range(30, 40)])) == [
            'scheduled=in.("[2,25)","[30,40)")'
        ]


class TestJsonOperators:
    def test_containment_encodes_the_object(self) -> None:
        assert rendered(Posts.metadata.contains({"a": 1})) == ['metadata=cs.{"a":1}']
        assert rendered(Posts.metadata.contained_by({"a": 1, "b": [2, "x"]})) == [
            'metadata=cd.{"a":1,"b":[2,"x"]}'
        ]

    def test_the_object_is_quoted_inside_a_group(self) -> None:
        assert rendered(Posts.metadata.contains({"a": 1}) | Posts.id.eq(1)) == [
            'or=(metadata.cs."{\\"a\\":1}",id.eq.1)'
        ]

    def test_negates_as_not(self) -> None:
        assert rendered(~Posts.metadata.contains({"a": None})) == [
            'metadata=not.cs.{"a":null}'
        ]


class TestOperators:
    def test_the_enum_carries_the_tokens_of_the_string_builder(self) -> None:
        assert FilterOperator.LIKE == Filters.LIKE
        assert FilterOperator.ILIKE == Filters.ILIKE
        assert FilterOperator.LIKE_ALL_OF == Filters.LIKE_ALL
        assert FilterOperator.LIKE_ANY_OF == Filters.LIKE_ANY
        assert FilterOperator.ILIKE_ALL_OF == Filters.ILIKE_ALL
        assert FilterOperator.ILIKE_ANY_OF == Filters.ILIKE_ANY
        assert FilterOperator.CONTAINS == Filters.CS
        assert FilterOperator.CONTAINED_BY == Filters.CD
        assert FilterOperator.OVERLAPS == Filters.OV
        assert FilterOperator.RANGE_LT == Filters.SL
        assert FilterOperator.RANGE_GT == Filters.SR
        assert FilterOperator.RANGE_GTE == Filters.NXL
        assert FilterOperator.RANGE_LTE == Filters.NXR
        assert FilterOperator.RANGE_ADJACENT == Filters.ADJ
        assert FilterOperator.MATCH_REGEX == "match"
        assert FilterOperator.IMATCH_REGEX == "imatch"

    def test_a_comparison_exposes_the_operand_as_given(self) -> None:
        contains = Posts.tags.contains(["a", "b"]).comparison
        assert contains is not None
        assert contains.operator is FilterOperator.CONTAINS
        assert contains.value == ("a", "b")

        range_ = Posts.scheduled.range_lt(Range(2, 25)).comparison
        assert range_ is not None
        assert range_.operator is FilterOperator.RANGE_LT
        assert range_.value == Range(2, 25)

        json_comparison = (~Posts.metadata.contains({"a": 1})).comparison
        assert json_comparison is not None
        assert json_comparison.value == {"a": 1}
        assert json_comparison.negated

        patterns = Posts.content.like_all_of(["%a%"]).comparison
        assert patterns is not None
        assert patterns.operator is FilterOperator.LIKE_ALL_OF
        assert patterns.value == ("%a%",)


PATTERNS = ["%a%", "a_b", "a,b", "p(q)", 'a"b\\c', "a b", "*a*", ""]

ARRAYS: list[list[Any]] = [
    ["a", "b"],
    [],
    ["a,b", "a{b", 'a"b', "a\\b", "a b", "", "null", "NULL"],
    [1, 2.5, Decimal("1.25"), None],
    [datetime(2024, 1, 15, 12, tzinfo=UTC), date(2024, 1, 15), Mood.VERY_HAPPY],
]
"""Members the string builder renders as the typed operators do. A boolean
member is left out, since the string builder sends it as `True` where every
typed operand is `true`, which Postgres reads alike."""

RANGES = [
    Range(1, 2),
    Range(1, 2, "()"),
    Range(1, 2, "[]"),
    Range(1, 2, "(]"),
    Range(None, 2),
    Range(1, None),
    Range(None, None),
    Range(date(2024, 1, 1), date(2024, 2, 1)),
    Range(datetime(2024, 1, 1, tzinfo=UTC), datetime(2024, 2, 1, tzinfo=UTC)),
    Range(Decimal("1.5"), Decimal("2.5")),
]


class TestEqualsTheStringBuilder:
    @pytest.mark.parametrize("method", ["like", "ilike"])
    @pytest.mark.parametrize("pattern", PATTERNS)
    def test_pattern(
        self, builder: BaseFilterRequestBuilder, method: str, pattern: str
    ) -> None:
        expected = getattr(builder, method)("x", pattern).request.query.get_list("x")
        negated = getattr(builder.not_, method)("x", pattern).request.query.get_list(
            "x"
        )

        filter_: Filter[Any] = getattr(Column("x"), method)(pattern)

        assert typed_values(filter_, "x") == expected
        assert typed_values(~filter_, "x") == negated

    @pytest.mark.parametrize(
        ("method", "operator"),
        [("match_regex", "match"), ("imatch_regex", "imatch")],
    )
    @pytest.mark.parametrize("pattern", ["^a", "a|b", "a(b)", "a,b", 'a"b'])
    def test_regular_expression(
        self,
        builder: BaseFilterRequestBuilder,
        method: str,
        operator: str,
        pattern: str,
    ) -> None:
        expected = builder.filter("x", operator, pattern).request.query.get_list("x")

        assert typed_values(getattr(Column("x"), method)(pattern), "x") == expected

    @pytest.mark.parametrize(
        "method", ["like_all_of", "like_any_of", "ilike_all_of", "ilike_any_of"]
    )
    @pytest.mark.parametrize(
        "patterns", [["%a%"], ["%a%", "%b%"], ["a_b", "a%b"], ["*a*", "b"], []]
    )
    def test_quantified_pattern(
        self, builder: BaseFilterRequestBuilder, method: str, patterns: list[str]
    ) -> None:
        """The string builder wraps one comma-separated string in braces as
        given, so the patterns here are ones the array literal needs no
        quoting for."""
        literal = ",".join(patterns)
        expected = getattr(builder, method)("x", literal).request.query.get_list("x")
        negated = getattr(builder.not_, method)("x", literal).request.query.get_list(
            "x"
        )

        filter_: Filter[Any] = getattr(Column("x"), method)(patterns)

        assert typed_values(filter_, "x") == expected
        assert typed_values(~filter_, "x") == negated

    @pytest.mark.parametrize("method", ["contains", "contained_by", "overlaps"])
    @pytest.mark.parametrize("values", ARRAYS)
    def test_array(
        self, builder: BaseFilterRequestBuilder, method: str, values: list[Any]
    ) -> None:
        expected = getattr(builder, method)("x", values).request.query.get_list("x")
        negated = getattr(builder.not_, method)("x", values).request.query.get_list("x")

        filter_: Filter[Any] = getattr(Column("x"), method)(values)

        assert typed_values(filter_, "x") == expected
        assert typed_values(~filter_, "x") == negated

    @pytest.mark.parametrize("method", ["contains", "contained_by"])
    @pytest.mark.parametrize(
        "value",
        [{"a": 1}, {"a": {"b": [1, "x", None, True]}}, {"a,b": 'q"uote'}, {}],
    )
    def test_json(
        self, builder: BaseFilterRequestBuilder, method: str, value: dict[str, Any]
    ) -> None:
        """The string builder's `contains()` encodes with a space after each
        colon where its `eq()` and the typed operators are compact, so the
        two are compared as JSON."""
        (expected,) = getattr(builder, method)("x", value).request.query.get_list("x")
        (typed,) = typed_values(getattr(Column("x"), method)(value), "x")
        token, _, expected_json = expected.partition(".")
        typed_token, _, typed_json = typed.partition(".")

        assert typed_token == token
        assert json.loads(typed_json) == json.loads(expected_json)

    @pytest.mark.parametrize("method", ["contains", "contained_by", "overlaps"])
    @pytest.mark.parametrize("range_", RANGES)
    def test_range_containment(
        self, builder: BaseFilterRequestBuilder, method: str, range_: Range[Any]
    ) -> None:
        expected = getattr(builder, method)("x", str(range_)).request.query.get_list(
            "x"
        )

        assert typed_values(getattr(Column("x"), method)(range_), "x") == expected

    @pytest.mark.parametrize(
        "method", ["range_lt", "range_gt", "range_gte", "range_lte", "range_adjacent"]
    )
    @pytest.mark.parametrize(
        ("lower", "upper"), [("1", "2"), ("2024-01-01", "2024-02-01"), ("", "2")]
    )
    def test_range(
        self, builder: BaseFilterRequestBuilder, method: str, lower: str, upper: str
    ) -> None:
        expected = getattr(builder, method)("x", lower, upper).request.query.get_list(
            "x"
        )
        negated = getattr(builder.not_, method)(
            "x", lower, upper
        ).request.query.get_list("x")
        range_ = Range(lower or None, upper, "()")

        filter_: Filter[Any] = getattr(Column("x"), method)(range_)

        assert typed_values(filter_, "x") == expected
        assert typed_values(~filter_, "x") == negated

    @pytest.mark.parametrize(
        "method", ["range_lt", "range_gt", "range_gte", "range_lte", "range_adjacent"]
    )
    @pytest.mark.parametrize("range_", RANGES)
    def test_range_with_other_bounds(
        self, builder: BaseFilterRequestBuilder, method: str, range_: Range[Any]
    ) -> None:
        token = getattr(
            Filters,
            {
                "range_lt": "SL",
                "range_gt": "SR",
                "range_gte": "NXL",
                "range_lte": "NXR",
                "range_adjacent": "ADJ",
            }[method],
        )
        expected = builder.filter("x", token, str(range_)).request.query.get_list("x")

        assert typed_values(getattr(Column("x"), method)(range_), "x") == expected

    def test_a_range_in_a_group(self, builder: BaseFilterRequestBuilder) -> None:
        expected = builder.or_('x.ov."[25,35)",id.eq.3').request.query.get_list("or")

        assert (
            typed_values(Column("x").overlaps(Range(25, 35)) | Column("id").eq(3), "or")
            == expected
        )

    def test_an_array_in_a_group(self, builder: BaseFilterRequestBuilder) -> None:
        expected = builder.or_('x.cs."{a,b}",id.eq.3').request.query.get_list("or")

        assert (
            typed_values(Column("x").contains(["a", "b"]) | Column("id").eq(3), "or")
            == expected
        )
