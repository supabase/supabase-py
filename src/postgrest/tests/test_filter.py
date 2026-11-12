from datetime import UTC, datetime
from decimal import Decimal
from enum import StrEnum
from functools import reduce
from operator import or_
from typing import Any
from uuid import UUID

import pytest
from supabase_utils.http.io import SyncHttpIO

from postgrest import (
    Column,
    Comparison,
    ComputedField,
    Filter,
    FilterOperator,
    Filters,
    NullableColumn,
    TextSearchType,
)
from postgrest.request_builder import BaseFilterRequestBuilder, SelectRequestBuilder
from postgrest.utils import sanitize_param


class TodoRow:
    pass


class Mood(StrEnum):
    HAPPY = "happy"
    VERY_HAPPY = "very happy"


class Todos:
    a = Column[TodoRow, int]("a")
    b = Column[TodoRow, int]("b")
    c = Column[TodoRow, int]("c")
    id = Column[TodoRow, int]("id")
    name = Column[TodoRow, str]("name")
    cost = Column[TodoRow, float]("cost")
    is_done = Column[TodoRow, bool]("is_done")
    data = Column[TodoRow, dict[str, Any]]("data")
    mood = Column[TodoRow, Mood]("mood")
    due = NullableColumn[TodoRow, datetime]("due")
    is_urgent = NullableColumn[TodoRow, bool]("is_urgent")
    full_name = ComputedField[TodoRow, str]("full_name")


def rendered(filter_: Filter[Any]) -> list[str]:
    return [f"{key}={value}" for key, value in filter_._query_parameters()]


def typed_values(filter_: Filter[Any], key: str) -> list[str]:
    return [value for name, value in filter_._query_parameters() if name == key]


