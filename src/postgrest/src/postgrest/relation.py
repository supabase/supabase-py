from __future__ import annotations

from collections.abc import Callable
from dataclasses import KW_ONLY, dataclass, field, replace
from typing import TYPE_CHECKING, Any, Generic, Self, override

from typing_extensions import TypeVar

from .filter import Filter, Ordering, Selectable, _EmbedIsNull, _expression_key
from .utils import _quote

if TYPE_CHECKING:
    from collections.abc import Iterable

    from .table import Table  # noqa: TC004, the table module imports this one

Row = TypeVar("Row", default=Any)
"""The row type of the table a relation starts from."""

Target = TypeVar("Target", default=Any)
"""The row type of the table a relation points at."""

Nested = TypeVar("Nested")
"""The row type of the table a relation nested in an embed points at."""


@dataclass(frozen=True)
class Relation(Generic[Row, Target]):
    """A foreign key between the table whose rows are `Row` and the table
    whose rows are `Target`, seen from the first: a `ToOneRelation` when
    this table holds the key, a `ToManyRelation` when the other one does.

    Declared once per foreign key and side, normally by the generator, as a
    class attribute of the table's namespace class:

        class Books:
            author = ToOneRelation[BooksRow, AuthorsRow](
                "authors", AuthorsRow, constraint="books_author_id_fkey"
            )

        class Authors:
            books = ToManyRelation[AuthorsRow, BooksRow]("books", BooksRow)

    A relation is put into a `select_only()` list with `select()`, and its
    rows are read from the `PartialRow` through the relation itself:

        books = (
            client.table(Books.table)
            .select_only([Books.title, Books.author.select([Authors.name])])
            .execute()
        )
        author = books[0][Books.author]
        name = None if author is None else author[Authors.name]
    """

    name: str
    """The name of the table the relation points at, which the embedded
    rows come back under."""

    target_type: type[Target]
    """The row type of the table the relation points at, which the values
    of an embedded row are decoded through."""

    _: KW_ONLY

    constraint: str | None = None
    """The name of the foreign key constraint, sent as the hint
    `authors!books_author_id_fkey` so PostgREST can tell two keys between
    the same tables apart, or `None` when there is only one."""

    alias: str | None = None
    """The key the embedded rows come back under instead of `name`, sent as
    `editor:authors!books_editor_id_fkey`, or `None` for `name`.

    Two relations to the same table both come back under its name, so all
    but one of them need an alias to be embedded side by side:

        class Books:
            author = ToOneRelation[BooksRow, AuthorsRow](
                "authors", AuthorsRow, constraint="books_author_id_fkey"
            )
            editor = ToOneRelation[BooksRow, AuthorsRow](
                "authors",
                AuthorsRow,
                constraint="books_editor_id_fkey",
                alias="editor",
            )
    """

    target_table: Callable[[], Table[Target, Any, Any]] | None = field(
        default=None, repr=False
    )
    """A function returning the `Table` the relation points at, or `None`.

    `select_as()` maps a model nested in a projection against this table, to
    reach its computed fields and relations. It is a function, called on
    first use, since two tables that point at each other cannot both be
    declared first:

        class Books:
            author = ToOneRelation[BooksRow, AuthorsRow](
                "authors", AuthorsRow, target_table=lambda: Authors.table
            )

    Without it a nested model can only name the stored columns of
    `target_type`.
    """

    _attribute: str | None = field(default=None, init=False, compare=False, repr=False)

    def __set_name__(self, owner: type, name: str) -> None:
        object.__setattr__(self, "_attribute", name)

    @property
    def response_key(self) -> str:
        """The key the embedded rows come back under in the parent row, and
        that addresses the embed in a filter or a scope: the `alias`, or the
        name of the table without the constraint."""
        return self.alias if self.alias is not None else self.name

    @property
    def _target(self) -> str:
        """The table as named in a `select` list, with its constraint."""
        if self.constraint is None:
            return self.name
        return f"{self.name}!{self.constraint}"

    @property
    def _head(self) -> str:
        """The embed as named in a `select` list, with its alias."""
        if self.alias is None:
            return self._target
        return f"{self.alias}:{self._target}"

    def select(
        self, columns: Iterable[Selectable[Target]] | None = None
    ) -> Embed[Row, Target]:
        """The related table as an entry of a `select_only()` list: `columns`
        of it, or every column when none are given.

            Books.author.select([Authors.id, Authors.name])  # authors(id,name)
            Books.author.select()                            # authors(*)

        `columns` can hold embeds of their own, so
        `Authors.books.select([Books.title, Books.publisher.select()])`
        renders `books(title,publishers(*))`.

        Raises `ValueError` for an empty `columns`; leave it out to select
        every column.
        """
        if columns is None:
            return Embed(self, ())
        selected = _selected(columns)
        if not selected:
            raise ValueError(
                "select() needs at least one column; leave the columns out "
                "for every column"
            )
        return Embed(self, selected)

    def is_null(self) -> Filter[Row]:
        """Only the rows with no embedded row, `authors=is.null`:

            client.table(Books.table).select_only(
                [Books.title, Books.author.select()]
            ).where(Books.author.is_null() | Books.title.eq("Dune"))

        Negate it for the rows with one, which is what `requiring()` does as
        well, but unlike `requiring()` it composes with `|`. A filter of the
        embed in `embedded()` counts: a row whose embedded rows all fail it
        has no embedded row.

        The relation has to be in the `select_only()` list. It applies to a
        read only: `execute()` raises `ValueError` for it in the `where()`
        of an update, a delete or a count, since it does not narrow the rows
        those affect.
        """
        return Filter(_EmbedIsNull(self.response_key, "is.null"))


