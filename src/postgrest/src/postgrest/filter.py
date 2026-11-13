from __future__ import annotations

from abc import ABC, abstractmethod
from collections.abc import Iterable, Mapping
from dataclasses import dataclass, replace
from enum import StrEnum
from typing import TYPE_CHECKING, Any, Generic, Literal, assert_never, overload

from typing_extensions import TypeVar

from .range import Bound, Range
from .types import _TEXT_SEARCH_OPERATORS, Filters, TextSearchType
from .utils import _sanitize_array_param, _serialize_filter_value, sanitize_param

if TYPE_CHECKING:
    from pydantic import JsonValue

Row = TypeVar("Row", default=Any)
"""The row type of the table a column expression, a filter or an ordering
belongs to."""

Value = TypeVar("Value", default=Any)
"""The Python type of a column expression, which its operators take as their
operand."""

Element = TypeVar("Element")
"""The element type of an array column."""


class FilterOperator(StrEnum):
    """A PostgREST filter operator, whose value is the token it is sent as.

    `TEXT_SEARCH` is sent prefixed by the query type and suffixed by the text
    search configuration when either is given, as in `wfts(english)`.
    """

    EQ = "eq"
    NEQ = "neq"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    IS_DISTINCT = "isdistinct"
    IS = "is"
    IN = "in"
    LIKE = "like"
    ILIKE = "ilike"
    MATCH_REGEX = "match"
    IMATCH_REGEX = "imatch"
    LIKE_ALL_OF = "like(all)"
    LIKE_ANY_OF = "like(any)"
    ILIKE_ALL_OF = "ilike(all)"
    ILIKE_ANY_OF = "ilike(any)"
    CONTAINS = "cs"
    CONTAINED_BY = "cd"
    OVERLAPS = "ov"
    RANGE_LT = "sl"
    RANGE_GT = "sr"
    RANGE_GTE = "nxl"
    RANGE_LTE = "nxr"
    RANGE_ADJACENT = "adj"
    TEXT_SEARCH = "fts"


_ARRAY_OPERATORS = frozenset(
    {
        FilterOperator.LIKE_ALL_OF,
        FilterOperator.LIKE_ANY_OF,
        FilterOperator.ILIKE_ALL_OF,
        FilterOperator.ILIKE_ANY_OF,
        FilterOperator.CONTAINS,
        FilterOperator.CONTAINED_BY,
        FilterOperator.OVERLAPS,
    }
)
"""The operators whose operand is sent as an array literal when it is a
collection of values."""


class Ordering(ABC, Generic[Row]):
    """One sort key of a query: a column expression, optionally with a
    direction and a null placement.

        .order(Books.priority.desc())
        .order(Books.id)  # breaks ties in the first

    A bare column is an ordering with no direction, and `order(Books.id)`
    sends `order=id`; `asc()`, `desc()`, `nulls_first()` and `nulls_last()`
    say more, as in `title.desc.nullslast`. Only what was asked for is sent,
    so the defaults of PostgREST and the database apply to the rest, where the
    string builder's `order()` always sends a direction.

    `Row` is the row type of the table the key belongs to, so an ordering on
    one table cannot be applied to a query on another.
    """

    @property
    @abstractmethod
    def order_key(self) -> str:
        """The key as it appears in the `order` parameter, such as
        `title.desc.nullslast`."""

    @abstractmethod
    def asc(self) -> Ordering[Row]:
        """Sorts smallest first."""

    @abstractmethod
    def desc(self) -> Ordering[Row]:
        """Sorts largest first."""

    @abstractmethod
    def nulls_first(self) -> Ordering[Row]:
        """Places `NULL`s before the other values."""

    @abstractmethod
    def nulls_last(self) -> Ordering[Row]:
        """Places `NULL`s after the other values."""


@dataclass(frozen=True)
class _Ordering(Ordering[Row]):
    """An ordering by an expression with the direction and the null placement
    that were asked for."""

    expression: str
    direction: Literal["asc", "desc"] | None = None
    """`None` sends no direction, so the default of PostgREST applies."""
    nulls: Literal["nullsfirst", "nullslast"] | None = None
    """`None` sends no placement, so the default of the database applies."""

    @property
    def order_key(self) -> str:
        parts = (self.expression, self.direction, self.nulls)
        return ".".join(part for part in parts if part is not None)

    def asc(self) -> Ordering[Row]:
        return replace(self, direction="asc")

    def desc(self) -> Ordering[Row]:
        return replace(self, direction="desc")

    def nulls_first(self) -> Ordering[Row]:
        return replace(self, nulls="nullsfirst")

    def nulls_last(self) -> Ordering[Row]:
        return replace(self, nulls="nullslast")