class TestRendering:
    def test_a_top_level_and_flattens_to_separate_query_parameters(self) -> None:
        assert rendered(Todos.a.eq(1) & Todos.b.gt(2)) == ["a=eq.1", "b=gt.2"]

    def test_an_or_renders_as_a_single_parenthesised_parameter(self) -> None:
        assert rendered(Todos.a.eq(1) | Todos.b.gt(2)) == ["or=(a.eq.1,b.gt.2)"]

    def test_an_and_nested_inside_an_or_renders_as_a_group(self) -> None:
        filter_ = (Todos.a.eq(1) & Todos.b.gt(2)) | Todos.c.eq(3)

        assert rendered(filter_) == ["or=(and(a.eq.1,b.gt.2),c.eq.3)"]

    def test_a_repeated_or_flattens(self) -> None:
        filter_ = Todos.a.eq(1) | Todos.b.eq(2) | Todos.c.eq(3)

        assert rendered(filter_) == ["or=(a.eq.1,b.eq.2,c.eq.3)"]

    def test_a_repeated_and_flattens(self) -> None:
        filter_ = Todos.a.eq(1) & Todos.b.eq(2) & Todos.c.eq(3)

        assert rendered(filter_) == ["a=eq.1", "b=eq.2", "c=eq.3"]

    def test_negation_prefixes_the_group_operator(self) -> None:
        assert rendered(~(Todos.a.eq(1) & Todos.b.gt(2))) == ["not.and=(a.eq.1,b.gt.2)"]
        assert rendered(~(Todos.a.eq(1) | Todos.b.gt(2))) == ["not.or=(a.eq.1,b.gt.2)"]

    def test_negating_a_single_comparison_prefixes_the_operator(self) -> None:
        assert rendered(~Todos.a.eq(1)) == ["a=not.eq.1"]

    def test_filters_reduce_into_one_flat_group(self) -> None:
        filter_ = reduce(or_, (Todos.id.eq(id) for id in [1, 2, 3]))

        assert rendered(filter_) == ["or=(id.eq.1,id.eq.2,id.eq.3)"]

    def test_raw_passes_an_operand_through_untouched(self) -> None:
        assert rendered(Filter.raw("cost::text", "eq.10")) == ["cost::text=eq.10"]
        assert rendered(~Filter[TodoRow].raw("x", "eq.1")) == ["x=not.eq.1"]
        assert rendered(Todos.id.eq(1) | Filter.raw("x", "eq.2")) == [
            "or=(id.eq.1,x.eq.2)"
        ]

    def test_group_operands_are_escaped_and_top_level_ones_are_not(self) -> None:
        assert rendered(Todos.name.eq("a,b")) == ["name=eq.a,b"]
        assert rendered(Todos.name.eq("a,b") | Todos.id.eq(3)) == [
            'or=(name.eq."a,b",id.eq.3)'
        ]
        assert rendered(Todos.name.eq("p(q)") | Todos.id.eq(3)) == [
            'or=(name.eq."p(q)",id.eq.3)'
        ]

    def test_quoted_group_operands_escape_backslashes_and_quotes(self) -> None:
        assert rendered(Todos.name.eq('a"b\\c,') | Todos.id.eq(3)) == [
            'or=(name.eq."a\\"b\\\\c,",id.eq.3)'
        ]

    def test_double_negation_collapses_in_both_positions(self) -> None:
        assert rendered(~~Todos.id.eq(2)) == ["id=eq.2"]
        assert rendered(~~Todos.id.eq(2) | Todos.id.eq(3)) == ["or=(id.eq.2,id.eq.3)"]
        assert rendered(~~~(Todos.a.eq(1) & Todos.b.eq(2))) == [
            "not.and=(a.eq.1,b.eq.2)"
        ]

    def test_negating_twice_gives_the_filter_back(self) -> None:
        assert ~~Todos.id.eq(2) == Todos.id.eq(2)
        assert ~~~Todos.id.eq(2) == ~Todos.id.eq(2)

    def test_composing_with_anything_but_a_filter_is_a_type_error(self) -> None:
        with pytest.raises(TypeError):
            Todos.a.eq(1) & "b=eq.2"  # pyrefly: ignore[unsupported-operation]
        with pytest.raises(TypeError):
            Todos.a.eq(1) | 5  # pyrefly: ignore[unsupported-operation]

    def test_a_negated_leaf_inside_a_group_moves_not_next_to_the_operator(
        self,
    ) -> None:
        assert rendered(~Todos.a.eq(1) | Todos.b.eq(2)) == ["or=(a.not.eq.1,b.eq.2)"]
        assert rendered(~Todos.name.eq("p(q)") | Todos.id.eq(3)) == [
            'or=(name.not.eq."p(q)",id.eq.3)'
        ]
        assert rendered(~Todos.name.eq("a,b") | Todos.id.eq(3)) == [
            'or=(name.not.eq."a,b",id.eq.3)'
        ]

    def test_a_negated_leaf_inside_a_nested_and_renders_in_place(self) -> None:
        filter_ = (Todos.a.eq(1) & ~Todos.b.eq(2)) | Todos.c.eq(3)

        assert rendered(filter_) == ["or=(and(a.eq.1,b.not.eq.2),c.eq.3)"]

    def test_a_raw_leaf_under_an_and_nested_in_an_or_reaches_the_group_grammar(
        self,
    ) -> None:
        filter_ = (Todos.id.eq(1) & Filter.raw("cost::text", "eq.10")) | Todos.id.eq(3)

        assert rendered(filter_) == ["or=(and(id.eq.1,cost::text.eq.10),id.eq.3)"]

    def test_a_raw_leaf_under_an_and_nested_in_a_not_reaches_the_group_grammar(
        self,
    ) -> None:
        filter_ = ~(Todos.id.eq(1) & Filter.raw("cost::text", "eq.10"))

        assert rendered(filter_) == ["not.and=(id.eq.1,cost::text.eq.10)"]

    def test_a_negated_raw_leaf_inside_a_group_moves_not_next_to_the_operand(
        self,
    ) -> None:
        filter_ = Todos.id.eq(1) | ~Filter[TodoRow].raw("x", "eq.2")

        assert rendered(filter_) == ["or=(id.eq.1,x.not.eq.2)"]

    def test_negating_a_nested_group_still_prefixes_the_group_operator(self) -> None:
        filter_ = ~(Todos.a.eq(1) & Todos.b.eq(2)) | Todos.c.eq(3)

        assert rendered(filter_) == ["or=(not.and(a.eq.1,b.eq.2),c.eq.3)"]

    def test_group_escaping_applies_two_levels_deep(self) -> None:
        filter_ = (Todos.a.eq(1) & Todos.name.eq("p(q)")) | Todos.id.eq(3)

        assert rendered(filter_) == ['or=(and(a.eq.1,name.eq."p(q)"),id.eq.3)']

    def test_a_column_name_with_reserved_characters_is_quoted(self) -> None:
        assert rendered(Column("col,name").eq(1)) == ['"col,name"=eq.1']
        assert rendered(Column("col:name").eq(1) | Todos.id.eq(3)) == [
            'or=("col:name".eq.1,id.eq.3)'
        ]

    def test_a_filter_is_a_value(self) -> None:
        assert Todos.a.eq(1) == Todos.a.eq(1)
        assert Todos.a.eq(1) != Todos.a.eq(2)
        assert Todos.a.eq(1) != ~Todos.a.eq(1)
        assert hash(Todos.a.eq(1) & Todos.b.eq(2)) == hash(
            Todos.a.eq(1) & Todos.b.eq(2)
        )

    def test_composing_leaves_the_operands_unchanged(self) -> None:
        left = Todos.a.eq(1)
        right = Todos.b.eq(2)
        both = left & right
        either = left | right

        assert rendered(left) == ["a=eq.1"]
        assert rendered(right) == ["b=eq.2"]
        assert rendered(both) == ["a=eq.1", "b=eq.2"]
        assert rendered(either) == ["or=(a.eq.1,b.eq.2)"]