@dataclass(frozen=True)
class ToOneRelation(Relation[Row, Target]):
    """A relation to at most one row of the other table: this table holds
    the foreign key, or a unique key of the other table points at it. See
    `Relation`.

    It reads from a `PartialRow` as a `PartialRow` of `Target`, or `None`
    when the key is `NULL` or points at no row.
    """


@dataclass(frozen=True)
class ToManyRelation(Relation[Row, Target]):
    """A relation to any number of rows of the other table, which holds the
    foreign key. See `Relation`.

    It reads from a `PartialRow` as a list of `PartialRow`s of `Target`,
    empty when no row points at this one.
    """

    def count(self) -> EmbeddedCount[Row]:
        """The number of related rows, `books(count)`, read from a
        `PartialRow` as an `int`:

            authors = (
                client.table(Authors.table)
                .select_only([Authors.name, Authors.books.count()])
                .execute()
            )
            book_count = authors[0][Authors.books.count()]

        Unlike `Expression.count()` it needs no `db-aggregates-enabled`
        setting.
        """
        return EmbeddedCount(self)


@dataclass(frozen=True)
class Embed(Selectable[Row], Generic[Row, Target]):
    """A related table as an entry of a `select_only()` list, created by
    `Relation.select()`.

    The embedded rows are read from a `PartialRow` through `relation`.
    """

    relation: Relation[Row, Target]
    """The relation the rows are embedded through."""

    columns: tuple[Selectable[Target], ...]
    """The entries selected of the related table; empty for every column."""

    @property
    @override
    def response_key(self) -> str:
        return self.relation.response_key

    @property
    @override
    def _selected_as(self) -> str:
        (entry,) = _select_entries((self,), ())
        return entry


@dataclass(frozen=True)
class EmbeddedCount(Selectable[Row]):
    """The number of rows of a to-many relation as an entry of a
    `select_only()` list, created by `ToManyRelation.count()`.

    It comes back under its own key, `books(count)`, so it can sit next to
    an embed of the same relation, and is sent after every embed, so the
    scopes of the relation apply to the embedded rows and not to the count.
    """

    relation: ToManyRelation[Row, Any]
    """The relation whose rows are counted."""

    @property
    @override
    def response_key(self) -> str:
        return _expression_key(f"{self.relation.response_key}(count)")

    @property
    @override
    def _selected_as(self) -> str:
        return f"{_quote(self.response_key)}:{self.relation._target}(count)"