class ColumnExpression(Ordering[Row], ABC, Generic[Row, Value]):
    """A single value of a row that a filter applies an operator to, or that a
    query orders by: a stored column, a computed field, or an expression
    derived from one.

    `Row` is the row type of the table the expression belongs to, and every
    filter and ordering built from it carries it, so a filter on one table is
    rejected by a query on another. `Value` is the Python type of the
    expression, which every operator takes as its operand, so
    `Books.id.eq("seven")` is a type error. Both default to `Any`, so
    `Column("deleted_at")` works without generated code.

    The operators of one kind of value exist on that kind only: `like()` on a
    `str` expression, `contains()` on a `list`, a `Range` or a `JsonValue`
    one, `range_lt()` on a `Range` one. Operators are methods, not Python's
    comparison operators, so a column keeps its equality and hash. There is
    no `not_in()` or `is_not_null()`: negate the filter with `~` instead.
    """

    @property
    @abstractmethod
    def expression(self) -> str:
        """The text PostgREST expects on the left of an operator."""

    @property
    def order_key(self) -> str:
        """The expression as it appears in the `order` parameter: on its own,
        it orders with no direction, so `order(Books.title)` sends
        `order=title`."""
        return self.expression

    def asc(self) -> Ordering[Row]:
        """Sorts by this expression, smallest first: `title.asc`."""
        return _Ordering(self.order_key, direction="asc")

    def desc(self) -> Ordering[Row]:
        """Sorts by this expression, largest first: `title.desc`."""
        return _Ordering(self.order_key, direction="desc")

    def nulls_first(self) -> Ordering[Row]:
        """Sorts by this expression with `NULL`s before the other values,
        leaving the direction to PostgREST: `title.nullsfirst`."""
        return _Ordering(self.order_key, nulls="nullsfirst")

    def nulls_last(self) -> Ordering[Row]:
        """Sorts by this expression with `NULL`s after the other values,
        leaving the direction to PostgREST: `title.nullslast`."""
        return _Ordering(self.order_key, nulls="nullslast")

    def _compare(
        self, operator: FilterOperator, value: object, *, token: str | None = None
    ) -> Filter[Row]:
        return Filter(_Comparison(self, operator, value, token or operator.value))

    def eq(self, value: Value) -> Filter[Row]:
        """Only rows where this expression equals `value`.

        Use `is_null()` to match SQL `NULL`, which no `eq()` does.
        """
        return self._compare(FilterOperator.EQ, value)

    def neq(self, value: Value) -> Filter[Row]:
        """Only rows where this expression does not equal `value`."""
        return self._compare(FilterOperator.NEQ, value)

    def gt(self, value: Value) -> Filter[Row]:
        """Only rows where this expression is greater than `value`."""
        return self._compare(FilterOperator.GT, value)

    def gte(self, value: Value) -> Filter[Row]:
        """Only rows where this expression is greater than or equal to
        `value`."""
        return self._compare(FilterOperator.GTE, value)

    def lt(self, value: Value) -> Filter[Row]:
        """Only rows where this expression is less than `value`."""
        return self._compare(FilterOperator.LT, value)

    def lte(self, value: Value) -> Filter[Row]:
        """Only rows where this expression is less than or equal to `value`."""
        return self._compare(FilterOperator.LTE, value)

    def is_distinct(self, value: Value) -> Filter[Row]:
        """Only rows where this expression is distinct from `value`.

        Unlike `neq()`, a `NULL` row matches any operand.
        """
        return self._compare(FilterOperator.IS_DISTINCT, value)

    def in_(self, values: Iterable[Value]) -> Filter[Row]:
        """Only rows where this expression equals one of `values`.

        An empty `values` matches no rows. `~Books.id.in_([1, 2])` renders
        `id=not.in.(1,2)`.
        """
        return self._compare(FilterOperator.IN, _members(values, "in_"))

    def like(self: ColumnExpression[Row, str], pattern: str) -> Filter[Row]:
        """Only rows matching the `LIKE` `pattern`, case-sensitively.

        `%` matches any run of characters and `_` exactly one.
        """
        return self._compare(FilterOperator.LIKE, pattern)

    def ilike(self: ColumnExpression[Row, str], pattern: str) -> Filter[Row]:
        """Only rows matching the `LIKE` `pattern`, case-insensitively."""
        return self._compare(FilterOperator.ILIKE, pattern)

    def match_regex(self: ColumnExpression[Row, str], pattern: str) -> Filter[Row]:
        """Only rows matching the POSIX regular expression `pattern`,
        case-sensitively.

        Not named `match()`, which on the string builder is an equality
        shorthand over several columns.
        """
        return self._compare(FilterOperator.MATCH_REGEX, pattern)

    def imatch_regex(self: ColumnExpression[Row, str], pattern: str) -> Filter[Row]:
        """Only rows matching the POSIX regular expression `pattern`,
        case-insensitively."""
        return self._compare(FilterOperator.IMATCH_REGEX, pattern)

    def like_all_of(
        self: ColumnExpression[Row, str], patterns: Iterable[str]
    ) -> Filter[Row]:
        """Only rows matching every one of `patterns`, case-sensitively.

        An empty `patterns` matches every row, `NULL` rows included, since
        `LIKE ALL` of nothing holds.
        """
        return self._compare(
            FilterOperator.LIKE_ALL_OF, _members(patterns, "like_all_of")
        )

    def like_any_of(
        self: ColumnExpression[Row, str], patterns: Iterable[str]
    ) -> Filter[Row]:
        """Only rows matching at least one of `patterns`, case-sensitively.

        An empty `patterns` matches no rows.
        """
        return self._compare(
            FilterOperator.LIKE_ANY_OF, _members(patterns, "like_any_of")
        )

    def ilike_all_of(
        self: ColumnExpression[Row, str], patterns: Iterable[str]
    ) -> Filter[Row]:
        """Only rows matching every one of `patterns`, case-insensitively.

        An empty `patterns` matches every row, as with `like_all_of()`.
        """
        return self._compare(
            FilterOperator.ILIKE_ALL_OF, _members(patterns, "ilike_all_of")
        )

    def ilike_any_of(
        self: ColumnExpression[Row, str], patterns: Iterable[str]
    ) -> Filter[Row]:
        """Only rows matching at least one of `patterns`, case-insensitively.

        An empty `patterns` matches no rows.
        """
        return self._compare(
            FilterOperator.ILIKE_ANY_OF, _members(patterns, "ilike_any_of")
        )

    @overload
    def contains(
        self: ColumnExpression[Row, list[Element]], values: Iterable[Element | None], /
    ) -> Filter[Row]: ...
    @overload
    def contains(
        self: ColumnExpression[Row, Range[Bound]], range: Range[Bound] | Bound, /
    ) -> Filter[Row]: ...
    @overload
    def contains(
        self: ColumnExpression[Row, JsonValue], value: Mapping[str, Any], /
    ) -> Filter[Row]: ...
    def contains(self, value: object, /) -> Filter[Row]:
        """Only rows whose value contains the operand, which the column type
        decides the shape of.

        An array column contains every element of `values`, sent as the array
        literal `{a,b}`; an empty `values` matches every row whose column is
        not `NULL`. A range column contains every value of `range`, sent as
        `[2,25)`, or the one value given, sent as `2`. A JSON column contains
        the object `value`, sent as `{"a":1}`; a JSON array or scalar operand
        has no typed form, use `raw("cs.[1,2]")`.
        """
        return self._compare(
            FilterOperator.CONTAINS, _containment_operand(value, "contains")
        )

    @overload
    def contained_by(
        self: ColumnExpression[Row, list[Element]], values: Iterable[Element | None], /
    ) -> Filter[Row]: ...
    @overload
    def contained_by(
        self: ColumnExpression[Row, Range[Bound]], range: Range[Bound], /
    ) -> Filter[Row]: ...
    @overload
    def contained_by(
        self: ColumnExpression[Row, JsonValue], value: Mapping[str, Any], /
    ) -> Filter[Row]: ...
    def contained_by(self, value: object, /) -> Filter[Row]:
        """Only rows whose value is contained by the operand, which the column
        type decides the shape of, as for `contains()`.

        An array column has no element outside `values`, a range column lies
        within `range`, and a JSON column is contained by the object `value`.
        """
        return self._compare(
            FilterOperator.CONTAINED_BY, _containment_operand(value, "contained_by")
        )

    @overload
    def overlaps(
        self: ColumnExpression[Row, list[Element]], values: Iterable[Element | None], /
    ) -> Filter[Row]: ...
    @overload
    def overlaps(
        self: ColumnExpression[Row, Range[Bound]], range: Range[Bound], /
    ) -> Filter[Row]: ...
    def overlaps(self, value: object, /) -> Filter[Row]:
        """Only rows whose value shares at least one element with `values`,
        on an array column, or at least one value with `range`, on a range
        column."""
        return self._compare(
            FilterOperator.OVERLAPS, _containment_operand(value, "overlaps")
        )

    def range_lt(
        self: ColumnExpression[Row, Range[Bound]], range: Range[Bound]
    ) -> Filter[Row]:
        """Only rows whose range is strictly to the left of `range`."""
        return self._compare(FilterOperator.RANGE_LT, range)

    def range_gt(
        self: ColumnExpression[Row, Range[Bound]], range: Range[Bound]
    ) -> Filter[Row]:
        """Only rows whose range is strictly to the right of `range`."""
        return self._compare(FilterOperator.RANGE_GT, range)

    def range_gte(
        self: ColumnExpression[Row, Range[Bound]], range: Range[Bound]
    ) -> Filter[Row]:
        """Only rows whose range does not extend to the left of `range`."""
        return self._compare(FilterOperator.RANGE_GTE, range)

    def range_lte(
        self: ColumnExpression[Row, Range[Bound]], range: Range[Bound]
    ) -> Filter[Row]:
        """Only rows whose range does not extend to the right of `range`."""
        return self._compare(FilterOperator.RANGE_LTE, range)

    def range_adjacent(
        self: ColumnExpression[Row, Range[Bound]], range: Range[Bound]
    ) -> Filter[Row]:
        """Only rows whose range is adjacent to `range`: the two share no
        value and nothing lies between them."""
        return self._compare(FilterOperator.RANGE_ADJACENT, range)

    def text_search(
        self,
        query: str,
        *,
        type: TextSearchType | None = None,
        config: str | None = None,
    ) -> Filter[Row]:
        """Only rows whose `text` or `tsvector` value matches the full text
        search `query`.

        Args:
            query: The text search query
            type: How PostgreSQL parses `query`. Without it, `query` is
                parsed by `to_tsquery`
            config: The text search configuration to use, such as `english`
        """
        token: str = Filters.FTS
        if type is not None:
            token = _TEXT_SEARCH_OPERATORS[TextSearchType(type)]
        if config:
            token = f"{token}({config})"
        return self._compare(FilterOperator.TEXT_SEARCH, query, token=token)

    def is_true(self: ColumnExpression[Row, bool]) -> Filter[Row]:
        """Only rows where this boolean expression `IS TRUE`.

        On a nullable column this differs from `eq(True)`: `eq.true` is unknown
        for a `NULL` row, `is.true` is false.
        """
        return self._compare(FilterOperator.IS, True)

    def is_false(self: ColumnExpression[Row, bool]) -> Filter[Row]:
        """Only rows where this boolean expression `IS FALSE`."""
        return self._compare(FilterOperator.IS, False)

    def raw(self, operand: str) -> Filter[Row]:
        """Apply an operator this package has no method for, keeping the
        column type-checked.

        `Books.tags.raw("someop.value")` renders `tags=someop.value`. The
        operand is sent as written, so keep the filter out of any subtree
        beneath `|` or `~` unless it is valid inside `or=(…)`.
        """
        return Filter(_Raw(sanitize_param(self.expression), operand))