class TestComparisonOperators:
    def test_render_their_wire_operator(self) -> None:
        assert rendered(Todos.id.eq(1)) == ["id=eq.1"]
        assert rendered(Todos.id.neq(1)) == ["id=neq.1"]
        assert rendered(Todos.id.gt(1)) == ["id=gt.1"]
        assert rendered(Todos.id.gte(1)) == ["id=gte.1"]
        assert rendered(Todos.id.lt(1)) == ["id=lt.1"]
        assert rendered(Todos.id.lte(1)) == ["id=lte.1"]
        assert rendered(Todos.id.is_distinct(1)) == ["id=isdistinct.1"]

    def test_boolean_is_checks(self) -> None:
        assert rendered(Todos.is_done.is_true()) == ["is_done=is.true"]
        assert rendered(Todos.is_done.is_false()) == ["is_done=is.false"]
        assert rendered(Todos.is_urgent.is_true()) == ["is_urgent=is.true"]
        assert rendered(Todos.is_urgent.is_null()) == ["is_urgent=is.null"]

    def test_is_null_on_a_nullable_column_and_a_computed_field(self) -> None:
        assert rendered(Todos.due.is_null()) == ["due=is.null"]
        assert rendered(~Todos.due.is_null()) == ["due=not.is.null"]
        assert rendered(Todos.full_name.is_null()) == ["full_name=is.null"]
        assert rendered(Todos.full_name.is_null() | Todos.id.eq(1)) == [
            "or=(full_name.is.null,id.eq.1)"
        ]

    def test_a_column_has_no_is_null(self) -> None:
        assert not hasattr(Todos.id, "is_null")

    def test_raw_keeps_the_column_and_passes_the_operand_through(self) -> None:
        assert rendered(Todos.name.raw("someop.value")) == ["name=someop.value"]
        assert rendered(~Todos.name.raw("someop.v")) == ["name=not.someop.v"]
        assert rendered(Column("col,name").raw("eq.1")) == ['"col,name"=eq.1']

    def test_the_operator_enum_carries_the_tokens_of_the_string_builder(
        self,
    ) -> None:
        assert FilterOperator.EQ == Filters.EQ
        assert FilterOperator.NEQ == Filters.NEQ
        assert FilterOperator.GT == Filters.GT
        assert FilterOperator.GTE == Filters.GTE
        assert FilterOperator.LT == Filters.LT
        assert FilterOperator.LTE == Filters.LTE
        assert FilterOperator.IS == Filters.IS
        assert FilterOperator.IN == Filters.IN
        assert FilterOperator.TEXT_SEARCH == Filters.FTS
        assert FilterOperator.IS_DISTINCT == "isdistinct"


