from __future__ import annotations

from enum import StrEnum

FilterValue = str | int | float | bool


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