def _members(values: Iterable[Any], method: str) -> tuple[Any, ...]:
    """`values` as a tuple, rejecting one string where a collection of values
    is expected, since a string is an iterable of its characters."""
    if isinstance(values, (str, bytes)):
        raise TypeError(f"{method}() takes an iterable of values, not one string")
    return tuple(values)


def _containment_operand(value: object, method: str) -> object:
    """The operand of `contains()`, `contained_by()` and `overlaps()`: a
    collection of values becomes a tuple, to be sent as an array literal, a
    mapping a `dict`, to be sent as JSON, and a `Range` or a single value is
    kept as given."""
    if isinstance(value, Mapping):
        return dict(value)
    if isinstance(value, Range) or not isinstance(value, Iterable):
        return value
    return _members(value, method)


@dataclass(frozen=True)
class _Comparison(Generic[Row]):
    """One operator applied to one column expression."""

    column: ColumnExpression[Row, Any]
    operator: FilterOperator
    value: Any
    """The operand as given, rendered when the request is built."""
    token: str
    """The operator as sent, which for a text search carries the query type
    and the configuration."""


@dataclass(frozen=True)
class _Raw(Generic[Row]):
    """Everything after the `=` as one string, sent as written in every
    position."""

    column: str
    operand: str


@dataclass(frozen=True)
class _And(Generic[Row]):
    children: tuple[_Node[Row], ...]