class TestIn:
    def test_renders_a_parenthesised_list(self) -> None:
        assert rendered(Todos.id.in_([1, 2])) == ["id=in.(1,2)"]
        assert rendered(Todos.name.in_(["a", "b"])) == ["name=in.(a,b)"]

    def test_accepts_any_iterable(self) -> None:
        assert rendered(Todos.id.in_((1, 2))) == ["id=in.(1,2)"]
        assert rendered(Todos.id.in_(id for id in range(3))) == ["id=in.(0,1,2)"]

    def test_rejects_one_string_in_place_of_the_values(self) -> None:
        with pytest.raises(TypeError, match="iterable of values"):
            Todos.name.in_("abc")  # pyrefly: ignore[string-as-iterable]

    def test_quotes_members_only_when_the_list_grammar_needs_it(self) -> None:
        assert rendered(Todos.name.in_(["p(q)", "a,b", "a{b", "x"])) == [
            'name=in.("p(q)","a,b",a{b,x)'
        ]

    def test_escapes_quotes_and_backslashes_in_members(self) -> None:
        assert rendered(Todos.name.in_(['a"b\\c'])) == ['name=in.("a\\"b\\\\c")']

    def test_negates_as_not_in(self) -> None:
        assert rendered(~Todos.id.in_([1, 2])) == ["id=not.in.(1,2)"]

    def test_keeps_its_own_parentheses_literal_inside_a_group(self) -> None:
        assert rendered(Todos.id.in_([2, 3]) | Todos.id.eq(1)) == [
            "or=(id.in.(2,3),id.eq.1)"
        ]
        assert rendered(~Todos.name.in_(["a,b"]) | Todos.id.eq(1)) == [
            'or=(name.not.in.("a,b"),id.eq.1)'
        ]

    def test_an_empty_list_renders_an_empty_pair_of_parentheses(self) -> None:
        assert rendered(Todos.id.in_([])) == ["id=in.()"]

    def test_members_render_like_other_operands(self) -> None:
        assert rendered(Todos.is_done.in_([True, False])) == ["is_done=in.(true,false)"]
        assert rendered(Todos.mood.in_([Mood.HAPPY, Mood.VERY_HAPPY])) == [
            "mood=in.(happy,very happy)"
        ]


class TestTextSearch:
    def test_renders_the_query_type_as_a_prefix(self) -> None:
        assert rendered(Todos.name.text_search("fat cat")) == ["name=fts.fat cat"]
        assert rendered(
            Todos.name.text_search("fat cat", type=TextSearchType.PLAIN)
        ) == ["name=plfts.fat cat"]
        assert rendered(
            Todos.name.text_search("fat cat", type=TextSearchType.PHRASE)
        ) == ["name=phfts.fat cat"]
        assert rendered(
            Todos.name.text_search("fat cat", type=TextSearchType.WEB_SEARCH)
        ) == ["name=wfts.fat cat"]

    def test_renders_the_configuration_as_a_suffix(self) -> None:
        assert rendered(Todos.name.text_search("fat cat", config="english")) == [
            "name=fts(english).fat cat"
        ]
        assert rendered(
            Todos.name.text_search(
                "fat cat", type=TextSearchType.WEB_SEARCH, config="english"
            )
        ) == ["name=wfts(english).fat cat"]

    def test_negates_and_groups_like_a_comparison(self) -> None:
        assert rendered(~Todos.name.text_search("fat cat", config="english")) == [
            "name=not.fts(english).fat cat"
        ]
        assert rendered(Todos.name.text_search("fat cat") | Todos.id.eq(1)) == [
            "or=(name.fts.fat cat,id.eq.1)"
        ]

    def test_exposes_the_text_search_operator(self) -> None:
        comparison = Todos.name.text_search("fat cat", config="english").comparison

        assert comparison is not None
        assert comparison.operator is FilterOperator.TEXT_SEARCH
        assert comparison.value == "fat cat"


