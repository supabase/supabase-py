from __future__ import annotations

import sys
from collections.abc import Mapping, Sequence
from datetime import date, datetime, time
from typing import Union
from uuid import UUID

from httpx import AsyncClient, BasicAuth, Client, Headers, QueryParams
from pydantic import TypeAdapter
from typing_extensions import TypeAliasType
from yarl import URL

if sys.version_info >= (3, 11):
    from enum import StrEnum
else:
    from strenum import StrEnum

# https://docs.pydantic.dev/2.11/concepts/types/#named-recursive-types
JSON = TypeAliasType(
    "JSON", "Union[None, bool, str, int, float, Sequence[JSON], Mapping[str, JSON]]"
)
JSONAdapter: TypeAdapter = TypeAdapter(JSON)
RequestJSON = TypeAliasType(
    "RequestJSON",
    "Union[None, bool, str, int, float, UUID, datetime, date, time, Sequence[RequestJSON], Mapping[str, RequestJSON]]",
)
# TypedDict is exposed by type checkers as Mapping[str, object], so the object
# fallback keeps generated row types assignable while runtime serialization
# still rejects unsupported objects.
WriteJSON = Union[Mapping[str, object], Sequence[Mapping[str, object]]]


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


class RequestMethod(StrEnum):
    GET = "GET"
    POST = "POST"
    PATCH = "PATCH"
    PUT = "PUT"
    DELETE = "DELETE"
    HEAD = "HEAD"


class ReturnMethod(StrEnum):
    minimal = "minimal"
    representation = "representation"
