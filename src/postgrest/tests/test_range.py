from dataclasses import FrozenInstanceError
from datetime import UTC, date, datetime
from decimal import Decimal
from enum import StrEnum

import pytest

from postgrest import Range


class Mood(StrEnum):
    VERY_HAPPY = "very happy"


def test_the_lower_bound_is_included_and_the_upper_excluded_unless_given() -> None:
    assert str(Range(2, 25)) == "[2,25)"
    assert str(Range(2, 25, "[]")) == "[2,25]"
    assert str(Range(2, 25, "()")) == "(2,25)"
    assert str(Range(2, 25, "(]")) == "(2,25]"


def test_a_none_bound_is_unbounded() -> None:
    assert str(Range(None, 25)) == "[,25)"
    assert str(Range(2, None)) == "[2,)"
    assert str(Range()) == "[,)"
    assert str(Range(2)) == "[2,)"


def test_bounds_render_as_filter_values() -> None:
    assert str(Range(date(2024, 1, 1), date(2024, 2, 1))) == "[2024-01-01,2024-02-01)"
    assert (
        str(
            Range(
                datetime(2024, 1, 1, tzinfo=UTC),
                datetime(2024, 2, 1, 12, 30, tzinfo=UTC),
            )
        )
        == "[2024-01-01T00:00:00+00:00,2024-02-01T12:30:00+00:00)"
    )
    assert str(Range(Decimal("1.5"), Decimal("2.25"))) == "[1.5,2.25)"
    assert str(Range(1.5, 2.0)) == "[1.5,2.0)"
    assert str(Range(Mood.VERY_HAPPY, None)) == "[very happy,)"


def test_a_bound_with_range_syntax_in_it_is_quoted() -> None:
    assert str(Range("a,b", "c")) == '["a,b",c)'
    assert str(Range("(a", "b]")) == '["(a","b]")'
    assert str(Range("[a", "b)")) == '["[a","b)")'
    assert str(Range('a"b', "c\\d")) == '["a\\"b","c\\\\d")'


def test_an_empty_string_bound_is_quoted_so_it_is_not_unbounded() -> None:
    assert str(Range("", "z")) == '["",z)'


def test_other_bounds_forms_are_rejected() -> None:
    with pytest.raises(
        ValueError, match=r"bounds must be one of \[\), \(\], \(\), \[\]"
    ):
        Range(1, 2, "[>")  # pyrefly: ignore[bad-argument-type]


def test_a_range_is_a_value() -> None:
    assert Range(1, 2) == Range(1, 2)
    assert Range(1, 2) == Range(1, 2, "[)")
    assert Range(1, 2) != Range(1, 2, "[]")
    assert Range(1, 2) != Range(1, 3)
    assert hash(Range(1, 2)) == hash(Range(1, 2))
    assert {Range(1, 2): "scheduled"}[Range(1, 2)] == "scheduled"


def test_a_range_is_frozen() -> None:
    with pytest.raises(FrozenInstanceError):
        Range(1, 2).lower = 3  # pyrefly: ignore[read-only]


def test_a_range_has_a_readable_repr() -> None:
    assert repr(Range(1, 2)) == "Range(lower=1, upper=2, bounds='[)')"
