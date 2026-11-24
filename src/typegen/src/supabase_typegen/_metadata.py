"""The `GeneratorMetadata` document of `@supabase/postgrest-typegen`, the
introspection contract `supabase gen types` pipes into the generator.

Only the fields the generator reads are declared. They are validated
strictly, so a field of the wrong type is rejected rather than coerced, and
every other field is ignored, so a newer producer that adds fields still
generates.
"""

from __future__ import annotations

import json
from typing import Annotated, Final

from pydantic import ConfigDict, Field, JsonValue, TypeAdapter, ValidationError
from pydantic.dataclasses import dataclass

SUPPORTED_VERSION: Final = 1
"""The `version` of the documents this generator reads."""

_CONFIG = ConfigDict(strict=True, extra="ignore")


@dataclass(frozen=True, kw_only=True, config=_CONFIG)
class Schema:
    name: str


@dataclass(frozen=True, kw_only=True, config=_CONFIG)
class Relation:
    """A table, foreign table, view or materialized view."""

    id: int
    schema: str
    name: str
    comment: str | None = None


@dataclass(frozen=True, kw_only=True, config=_CONFIG)
class View(Relation):
    is_updatable: bool
    is_insert_enabled: bool | None = None
    """Absent from documents that predate it, which read `is_updatable`."""
    is_update_enabled: bool | None = None
    """Absent from documents that predate it, which read `is_updatable`."""


@dataclass(frozen=True, kw_only=True, config=_CONFIG)
class Column:
    table_id: int
    name: str
    default_value: JsonValue = None
    data_type: str
    format: str
    type_schema: str
    is_identity: bool
    identity_generation: str | None = None
    is_generated: bool
    is_nullable: bool
    is_updatable: bool
    comment: str | None = None


@dataclass(frozen=True, kw_only=True, config=_CONFIG)
class PrimaryKey:
    schema: str
    table_name: str
    name: str


@dataclass(frozen=True, kw_only=True, config=_CONFIG)
class Relationship:
    foreign_key_name: str
    schema: str
    relation: str
    columns: tuple[str, ...]
    is_one_to_one: bool
    referenced_schema: str
    referenced_relation: str
    referenced_columns: tuple[str, ...]


@dataclass(frozen=True, kw_only=True, config=_CONFIG)
class FunctionArgument:
    mode: str
    name: str
    type_id: int


@dataclass(frozen=True, kw_only=True, config=_CONFIG)
class Function:
    id: int
    schema: str
    name: str
    args: tuple[FunctionArgument, ...]
    return_type_id: int
    return_type_relation_id: int | None = None
    is_set_returning_function: bool
    prorows: float | None = None
    behavior: str


@dataclass(frozen=True, kw_only=True, config=_CONFIG)
class TypeAttribute:
    name: str
    type_id: int


@dataclass(frozen=True, kw_only=True, config=_CONFIG)
class Type:
    id: int
    name: str
    schema: str
    format: str
    enums: tuple[str, ...]
    attributes: tuple[TypeAttribute, ...]
    comment: str | None = None
    type_relation_id: int | None = None


@dataclass(frozen=True, kw_only=True, config=_CONFIG)
class TypeReference:
    """A `types` entry by oid, with its `format` and `type_schema`, both
    `None` when the type is not in `types`."""

    type_id: int
    format: str | None = None
    type_schema: str | None = None


@dataclass(frozen=True, kw_only=True, config=_CONFIG)
class RpcArgument(TypeReference):
    name: str
    """Empty for an unnamed parameter."""
    has_default: bool
    relation_id: int | None = None
    """The relation whose row type the parameter has."""


@dataclass(frozen=True, kw_only=True, config=_CONFIG)
class RpcColumn(TypeReference):
    name: str
    is_nullable: bool = True
    """Absent from documents that predate it, which read as nullable."""


@dataclass(frozen=True, kw_only=True, config=_CONFIG)
class RpcReturns(TypeReference):
    relation_id: int | None = None
    columns: tuple[RpcColumn, ...] | None = None
    """The columns of a `RETURNS TABLE (…)` result, else `None`."""


@dataclass(frozen=True, kw_only=True, config=_CONFIG)
class RpcOverload:
    function_id: int
    args: tuple[RpcArgument, ...]
    returns: RpcReturns
    is_set_returning: bool
    computed_field_of: int | None = None
    error: str | None = None
    """Why PostgREST cannot resolve a call to this overload."""


@dataclass(frozen=True, kw_only=True, config=_CONFIG)
class RpcFunction:
    schema: str
    name: str
    overloads: tuple[RpcOverload, ...]


@dataclass(frozen=True, kw_only=True, config=_CONFIG)
class GeneratorMetadata:
    version: int
    schemas: tuple[Schema, ...]
    tables: tuple[Relation, ...]
    foreign_tables: Annotated[tuple[Relation, ...], Field(alias="foreignTables")]
    views: tuple[View, ...]
    materialized_views: Annotated[
        tuple[Relation, ...], Field(alias="materializedViews")
    ]
    columns: tuple[Column, ...]
    primary_keys: Annotated[tuple[PrimaryKey, ...], Field(alias="primaryKeys")]
    relationships: tuple[Relationship, ...]
    functions: tuple[Function, ...]
    types: tuple[Type, ...]
    rpc_functions: Annotated[
        tuple[RpcFunction, ...] | None, Field(alias="rpcFunctions")
    ] = None
    """The functions PostgREST exposes under `/rpc`. Absent from documents
    that predate it, which describe none."""


class MetadataError(ValueError):
    """The document is not a `GeneratorMetadata` document this generator
    reads."""


@dataclass(frozen=True, config=ConfigDict(extra="ignore"))
class _Versioned:
    version: JsonValue


_VERSIONED: Final = TypeAdapter(_Versioned)
_ADAPTER: Final = TypeAdapter(GeneratorMetadata)


def parse_generator_metadata(document: str | bytes) -> GeneratorMetadata:
    """The `GeneratorMetadata` of the JSON `document`.

    Raises `MetadataError` when it is not JSON, has another `version` than
    `SUPPORTED_VERSION`, or does not have the shape of the contract.
    """
    try:
        version = _VERSIONED.validate_json(document).version
    except ValidationError as error:
        if any(problem["type"] == "json_invalid" for problem in error.errors()):
            raise MetadataError(f"The document is not JSON: {error}") from error
        raise MetadataError(
            "The document is not a GeneratorMetadata document: it is not a JSON "
            "object with a version."
        ) from error
    if version != SUPPORTED_VERSION or isinstance(version, bool):
        raise MetadataError(
            f"The document has GeneratorMetadata version {json.dumps(version)}, "
            f"but this supabase_typegen reads version {SUPPORTED_VERSION}. "
            "Install the supabase_typegen that matches your Supabase CLI."
        )
    try:
        return _ADAPTER.validate_json(document)
    except ValidationError as error:
        raise MetadataError(
            f"The document does not have the GeneratorMetadata shape: {error}"
        ) from error