@dataclass(frozen=True)
class EmbeddedScope(Generic[Target]):
    """Filters, sort keys and a row window applied to the rows of one embed,
    built in the callback of `embedded()` or `requiring()`:

        authors = (
            client.table(Authors.table)
            .select_only([Authors.name, Authors.books.select([Books.title])])
            .embedded(
                Authors.books,
                lambda books: books.where(Books.title.ilike("%dune%"))
                .order(Books.published_on.desc())
                .limit(1),
            )
            .execute()
        )
        # books.title=ilike.%dune%&books.order=published_on.desc&books.limit=1

    Everything here applies to the embedded rows of each parent row and
    targets the related table, whose rows are `Target`, so a filter on
    another table is a type error. The embed has to be in the
    `select_only()` list.
    """

    relation: Relation[Any, Target]
    """The relation whose embedded rows the scope applies to."""

    _: KW_ONLY

    requires_match: bool = False
    """Whether the parent rows without a matching embedded row are dropped,
    sent as `!inner` on the embed."""

    filter: Filter[Target] | None = None
    """The filter on the embedded rows, or `None` for every one of them."""

    orderings: tuple[Ordering[Target], ...] = ()
    """The sort keys of the embedded rows, first key first."""

    row_limit: int | None = None
    """The maximum number of embedded rows per parent row."""

    row_offset: int | None = None
    """The number of embedded rows to skip per parent row."""

    scopes: tuple[EmbeddedScope[Any], ...] = ()
    """The scopes of the embeds nested in this one."""

    def where(self, filter: Filter[Target]) -> Self:
        """Only the embedded rows satisfying `filter`.

        The parent rows stay, with an empty list or `None` where no embedded
        row matches, unless the scope was opened with `requiring()`.
        `filter` can name a column the `select_only()` list leaves out.
        Repeated calls combine with `&`.
        """
        combined = filter if self.filter is None else self.filter & filter
        return replace(self, filter=combined)

    def order(self, ordering: Ordering[Target]) -> Self:
        """Sort the embedded rows by `ordering`. Repeated calls append, so
        the second key breaks ties in the first.

        Raises `ValueError` for a to-one relation, which has one row.
        """
        self._check_to_many("order")
        return replace(self, orderings=(*self.orderings, ordering))

    def limit(self, count: int) -> Self:
        """Return at most `count` embedded rows per parent row.

        Raises `ValueError` for a to-one relation, which has one row.
        """
        self._check_to_many("limit")
        return replace(self, row_limit=count)

    def range(self, start: int, end: int) -> Self:
        """Return the embedded rows from index `start` to index `end`, both
        included, per parent row.

        Raises `ValueError` when `end` is less than `start`, and for a
        to-one relation, which has one row.
        """
        self._check_to_many("range")
        if end < start:
            raise ValueError(
                f"range() needs end ({end}) to be at least start ({start})"
            )
        return replace(self, row_offset=start, row_limit=end - start + 1)

    def embedded(
        self,
        relation: Relation[Target, Nested],
        scope: Callable[[EmbeddedScope[Nested]], EmbeddedScope[Nested]],
    ) -> Self:
        """Apply `scope` to the rows of `relation`, an embed nested in this
        one, under a dotted path such as `books.reviews.limit=3`."""
        return replace(self, scopes=(*self.scopes, scope(EmbeddedScope(relation))))

    def requiring(
        self,
        relation: Relation[Target, Nested],
        scope: Callable[[EmbeddedScope[Nested]], EmbeddedScope[Nested]] | None = None,
    ) -> Self:
        """The same as `embedded()`, and drops the rows of this embed that
        have no matching row in `relation`.

        Only the rows of this embed are dropped, not the parent rows of the
        query, unless this scope was opened with `requiring()` as well.
        """
        return replace(self, scopes=(*self.scopes, _requiring(relation, scope)))

    def _check_to_many(self, method: str) -> None:
        if isinstance(self.relation, ToOneRelation):
            raise ValueError(
                f"{method}() applies to the rows of a to-many relation, and "
                f"{self.relation.response_key} has one row"
            )


def _requiring[Target](
    relation: Relation[Any, Target],
    scope: Callable[[EmbeddedScope[Target]], EmbeddedScope[Target]] | None,
) -> EmbeddedScope[Target]:
    """A scope on `relation` that drops the parent rows without a match, with
    `scope` applied when given."""
    opened = EmbeddedScope(relation, requires_match=True)
    return opened if scope is None else scope(opened)


