from __future__ import annotations

import sys
from collections.abc import Mapping, Sequence
from datetime import date, datetime, time
from decimal import Decimal
from typing import Any, ClassVar, Protocol, Union, cast
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

# Accepted input for write operations (insert/upsert/update).
# Supabase CLI-generated types include datetime/date/time/UUID/Decimal fields,
# which are not strict JSON but serialize to JSON cleanly. Kept separate from
# JSON so inbound response validation stays strict.
JSONSerializable = TypeAliasType(
    "JSONSerializable",
    "Union[None, bool, str, int, float, datetime, date, time, UUID, Decimal, Sequence[JSONSerializable], Mapping[str, JSONSerializable]]",
)


class _TypedDictLike(Protocol):
    # Every TypedDict class defines these attributes and plain mappings don't.
    # Needed because neither mypy nor pyright accepts a TypedDict where a
    # Mapping with concrete value types is expected.
    __required_keys__: ClassVar[frozenset[str]]
    __optional_keys__: ClassVar[frozenset[str]]


# Write inputs additionally accept TypedDict rows, while plain mappings still
# have to satisfy the strict JSONSerializable value types above.
JSONSerializableInput = TypeAliasType(
    "JSONSerializableInput",
    "Union[None, bool, str, int, float, datetime, date, time, UUID, Decimal, Sequence[JSONSerializableInput], Mapping[str, JSONSerializableInput], _TypedDictLike]",
)

_AnyAdapter: TypeAdapter = TypeAdapter(Any)


def jsonable_encoder(value: JSONSerializableInput) -> JSON:
    """Convert datetime/date/time/UUID/Decimal values to JSON-safe primitives.

    Plain JSON passes through unchanged. Mirrors the outbound handling in v3
    (pydantic-based serialization) without changing the httpx request path.
    """
    return cast(JSON, _AnyAdapter.dump_python(value, mode="json"))


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
