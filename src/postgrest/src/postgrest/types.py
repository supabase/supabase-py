import json
import sys
from collections.abc import Mapping, Sequence
from typing import Any, Union

from httpx import AsyncClient, BasicAuth, Client, Headers, QueryParams
from pydantic import BeforeValidator, TypeAdapter
from typing_extensions import Annotated, TypeAliasType
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


def _coerce_json(v: Any) -> Any:
    """Coerce raw JSON string to parsed object, or pass through if already deserialized."""
    if isinstance(v, (str, bytes, bytearray)):
        try:
            return json.loads(v)
        except Exception:
            return v
    return v


class _JsonType:
    """
    Flexible Pydantic Json type that accepts both already-deserialized Python objects
    (dicts, lists, scalars) and raw JSON strings.

    Usage:
        class Row(BaseModel):
            json_col: Json                      # accepts dict, list, scalar, or json string
            typed_col: Json[dict[str, int]]      # parses string if needed, validates as dict[str, int]
            model_col: Json[MySubModel]          # parses string or dict into MySubModel
    """

    def __getitem__(self, item: Any) -> Any:
        return Annotated[item, BeforeValidator(_coerce_json)]

    def __get_pydantic_core_schema__(self, source_type: Any, handler: Any) -> Any:
        from pydantic_core import core_schema

        schema = handler(Any)
        return core_schema.no_info_before_validator_function(
            _coerce_json,
            schema,
        )


Json = _JsonType()


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