def _selected[Row](columns: Iterable[Selectable[Row]]) -> tuple[Selectable[Row], ...]:
    """`columns` as a tuple, rejecting two embeds that come back under the
    same key, whose rows would overwrite each other."""
    selected = tuple(columns)
    seen: set[str] = set()
    for column in selected:
        if isinstance(column, Embed):
            if column.response_key in seen:
                raise ValueError(
                    f"{column.response_key} is embedded twice; select its "
                    "columns in one select(), or give one of two relations "
                    "to the same table an alias"
                )
            seen.add(column.response_key)
    return selected


def _select_entries(
    columns: Iterable[Selectable[Any]], scopes: tuple[EmbeddedScope[Any], ...]
) -> tuple[str, ...]:
    """The entries of a `select` list for `columns`, with `!inner` on the
    embeds `scopes` require a match in, and the counts of embedded rows
    last, since PostgREST applies the scope of a relation to its first embed.

    Raises `ValueError` for a scope whose embed is not in `columns`, and for
    an `is_null()` in a scope on an embed not selected inside it.
    """
    columns = tuple(columns)
    embeds = {column.relation for column in columns if isinstance(column, Embed)}
    for scope in scopes:
        if scope.relation not in embeds:
            raise ValueError(
                f"{scope.relation.response_key} is not embedded in the select "
                "list, so its rows cannot be scoped"
            )
    entries: list[str] = []
    counts: list[str] = []
    for column in columns:
        match column:
            case Embed():
                entries.append(_embed_entry(column, scopes))
            case EmbeddedCount():
                counts.append(column._selected_as)
            case _:
                entries.append(column._selected_as)
    return (*entries, *counts)


def _embed_entry(embed: Embed[Any, Any], scopes: tuple[EmbeddedScope[Any], ...]) -> str:
    own = tuple(scope for scope in scopes if scope.relation == embed.relation)
    nested = tuple(inner for scope in own for inner in scope.scopes)
    for scope in own:
        if scope.filter is not None:
            _check_embedded(scope.filter, embed.columns, embed.response_key)
    head = embed.relation._head
    if any(scope.requires_match for scope in own):
        head = f"{head}!inner"
    members = _select_entries(embed.columns, nested) or ("*",)
    return f"{head}({','.join(members)})"


def _check_embedded(
    filter: Filter[Any], columns: Iterable[Selectable[Any]], where: str
) -> None:
    """Raises `ValueError` when an `is_null()` of a relation in `filter`
    addresses an embed that `columns`, the entries selected in `where`, do
    not hold, which PostgREST rejects as an unknown column."""
    embedded = {column.response_key for column in columns if isinstance(column, Embed)}
    if missing := filter._embed_references() - embedded:
        raise ValueError(
            f"{', '.join(sorted(missing))} is not embedded in {where}, so the "
            "filter cannot test it for null"
        )


def _scope_parameters(
    scopes: tuple[EmbeddedScope[Any], ...], prefix: str = ""
) -> list[tuple[str, str]]:
    """The query parameters of `scopes` and of every scope nested in them,
    each under the dotted path of its embed: `books.title=eq.Dune`,
    `books.order=title`, `books.limit=1`, `books.reviews.offset=2`.

    Several scopes on one embed combine as repeated calls on one scope do:
    their filters all apply, their sort keys go into one `order`, since
    PostgREST reads the first one only, and the last row window wins.
    """
    grouped: dict[str, list[EmbeddedScope[Any]]] = {}
    for scope in scopes:
        grouped.setdefault(f"{prefix}{scope.relation.response_key}", []).append(scope)
    parameters: list[tuple[str, str]] = []
    for path, group in grouped.items():
        windows: dict[str, str] = {}
        for scope in group:
            if scope.filter is not None:
                parameters.extend(
                    (f"{path}.{key}", value)
                    for key, value in scope.filter._query_parameters()
                )
            if scope.row_offset is not None:
                windows["offset"] = str(scope.row_offset)
            if scope.row_limit is not None:
                windows["limit"] = str(scope.row_limit)
        order = [ordering.order_key for scope in group for ordering in scope.orderings]
        if order:
            parameters.append((f"{path}.order", ",".join(order)))
        parameters.extend((f"{path}.{key}", value) for key, value in windows.items())
        nested = tuple(inner for scope in group for inner in scope.scopes)
        parameters.extend(_scope_parameters(nested, f"{path}."))
    return parameters