@dataclass(frozen=True)
class _Or(Generic[Row]):
    children: tuple[_Node[Row], ...]


@dataclass(frozen=True)
class _Not(Generic[Row]):
    inner: _Negatable[Row]


type _Negatable[Row] = _Comparison[Row] | _Raw[Row] | _And[Row] | _Or[Row]
"""A node `~` wraps. A `_Not` is never one, since `~~x` is `x`."""

type _Node[Row] = _Negatable[Row] | _Not[Row]


@dataclass(frozen=True, kw_only=True)
class Comparison(Generic[Row]):
    """One operator applied to one column expression, negated or not: the
    shape a consumer that cannot apply a whole tree, such as a realtime
    subscription, reads through `Filter.comparison`."""

    column: ColumnExpression[Row, Any]
    """The expression on the left of the operator."""
    operator: FilterOperator
    value: object
    """The operand as it was given: the value of a comparison, a tuple for
    `in_()` and for the array operators, a `Range` for the range operators,
    and `None`, `True` or `False` for an `IS` check."""
    negated: bool
    """Whether the comparison is wrapped in `~`, so it matches the rows the
    operator does not."""


@dataclass(frozen=True)
class Filter(Generic[Row]):
    """A filter on the rows of a table, built from the operator methods of a
    `ColumnExpression` and composed with `&`, `|` and `~`:

        (Books.is_done.eq(False) & Books.priority.gt(3)) | Books.id.eq(7)

    It is rendered when the request is built, by position: a top-level `&`
    becomes separate query parameters, `|` one `or=(…)`, an `&` nested inside
    a `|` an `and(…)`, a negated leaf inside a group `id.not.eq.2`, and a
    double negation collapses.

    `Row` is the row type of the table the filter belongs to, so a filter on
    one table cannot be combined with, or applied to a query on, another.
    """

    _node: _Node[Row]

    @classmethod
    def raw(cls, column: str, operand: str) -> Filter[Row]:
        """A filter written entirely in PostgREST syntax, for an expression no
        column can name.

        `Filter.raw("cost::text", "eq.10")` renders `cost::text=eq.10`:
        `column` is the query parameter name and `operand` everything after
        the `=`. Nothing here is checked. Prefer `ColumnExpression.raw()`,
        which keeps the column type-checked and takes only the operand.

        The filter is sent as written, so keep it out of any subtree beneath
        `|` or `~` unless it is valid inside `or=(…)`; a `::` in the column
        name, for example, parses at top level only.
        """
        return cls(_Raw(column, operand))

    def __and__(self, other: Filter[Row]) -> Filter[Row]:
        """Only rows satisfying both this filter and `other`."""
        if not isinstance(other, Filter):
            return NotImplemented
        return Filter(_And((*_and_parts(self._node), *_and_parts(other._node))))

    def __or__(self, other: Filter[Row]) -> Filter[Row]:
        """Only rows satisfying this filter, `other`, or both."""
        if not isinstance(other, Filter):
            return NotImplemented
        return Filter(_Or((*_or_parts(self._node), *_or_parts(other._node))))

    def __invert__(self) -> Filter[Row]:
        """Only rows that do not satisfy this filter. Negating twice gives the
        filter back."""
        match self._node:
            case _Not():
                return Filter(self._node.inner)
            case _:
                return Filter(_Not(self._node))

    @property
    def comparison(self) -> Comparison[Row] | None:
        """The one comparison this filter consists of, negated or not, or
        `None` for a raw or a composed filter."""
        match self._node:
            case _Comparison() as node:
                return Comparison(
                    column=node.column,
                    operator=node.operator,
                    value=node.value,
                    negated=False,
                )
            case _Not(inner=_Comparison() as node):
                return Comparison(
                    column=node.column,
                    operator=node.operator,
                    value=node.value,
                    negated=True,
                )
            case _:
                return None

    def _query_parameters(self) -> list[tuple[str, str]]:
        """The query parameters this filter contributes to a request, as
        `(key, value)` pairs."""
        return _query_parameters(self._node)