class TestValueRendering:
    def test_strings_numbers_and_booleans_render_as_themselves(self) -> None:
        assert rendered(Todos.name.eq("a b")) == ["name=eq.a b"]
        assert rendered(Todos.cost.gt(1.5)) == ["cost=gt.1.5"]
        assert rendered(Todos.is_done.eq(True)) == ["is_done=eq.true"]
        assert rendered(Todos.is_done.eq(False)) == ["is_done=eq.false"]

    def test_an_enum_renders_as_its_value(self) -> None:
        assert rendered(Todos.mood.eq(Mood.VERY_HAPPY)) == ["mood=eq.very happy"]

    def test_a_dict_renders_as_json(self) -> None:
        assert rendered(Todos.data.eq({"a": 1, "b": "x"})) == [
            'data=eq.{"a":1,"b":"x"}'
        ]

    def test_a_dict_inside_a_group_is_quoted_as_a_filter_value(self) -> None:
        assert rendered(Todos.data.eq({"a": 1}) | Todos.id.eq(1)) == [
            'or=(data.eq."{\\"a\\":1}",id.eq.1)'
        ]

    def test_an_ad_hoc_column_accepts_any_operand(self) -> None:
        assert rendered(Column("deleted_at").eq(None)) == ["deleted_at=eq.null"]
        assert rendered(Column("tags").eq(["a", "b"])) == ['tags=eq.["a","b"]']


class TestComparison:
    def test_exposes_a_single_operator_call_with_its_operand_as_given(self) -> None:
        comparison = Todos.id.eq(1).comparison

        assert comparison == Comparison(
            column=Todos.id, operator=FilterOperator.EQ, value=1, negated=False
        )
        in_ = Todos.id.in_([1, 2]).comparison
        assert in_ is not None
        assert in_.value == (1, 2)
        is_null = Todos.due.is_null().comparison
        assert is_null is not None
        assert is_null.operator is FilterOperator.IS
        assert is_null.value is None

    def test_survives_a_not_around_a_single_comparison_as_negated(self) -> None:
        comparison = (~Todos.id.in_([1, 2])).comparison

        assert comparison == Comparison(
            column=Todos.id, operator=FilterOperator.IN, value=(1, 2), negated=True
        )

    def test_is_none_for_a_raw_or_composed_filter(self) -> None:
        assert Filter[TodoRow].raw("x", "eq.1").comparison is None
        assert (Todos.a.eq(1) & Todos.b.eq(2)).comparison is None
        assert (~(Todos.a.eq(1) & Todos.b.eq(2))).comparison is None

    def test_survives_a_double_negation(self) -> None:
        assert (~~Todos.a.eq(1)).comparison == Todos.a.eq(1).comparison


COMPARISON_VALUES: list[Any] = [
    None,
    True,
    False,
    {"key": "value"},
    ["a", "b"],
    "a",
    "a,b",
    "p(q)",
    'a"b\\c',
    42,
    1.5,
    Decimal("1.25"),
    datetime(2024, 1, 15, 12, tzinfo=UTC),
    UUID("12345678-1234-5678-1234-567812345678"),
    Mood.VERY_HAPPY,
]


