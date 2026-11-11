from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Any, Generic, assert_never

from typing_extensions import TypeVar

from .types import _TEXT_SEARCH_OPERATORS, Filters, TextSearchType
from .utils import _serialize_filter_value, sanitize_param

if TYPE_CHECKING:
    from collections.abc import Iterable

Row = TypeVar("Row", default=Any)
"""The row type of the table a column expression or a filter belongs to."""

Value = TypeVar("Value", default=Any)
"""The Python type of a column expression, which its operators take as their
operand."""


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
    TEXT_SEARCH = "fts"


class ColumnExpression(ABC, Generic[Row, Value]):
    """A single value of a row that a filter applies an operator to: a stored
    column, a computed field, or an expression derived from one.

    `Row` is the row type of the table the expression belongs to, and every
    filter built from it carries it, so a filter on one table is rejected by a
    query on another. `Value` is the Python type of the expression, which every
    operator takes as its operand, so `Books.id.eq("seven")` is a type error.
    Both default to `Any`, so `Column("deleted_at")` works without generated
    code.

    Operators are methods, not Python's comparison operators, so a column keeps
    its equality and hash. There is no `not_in()` or `is_not_null()`: negate the
    filter with `~` instead.
    """

    @property
    @abstractmethod
    def expression(self) -> str:
        """The text PostgREST expects on the left of an operator."""

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
        return self._compare(FilterOperator.IN, tuple(values))

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
        return Filter(_Raw(self.expression, operand))


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
    inner: _Node[Row]


type _Node[Row] = _Comparison[Row] | _Raw[Row] | _And[Row] | _Or[Row] | _Not[Row]


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
    `in_()`, and `None`, `True` or `False` for an `IS` check."""
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
        return Filter(_And((*_and_parts(self._node), *_and_parts(other._node))))

    def __or__(self, other: Filter[Row]) -> Filter[Row]:
        """Only rows satisfying this filter, `other`, or both."""
        return Filter(_Or((*_or_parts(self._node), *_or_parts(other._node))))

    def __invert__(self) -> Filter[Row]:
        """Only rows that do not satisfy this filter."""
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
    since its parentheses and commas are syntax."""
    if node.operator is FilterOperator.IN:
        members = ",".join(
            sanitize_param(_serialize_filter_value(member)) for member in node.value
        )
        return f"({members})"
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


def _negated_query_parameters(node: _Node[Row]) -> list[tuple[str, str]]:
    match node:
        case _Comparison():
            return [(_key(node), f"not.{node.token}.{_operand(node)}")]
        case _Raw():
            return [(node.column, f"not.{node.operand}")]
        case _And():
            return [("not.and", _group_list(node.children))]
        case _Or():
            return [("not.or", _group_list(node.children))]
        case _Not():
            return _query_parameters(node.inner)
        case _:
            assert_never(node)


def _group_list(children: tuple[_Node[Row], ...]) -> str:
    return f"({','.join(_group(child) for child in children)})"


def _group(node: _Node[Row]) -> str:
    """A node in the comma-separated form used inside `or=(…)`: an `&` is
    spelled `and(…)`, operands are escaped, a negated leaf puts `not.` after
    the column (`id.not.eq.2`) while a negated group keeps it in front
    (`not.and(…)`), and a double negation collapses."""
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


def _negated_group(node: _Node[Row]) -> str:
    match node:
        case _Comparison():
            return f"{_key(node)}.not.{node.token}.{_group_operand(node)}"
        case _Raw():
            return f"{node.column}.not.{node.operand}"
        case _And() | _Or():
            return f"not.{_group(node)}"
        case _Not():
            return _group(node.inner)
        case _:
            assert_never(node)