def _and_parts(node: _Node[Row]) -> tuple[_Node[Row], ...]:
    """Absorbs a child `&` so `a & b & c` renders flat rather than nested."""
    return node.children if isinstance(node, _And) else (node,)


def _or_parts(node: _Node[Row]) -> tuple[_Node[Row], ...]:
    """Absorbs a child `|` so `a | b | c` renders `or=(a,b,c)` rather than
    `or=(or(a,b),c)`."""
    return node.children if isinstance(node, _Or) else (node,)


def _key(node: _Comparison[Any]) -> str:
    return sanitize_param(node.column.expression)


def _operand(node: _Comparison[Any]) -> str:
    """The operand as sent at top level, where PostgREST reads everything
    after the operator as the value. The members of an `in` list are escaped,
    since its parentheses and commas are syntax, and a collection given to an
    array operator is sent as the array literal `{a,b}`, with its members
    escaped as that literal requires."""
    if node.operator is FilterOperator.IN:
        members = ",".join(
            sanitize_param(_serialize_filter_value(member)) for member in node.value
        )
        return f"({members})"
    if node.operator in _ARRAY_OPERATORS and isinstance(node.value, tuple):
        return _sanitize_array_param(node.value)
    return _serialize_filter_value(node.value)


def _group_operand(node: _Comparison[Any]) -> str:
    """The operand as sent inside a group, escaped. The parentheses of an `in`
    list stay literal there; its members are escaped already."""
    operand = _operand(node)
    if node.operator is FilterOperator.IN:
        return operand
    return sanitize_param(operand)