class TestEqualsTheStringBuilder:
    @pytest.mark.parametrize("method", ["eq", "neq", "gt", "gte", "lt", "lte"])
    @pytest.mark.parametrize("value", COMPARISON_VALUES)
    def test_comparison(
        self, builder: BaseFilterRequestBuilder, method: str, value: Any
    ) -> None:
        expected = getattr(builder, method)("x", value).request.query.get_list("x")

        assert typed_values(getattr(Column("x"), method)(value), "x") == expected

    @pytest.mark.parametrize("method", ["eq", "neq", "gt", "gte", "lt", "lte"])
    @pytest.mark.parametrize("value", COMPARISON_VALUES)
    def test_negated_comparison(
        self, builder: BaseFilterRequestBuilder, method: str, value: Any
    ) -> None:
        expected = getattr(builder.not_, method)("x", value).request.query.get_list("x")
        filter_: Filter[Any] = getattr(Column("x"), method)(value)

        assert typed_values(~filter_, "x") == expected

    def test_is(self, builder: BaseFilterRequestBuilder) -> None:
        assert typed_values(NullableColumn("x").is_null(), "x") == builder.is_(
            "x", None
        ).request.query.get_list("x")
        assert typed_values(Column("x").is_true(), "x") == builder.is_(
            "x", True
        ).request.query.get_list("x")
        assert typed_values(Column("x").is_false(), "x") == builder.is_(
            "x", False
        ).request.query.get_list("x")
        assert typed_values(~NullableColumn("x").is_null(), "x") == builder.not_.is_(
            "x", None
        ).request.query.get_list("x")

    @pytest.mark.parametrize(
        "values",
        [
            [1, 2, 3],
            ["a", "b"],
            [],
            ['ACME, "Pro"', "C:\\Reports,2026"],
            ['"Pro"'],
            ["folder\\report"],
            ['folder\\"report'],
            ["normal", "a,b", "a:b", "a(b)", "table.column"],
        ],
    )
    def test_in(self, builder: BaseFilterRequestBuilder, values: list[Any]) -> None:
        expected = builder.in_("x", values).request.query.get_list("x")

        assert typed_values(Column("x").in_(values), "x") == expected
        assert typed_values(~Column("x").in_(values), "x") == builder.not_.in_(
            "x", values
        ).request.query.get_list("x")

    @pytest.mark.parametrize("column", ["col,name", "col:name", "col(name)", "a.b"])
    def test_column_name(self, builder: BaseFilterRequestBuilder, column: str) -> None:
        key = sanitize_param(column)
        expected = builder.eq(column, "val").request.query.get_list(key)

        assert typed_values(Column(column).eq("val"), key) == expected

    def test_repeated_filters_on_one_column(
        self, builder: BaseFilterRequestBuilder
    ) -> None:
        expected = builder.lte("x", "a").gte("x", "b").request.query.get_list("x")

        assert (
            typed_values(Column("x").lte("a") & Column("x").gte("b"), "x") == expected
        )

    def test_or(self, builder: BaseFilterRequestBuilder) -> None:
        expected = builder.or_("x.eq.1,y.gt.2").request.query.get_list("or")

        assert typed_values(Column("x").eq(1) | Column("y").gt(2), "or") == expected

    def test_not_or(self, builder: BaseFilterRequestBuilder) -> None:
        expected = builder.not_.or_("x.eq.1,y.gt.2").request.query.get_list("not.or")

        assert (
            typed_values(~(Column("x").eq(1) | Column("y").gt(2)), "not.or") == expected
        )

    @pytest.mark.parametrize("type_", [None, *TextSearchType])
    @pytest.mark.parametrize("config", [None, "", "english"])
    def test_text_search(
        self,
        select_builder: SelectRequestBuilder[SyncHttpIO],
        type_: TextSearchType | None,
        config: str | None,
    ) -> None:
        expected = select_builder.text_search(
            "x", "fat cat", type=type_, config=config
        ).request.query.get_list("x")

        assert (
            typed_values(
                Column("x").text_search("fat cat", type=type_, config=config), "x"
            )
            == expected
        )
