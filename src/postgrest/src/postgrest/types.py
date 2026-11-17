from __future__ import annotations

from collections.abc import Mapping, Sequence
from enum import StrEnum

FilterValue = str | int | float | bool

type RequestBody = Mapping[str, object] | Sequence[Mapping[str, object]]
"""The body of an insert or an upsert: one row, a mapping of column names to
values, or a list of rows.

A type checker sees a TypedDict, such as the `Insert` and `Update` types
`supabase gen types --lang python` generates, as `Mapping[str, object]`,
which `JSON` does not cover. The values are serialized the way pydantic
serializes them, so a `datetime` or a `UUID` is sent as its string, and
`bytes` as the `\\x` hex text PostgreSQL reads for `bytea`.
"""


class CountMethod(StrEnum):
    exact = "exact"
    planned = "planned"
    estimated = "estimated"


class Filters(StrEnum):
    NOT = "not"
    EQ = "eq"
    NEQ = "neq"
    GT = "gt"
    GTE = "gte"
    LT = "lt"
    LTE = "lte"
    IS = "is"
    IS_DISTINCT = "isdistinct"
    LIKE = "like"
    LIKE_ALL = "like(all)"
    LIKE_ANY = "like(any)"
    ILIKE = "ilike"
    ILIKE_ALL = "ilike(all)"
    ILIKE_ANY = "ilike(any)"
    FTS = "fts"
    PLFTS = "plfts"
    PHFTS = "phfts"
    WFTS = "wfts"
    IN = "in"
    CS = "cs"
    CD = "cd"
    OV = "ov"
    SL = "sl"
    SR = "sr"
    NXL = "nxl"
    NXR = "nxr"
    ADJ = "adj"


class Mutation(StrEnum):
    """A write that needs a filter to name the rows it affects."""

    UPDATE = "update"
    DELETE = "delete"


class ResponseShape(StrEnum):
    """The shape of the response a query asks PostgREST for.

    It decides the `Accept` header of the request.
    """

    ROWS = "rows"
    SINGLE = "single"
    CSV = "csv"
    GEOJSON = "geojson"
    PLAN = "plan"


class ReturnMethod(StrEnum):
    minimal = "minimal"
    representation = "representation"


class TextSearchType(StrEnum):
    """How `text_search()` parses its query into a `tsquery`."""

    PLAIN = "plain"
    PHRASE = "phrase"
    WEB_SEARCH = "web_search"


_TEXT_SEARCH_OPERATORS = {
    TextSearchType.PLAIN: Filters.PLFTS,
    TextSearchType.PHRASE: Filters.PHFTS,
    TextSearchType.WEB_SEARCH: Filters.WFTS,
}