def _query_parameters(node: _Node[Row]) -> list[tuple[str, str]]:
    match node:
        case _Comparison():
            return [(_key(node), f"{node.token}.{_operand(node)}")]
        case _Raw():
            return [(node.column, node.operand)]
        case _And():
            return [
                parameter
                for child in node.children
                for parameter in _query_parameters(child)
            ]
        case _Or():
            return [("or", _group_list(node.children))]
        case _Not():
            return _negated_query_parameters(node.inner)
        case _:
            assert_never(node)


def _negated_query_parameters(node: _Negatable[Row]) -> list[tuple[str, str]]:
    match node:
        case _Comparison():
            return [(_key(node), f"not.{node.token}.{_operand(node)}")]
        case _Raw():
            return [(node.column, f"not.{node.operand}")]
        case _And():
            return [("not.and", _group_list(node.children))]
        case _Or():
            return [("not.or", _group_list(node.children))]
        case _:
            assert_never(node)


def _group_list(children: tuple[_Node[Row], ...]) -> str:
    return f"({','.join(_group(child) for child in children)})"


def _group(node: _Node[Row]) -> str:
    """A node in the comma-separated form used inside `or=(…)`: an `&` is
    spelled `and(…)`, operands are escaped, and a negated leaf puts `not.`
    after the column (`id.not.eq.2`) while a negated group keeps it in front
    (`not.and(…)`)."""
    match node:
        case _Comparison():
            return f"{_key(node)}.{node.token}.{_group_operand(node)}"
        case _Raw():
            return f"{node.column}.{node.operand}"
        case _And():
            return f"and{_group_list(node.children)}"
        case _Or():
            return f"or{_group_list(node.children)}"
        case _Not():
            return _negated_group(node.inner)
        case _:
            assert_never(node)


def _negated_group(node: _Negatable[Row]) -> str:
    match node:
        case _Comparison():
            return f"{_key(node)}.not.{node.token}.{_group_operand(node)}"
        case _Raw():
            return f"{node.column}.not.{node.operand}"
        case _And() | _Or():
            return f"not.{_group(node)}"
        case _:
            assert_never(node)
