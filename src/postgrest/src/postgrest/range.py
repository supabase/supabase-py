from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Generic, Literal

from typing_extensions import TypeVar

from .utils import _serialize_filter_value

Bound = TypeVar("Bound", default=Any)
"""The Python type of the bounds of a `Range`."""

type RangeBounds = Literal["[)", "(]", "()", "[]"]
"""Which bounds of a `Range` are included: `[` and `]` include theirs, `(`
and `)` exclude theirs."""

_RANGE_BOUNDS = ("[)", "(]", "()", "[]")

_RESERVED_CHARACTERS = '(),[]"\\'
"""Characters a bound is quoted for, since Postgres reads them as range
syntax."""


@dataclass(frozen=True)
class Range(Generic[Bound]):
    """A PostgreSQL range value: the value of a range column, such as
    `int4range` or `tstzrange`, and the operand of its operators.

    `Range(2, 25)` is `[2,25)`, the lower bound included and the upper
    excluded, which is the form Postgres gives every discrete range. `bounds`
    chooses the other forms, as in psycopg: `Range(2, 25, "[]")` is `[2,25]`.
    A `None` bound is unbounded, so `Range(None, 25)` is `(,25)`.

    `Bound` is the Python type of the bounds: `int` for `int4range` and
    `int8range`, `float` for `numrange`, `date` for `daterange` and `datetime`
    for `tsrange` and `tstzrange`. A column typed `Range[date]` takes a
    `Range[date]` and nothing else as the operand of a range operator.

    `str(Range(2, 25))` is the literal Postgres reads, `[2,25)`.
    """

    lower: Bound | None = None
    """The lower bound, or `None` for no lower bound."""
    upper: Bound | None = None
    """The upper bound, or `None` for no upper bound."""
    bounds: RangeBounds = "[)"
    """Which bounds are included, `[)` unless given."""

    def __post_init__(self) -> None:
        if self.bounds not in _RANGE_BOUNDS:
            raise ValueError(
                f"bounds must be one of {', '.join(_RANGE_BOUNDS)}, not {self.bounds!r}"
            )

    def __str__(self) -> str:
        """The range as Postgres writes it, such as `[2,25)` or `(,25]`."""
        lower, upper = self.bounds
        return f"{lower}{_bound(self.lower)},{_bound(self.upper)}{upper}"


def _bound(value: object) -> str:
    """A bound rendered as a filter value, quoted when it holds a character
    Postgres reads as range syntax or is empty, which would otherwise mean
    unbounded."""
    if value is None:
        return ""
    text = _serialize_filter_value(value)
    if text and not any(character in text for character in _RESERVED_CHARACTERS):
        return text
    escaped = text.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{escaped}"'
