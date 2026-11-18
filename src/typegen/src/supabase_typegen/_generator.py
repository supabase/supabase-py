"""Generates the Python module of the typed API of postgrest from a
`GeneratorMetadata` document."""

from __future__ import annotations

import re
from collections import Counter, defaultdict
from collections.abc import Callable, Iterable, Sequence
from dataclasses import dataclass, field
from typing import Final

from ._metadata import (
    Column,
    Function,
    GeneratorMetadata,
    Relation,
    Relationship,
    RpcArgument,
    RpcColumn,
    RpcFunction,
    RpcOverload,
    Type,
    TypeReference,
    View,
)
from ._names import (
    claim,
    constant_name,
    member_name,
    pascal_case,
    snake_case,
    unique_names,
)
from ._source import (
    INDENT,
    LINE_TERMINATORS,
    Group,
    docstring,
    from_import,
    string,
)
from .version import __version__

_CATALOG: Final = "pg_catalog"

_TYPE_NAMES: Final = frozenset(
    {
        "Annotated",
        "Any",
        "BaseModel",
        "Bytea",
        "Column",
        "ComputedField",
        "Field",
        "FunctionCall",
        "JSON",
        "JsonValue",
        "Mapping",
        "Never",
        "NotRequired",
        "NullableColumn",
        "StrEnum",
        "Table",
        "ToManyRelation",
        "ToOneRelation",
        "TypedDict",
    }
)
"""The names the module imports, which no generated class takes."""

_ANNOTATION_NAMES: Final = frozenset(
    {"bool", "bytes", "datetime", "dict", "float", "int", "list", "str", "uuid"}
)
"""The lowercase names annotations refer to. A class body looks names up in
itself first, so no attribute of a class with annotations takes one."""

_BASE_MODEL_ATTRIBUTES: Final = frozenset(
    {
        "construct",
        "copy",
        "dict",
        "from_orm",
        "json",
        "model_computed_fields",
        "model_config",
        "model_construct",
        "model_copy",
        "model_dump",
        "model_dump_json",
        "model_extra",
        "model_fields",
        "model_fields_set",
        "model_json_schema",
        "model_parametrized_name",
        "model_post_init",
        "model_rebuild",
        "model_validate",
        "model_validate_json",
        "model_validate_strings",
        "parse_file",
        "parse_obj",
        "parse_raw",
        "schema",
        "schema_json",
        "update_forward_refs",
        "validate",
    }
)
"""The attributes of `pydantic.BaseModel`, which no field may shadow."""

_FIELD_RESERVED: Final = _ANNOTATION_NAMES | _BASE_MODEL_ATTRIBUTES | {"table"}
"""The names no column takes: its name is the field of the row model and
the attribute of the namespace class, whose table is `table`."""

_METHOD_RESERVED: Final = _ANNOTATION_NAMES | {"object", "staticmethod"}
"""The names no method of `Functions` takes."""

_PARAMETER_RESERVED: Final = _ANNOTATION_NAMES | {
    "arguments",
    "item",
    "object",
    "read_only",
    "type",
}
"""The names no parameter of a function call takes, since the body of the
method refers to them."""

_INPUT_MODES: Final = frozenset({"in", "inout", "variadic"})

_RESERVED_QUERY_PARAMETERS: Final = frozenset(
    {"select", "columns", "on_conflict", "order", "limit", "offset", "and", "or"}
)
"""The query parameters PostgREST reads as options of the request rather
than as arguments of a function."""


@dataclass(frozen=True)
class _PythonType:
    """How the module types a Postgres type."""

    annotation: str
    """The type a present value is read as, `datetime.date` for `date`."""

    encode: Callable[[str], str] | None = None
    """The expression that turns a value of the type, given as an expression,
    into JSON, or `None` when the value is JSON already."""

    sent: str | None = None
    """The type a value is written or filtered by, when it is wider than
    `annotation`: `bytes` for a `bytea` read as `Bytea`."""

    decodes: bool = False
    """Whether a value is decoded from its JSON form into another type."""

    is_json: bool = False
    """Whether the value is `json` or of a type the module does not know."""

    fits_query: bool = True
    """Whether a read-only call can send the value as a query parameter,
    which a JSON value or a composite value cannot be."""


_ANY: Final = _PythonType("Any", is_json=True, fits_query=False)
_JSON_VALUE: Final = _PythonType("JsonValue", is_json=True, fits_query=False)
_STR: Final = _PythonType("str")
_INT: Final = _PythonType("int")
_FLOAT: Final = _PythonType("float")


def _isoformat(value: str) -> str:
    return f"{value}.isoformat()"


def _model_dump(value: str) -> str:
    return f'{value}.model_dump(mode="json", by_alias=True)'


_DATE: Final = _PythonType("datetime.date", _isoformat, decodes=True)
_TIME: Final = _PythonType("datetime.time", _isoformat, decodes=True)
_DATETIME: Final = _PythonType("datetime.datetime", _isoformat, decodes=True)

_BUILTIN_TYPES: Final[dict[str, _PythonType]] = {
    "bool": _PythonType("bool"),
    "int2": _INT,
    "int4": _INT,
    "int8": _INT,
    "float4": _FLOAT,
    "float8": _FLOAT,
    "numeric": _FLOAT,
    "bytea": _PythonType(
        "Bytea", lambda value: f'"\\\\x" + {value}.hex()', "bytes", decodes=True
    ),
    "bpchar": _STR,
    "varchar": _STR,
    "text": _STR,
    "date": _DATE,
    "time": _TIME,
    "timetz": _STR,
    "timestamp": _DATETIME,
    "timestamptz": _DATETIME,
    "uuid": _PythonType("uuid.UUID", lambda value: f"str({value})", decodes=True),
    "interval": _STR,
    "json": _JSON_VALUE,
    "jsonb": _JSON_VALUE,
    "int4range": _STR,
    "int4multirange": _STR,
    "int8range": _STR,
    "int8multirange": _STR,
    "numrange": _STR,
    "nummultirange": _STR,
    "tsrange": _STR,
    "tsmultirange": _STR,
    "tstzrange": _STR,
    "tstzmultirange": _STR,
    "daterange": _STR,
    "datemultirange": _STR,
    "record": _PythonType("dict[str, Any]", is_json=True, fits_query=False),
}
"""The Python types of the built-in types of `pg_catalog`."""

_EXTENSION_TYPES: Final[dict[str, _PythonType]] = {
    "citext": _STR,
    "vector": _STR,
    "halfvec": _STR,
    "sparsevec": _STR,
}
"""The Python types of extension types, which live in whichever schema the
extension was created in. PostgREST sends pgvector values as their text."""

_IMPORTS: Final[dict[str, str]] = {
    "Annotated": "typing",
    "Any": "typing",
    "Never": "typing",
    "NotRequired": "typing",
    "TypedDict": "typing",
    "Mapping": "collections.abc",
    "StrEnum": "enum",
    "Bytea": "postgrest",
    "BaseModel": "pydantic",
    "Field": "pydantic",
    "JsonValue": "pydantic",
    "JSON": "supabase_utils.types",
    "Column": "postgrest",
    "ComputedField": "postgrest",
    "FunctionCall": "postgrest",
    "NullableColumn": "postgrest",
    "Table": "postgrest",
    "ToManyRelation": "postgrest",
    "ToOneRelation": "postgrest",
}
"""The module each imported name comes from."""

_STANDARD_LIBRARY: Final = frozenset(
    {"collections.abc", "datetime", "enum", "typing", "uuid"}
)

_ANNOTATION_TOKEN: Final = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_]\w*)?")


def generate(metadata: GeneratorMetadata) -> str:
    """The Python module of the typed tables, views, enums, composite types
    and function calls of every schema of `metadata`.

    Objects are emitted in the order of `metadata`, which
    `sortGeneratorMetadata` of `@supabase/postgrest-typegen` makes
    deterministic; `supabase gen types` sorts it before it runs the
    generator.
    """
    return _Module(metadata).render()


def describes_nothing(metadata: GeneratorMetadata) -> bool:
    """Whether the schemas of `metadata` hold no table, view or materialized
    view with columns, no enum, no composite type and no function."""
    module = _Module(metadata)
    return not (
        module.tables
        or module.emitted_enums()
        or module.emitted_composites()
        or module.rpc_functions()
    )


@dataclass
class _Table:
    """A relation the module declares a row model and a namespace for."""

    relation: Relation
    columns: list[Column]
    is_view: bool
    is_insertable: bool
    is_updatable: bool
    primary_key: list[str] = field(default_factory=list[str])
    row: str = ""
    insert: str | None = None
    update: str | None = None
    namespace: str = ""
    members: dict[str, str] = field(default_factory=dict[str, str])

    @property
    def key(self) -> tuple[str, str]:
        return (self.relation.schema, self.relation.name)

    @property
    def display_name(self) -> str:
        return _display_name(self.relation.schema, self.relation.name)


@dataclass(frozen=True)
class _ComputedField:
    name: str
    type: _PythonType


@dataclass(frozen=True)
class _RelationMember:
    """A `ToOneRelation` or `ToManyRelation` attribute of a namespace."""

    base_name: str
    """The attribute name when no other member of the namespace has it."""

    disambiguated_name: str
    """The attribute name when `base_name` collides, spelling out the
    foreign key columns."""

    target: _Table
    is_to_many: bool
    name: str
    """The name of the table, or of the function of a computed
    relationship, the embedded rows come back under."""

    constraint: str | None
    """The foreign key constraint PostgREST needs as a hint, when the table
    name alone is ambiguous."""

    is_computed: bool = False


@dataclass(frozen=True)
class _Method:
    """One overload of a function with a method on `Functions`."""

    function: RpcFunction
    overload: RpcOverload
    name: str


class _Module:
    def __init__(self, metadata: GeneratorMetadata) -> None:
        self._metadata = metadata
        listed = [schema.name for schema in metadata.schemas]
        self._schemas = set(listed) or {
            relation.schema for relation in self._all_relations()
        }
        self._types_by_id = {type_.id: type_ for type_ in metadata.types}
        self._enums = {
            (type_.schema, type_.name): type_ for type_ in metadata.types if type_.enums
        }
        self._composites = {
            (type_.schema, type_.name): type_
            for type_ in metadata.types
            if type_.attributes
        }
        self._behaviors = {
            function.id: function.behavior for function in metadata.functions
        }
        self._class_names: set[str] = set(_TYPE_NAMES)
        self._type_names: dict[tuple[str, str], str] = {}
        self._imports: set[str] = set()
        self._modules: set[str] = set()
        self.tables = self._described_tables()
        self.tables_by_key = {table.key: table for table in self.tables}
        self.tables_by_id = {table.relation.id: table for table in self.tables}
        self._relationships = [
            relationship
            for relationship in metadata.relationships
            if (relationship.schema, relationship.relation) in self.tables_by_key
            and (relationship.referenced_schema, relationship.referenced_relation)
            in self.tables_by_key
        ]

    def _all_relations(self) -> Iterable[Relation]:
        metadata = self._metadata
        yield from metadata.tables
        yield from metadata.foreign_tables
        yield from metadata.views
        yield from metadata.materialized_views

    def _described_tables(self) -> list[_Table]:
        metadata = self._metadata
        columns: defaultdict[int, list[Column]] = defaultdict(list)
        for column in metadata.columns:
            columns[column.table_id].append(column)
        primary_keys: defaultdict[tuple[str, str], list[str]] = defaultdict(list)
        for primary_key in metadata.primary_keys:
            primary_keys[(primary_key.schema, primary_key.table_name)].append(
                primary_key.name
            )

        def described(
            relation: Relation, *, is_view: bool, insertable: bool, updatable: bool
        ) -> _Table:
            return _Table(
                relation,
                columns[relation.id],
                is_view=is_view,
                is_insertable=insertable,
                is_updatable=updatable,
                primary_key=primary_keys[(relation.schema, relation.name)],
            )

        def included(relations: Iterable[Relation]) -> list[Relation]:
            return [
                relation for relation in relations if relation.schema in self._schemas
            ]

        def view_described(view: View) -> _Table:
            return described(
                view,
                is_view=True,
                insertable=view.is_updatable
                if view.is_insert_enabled is None
                else view.is_insert_enabled,
                updatable=view.is_updatable
                if view.is_update_enabled is None
                else view.is_update_enabled,
            )

        def foreign_table_described(table: Relation) -> _Table:
            # A foreign data wrapper that cannot write reports every column of
            # its tables as not updatable.
            writable = any(column.is_updatable for column in columns[table.id])
            return described(
                table, is_view=False, insertable=writable, updatable=writable
            )

        tables = [
            *(
                described(table, is_view=False, insertable=True, updatable=True)
                for table in included(metadata.tables)
            ),
            *(
                foreign_table_described(table)
                for table in included(metadata.foreign_tables)
            ),
            *(
                view_described(view)
                for view in metadata.views
                if view.schema in self._schemas
            ),
            *(
                described(view, is_view=True, insertable=False, updatable=False)
                for view in included(metadata.materialized_views)
            ),
        ]
        return [table for table in tables if table.columns]

    def _claim_class(self, candidate: str) -> str:
        return claim(self._class_names, candidate)

    def _claim_names(self) -> None:
        for key in self.emitted_enums():
            self._type_names[key] = self._claim_class(_type_base_name(*key))
        for key in self.emitted_composites():
            self._type_names[key] = self._claim_class(_type_base_name(*key))
        for table in self.tables:
            base = _type_base_name(*table.key)
            table.row = self._claim_class(f"{base}Row")
            if table.is_insertable:
                table.insert = self._claim_class(f"{base}Insert")
            if table.is_updatable:
                table.update = self._claim_class(f"{base}Update")
            table.namespace = self._claim_class(base)
            table.members = unique_names(
                (column.name for column in table.columns),
                reserved=_FIELD_RESERVED,
                aliased=True,
            )

    def emitted_enums(self) -> list[tuple[str, str]]:
        """The enums of the generated schemas, and the enums of other schemas
        a generated object refers to, in the order of `types`."""
        referenced = self._referenced_type_keys()
        return [
            key for key in self._enums if key[0] in self._schemas or key in referenced
        ]

    def emitted_composites(self) -> list[tuple[str, str]]:
        """The composite types of the generated schemas, and the composite
        types of other schemas a generated object refers to, in the order of
        `types`."""
        referenced = self._referenced_type_keys()
        return [
            key
            for key in self._composites
            if key[0] in self._schemas or key in referenced
        ]

    def _referenced_type_keys(self) -> set[tuple[str, str]]:
        keys = {
            self._element_key(column.type_schema, column.format)
            for table in self.tables
            for column in table.columns
        }
        for function in self.rpc_functions():
            for overload in function.overloads:
                references: list[TypeReference] = [*overload.args, overload.returns]
                references += overload.returns.columns or ()
                keys |= {
                    self._element_key(reference.type_schema, reference.format)
                    for reference in references
                    if reference.type_schema is not None
                    and reference.format is not None
                }
        for function in self._metadata.functions:
            type_ = self._types_by_id.get(function.return_type_id)
            if type_ is not None:
                keys.add(self._element_key(type_.schema, type_.name))
        pending = [
            key for key in self._composites if key[0] in self._schemas or key in keys
        ]
        seen: set[tuple[str, str]] = set()
        while pending:
            key = pending.pop()
            if key in seen:
                continue
            seen.add(key)
            keys.add(key)
            for attribute in self._composites[key].attributes:
                type_ = self._types_by_id.get(attribute.type_id)
                if type_ is None:
                    continue
                element = self._element_key(type_.schema, type_.name)
                keys.add(element)
                if element in self._composites:
                    pending.append(element)
        return keys

    def _element_key(self, schema: str, name: str) -> tuple[str, str]:
        """The type of the elements of the array type `name`, or `name` itself
        when it is no array type."""
        key = (schema, name)
        if key in self._enums or key in self._composites or not name.startswith("_"):
            return key
        return (schema, name[1:])

    def rpc_functions(self) -> list[RpcFunction]:
        return [
            function
            for function in self._metadata.rpc_functions or ()
            if function.schema in self._schemas
        ]

    def _import(self, name: str) -> str:
        self._imports.add(name)
        return name

    def _annotation(self, python_type: _PythonType, *, sent: bool = False) -> str:
        """The annotation of `python_type`, as it is read or, with `sent`, as
        it is written or filtered by, with the names it refers to imported."""
        annotation = (sent and python_type.sent) or python_type.annotation
        for token in _ANNOTATION_TOKEN.findall(annotation):
            module, _, _ = token.partition(".")
            if module in {"datetime", "uuid"}:
                self._modules.add(module)
            elif token in _IMPORTS:
                self._imports.add(token)
        return annotation

    def _python_type(
        self, format: str, schema: str, *, is_array: bool | None = None
    ) -> _PythonType:
        """The Python type of the type named `format` in `schema`. An array
        type, named `_text` for `text[]`, is a list of its elements, which
        live in the schema of the array type."""
        if is_array is None:
            key = (schema, format)
            is_array = (
                format.startswith("_")
                and key not in self._enums
                and key not in self._composites
            )
        if is_array:
            element = self._python_type(format[1:], schema, is_array=False)
            encode = element.encode
            return _PythonType(
                f"list[{element.annotation}]",
                None
                if encode is None
                else lambda value: f"[{encode('item')} for item in {value}]",
                None if element.sent is None else f"list[{element.sent}]",
                decodes=element.decodes,
                is_json=element.is_json,
                fits_query=element.fits_query,
            )
        key = (schema, format)
        if key in self._enums:
            return _PythonType(self._type_names[key], decodes=True)
        if key in self._composites:
            return _PythonType(
                self._type_names[key], _model_dump, decodes=True, fits_query=False
            )
        if schema == _CATALOG and format in _BUILTIN_TYPES:
            return _BUILTIN_TYPES[format]
        return _EXTENSION_TYPES.get(format, _ANY)

    def _column_type(self, column: Column) -> _PythonType:
        is_array = column.data_type == "ARRAY"
        return self._python_type(column.format, column.type_schema, is_array=is_array)

    def _reference_type(self, reference: TypeReference) -> _PythonType:
        if reference.format is None or reference.type_schema is None:
            return _ANY
        return self._python_type(reference.format, reference.type_schema)

    def _type_of_id(self, type_id: int) -> _PythonType:
        type_ = self._types_by_id.get(type_id)
        if type_ is None:
            return _ANY
        return self._python_type(type_.name, type_.schema)

    def render(self) -> str:
        self._claim_names()
        sections = [self._enum(self._enums[key]) for key in self.emitted_enums()]
        sections += [
            self._composite(self._composites[key]) for key in self.emitted_composites()
        ]
        for table in self.tables:
            sections.append(self._row_model(table))
            if table.insert is not None:
                sections.append(self._values(table, table.insert, is_insert=True))
            if table.update is not None:
                sections.append(self._values(table, table.update, is_insert=False))
        relation_counts = self._relationship_counts()
        computed = self._computed_members()
        for table in self.tables:
            fields, relations = computed.get(table.relation.id, ([], []))
            sections.append(
                self._namespace(
                    table,
                    fields,
                    self._relation_members(table, relation_counts, relations),
                )
            )
        sections.extend(self._functions())
        body = "\n\n\n".join("\n".join(section) for section in sections)
        return f"{self._header()}\n\n\n{body}\n" if body else f"{self._header()}\n"

    def _header(self) -> str:
        schemas = ", ".join(
            LINE_TERMINATORS.sub(" ", name) for name in sorted(self._schemas)
        )
        lines = [
            *docstring(
                f"Typed tables and functions of the schemas {schemas}.",
                f"Generated by supabase_typegen {__version__} from GeneratorMetadata "
                f"version {self._metadata.version}.\nDo not edit by hand; regenerate "
                "with `supabase gen types --lang python`.",
                indent="",
            ),
            "",
            "from __future__ import annotations",
        ]
        standard = [f"import {module}" for module in sorted(self._modules)]
        third_party: list[str] = []
        by_module: defaultdict[str, list[str]] = defaultdict(list)
        for name in self._imports:
            by_module[_IMPORTS[name]].append(name)
        for module in sorted(by_module):
            target = standard if module in _STANDARD_LIBRARY else third_party
            target.extend(from_import(module, sorted(by_module[module])))
        for group in (standard, third_party):
            if group:
                lines += ["", *group]
        return "\n".join(lines)

    def _enum(self, type_: Type) -> list[str]:
        name = self._type_names[(type_.schema, type_.name)]
        members = unique_names(type_.enums, identifier=constant_name)
        lines = [
            f"class {name}({self._import('StrEnum')}):",
            *docstring(
                f"The Postgres enum `{_display_name(type_.schema, type_.name)}`.",
                type_.comment,
                indent=INDENT,
            ),
            "",
        ]
        lines += [
            f"{INDENT}{members[label]} = {string(label)}" for label in type_.enums
        ]
        return lines

    def _composite(self, type_: Type) -> list[str]:
        name = self._type_names[(type_.schema, type_.name)]
        names = unique_names(
            (attribute.name for attribute in type_.attributes),
            reserved=_FIELD_RESERVED,
            aliased=True,
        )
        lines = [
            f"class {name}({self._import('BaseModel')}):",
            *docstring(
                "The Postgres composite type "
                f"`{_display_name(type_.schema, type_.name)}`, whose attributes "
                "can all be `None`.",
                type_.comment,
                indent=INDENT,
            ),
            "",
        ]
        for attribute in type_.attributes:
            python_type = self._type_of_id(attribute.type_id)
            lines += self._model_field(
                names[attribute.name], attribute.name, python_type, nullable=True
            )
        return lines

    def _model_field(
        self, name: str, column: str, python_type: _PythonType, *, nullable: bool
    ) -> list[str]:
        annotation = self._annotation(python_type)
        if nullable:
            annotation = f"{annotation} | None"
        if name == column:
            default = " = None" if nullable else ""
            return [f"{INDENT}{name}: {annotation}{default}"]
        arguments = ["default=None"] if nullable else []
        arguments.append(f"alias={string(column)}")
        field = Group(f"{name}: {annotation} = {self._import('Field')}", arguments)
        return field.lines(INDENT)

    def _row_model(self, table: _Table) -> list[str]:
        kind = "view" if table.is_view else "table"
        lines = [
            f"class {table.row}({self._import('BaseModel')}):",
            *docstring(
                f"A row of the `{table.display_name}` {kind}, as `select()` reads it.",
                table.relation.comment,
                indent=INDENT,
            ),
            "",
        ]
        for column in table.columns:
            lines += self._model_field(
                table.members[column.name],
                column.name,
                self._column_type(column),
                nullable=column.is_nullable,
            )
            lines += docstring(column.comment, indent=INDENT)
        return lines

    def _values(self, table: _Table, name: str, *, is_insert: bool) -> list[str]:
        writable = [column for column in table.columns if _is_writable(column)]
        typed_dict = self._import("TypedDict")
        if is_insert:
            header = f"class {name}({typed_dict}):"
            summary = (
                f"A row to insert into `{table.display_name}`. A column left out "
                "gets its database default, and `None` inserts `NULL`."
            )
        else:
            header = f"class {name}({typed_dict}, total=False):"
            summary = (
                f"The columns to update of `{table.display_name}`. A column left "
                "out keeps its value, and `None` writes `NULL`."
            )
        lines = [header, *docstring(summary, indent=INDENT)]
        if writable:
            lines.append("")
        for column in writable:
            key = table.members[column.name]
            annotation = self._annotation(self._column_type(column), sent=True)
            if column.is_nullable:
                annotation = f"{annotation} | None"
            if key != column.name:
                field = f"{self._import('Field')}(alias={string(column.name)})"
                annotation = f"{self._import('Annotated')}[{annotation}, {field}]"
            if is_insert and not _is_required(column, is_view=table.is_view):
                not_required = self._import("NotRequired")
                lines += Group(f"{key}: {not_required}", [annotation], "[]").lines(
                    INDENT
                )
            else:
                lines.append(f"{INDENT}{key}: {annotation}")
        return lines

    def _computed_members(
        self,
    ) -> dict[int, tuple[list[_ComputedField], list[_RelationMember]]]:
        """The computed fields and computed relationships of each table:
        functions whose only input argument is the row type of the table.

        PostgREST resolves a name to a column first, so a function named like
        a column of its table is neither, and an overload of one is addressed
        by the name of the first. A function of another schema is neither.
        """
        members: dict[int, tuple[list[_ComputedField], list[_RelationMember]]] = {}
        names: defaultdict[int, set[str]] = defaultdict(set)
        for function in self._metadata.functions:
            table = self._computed_member_table(function)
            if table is None:
                continue
            columns = {column.name for column in table.columns}
            if function.name in columns or function.name in names[table.relation.id]:
                continue
            fields, relations = members.setdefault(table.relation.id, ([], []))
            if function.return_type_relation_id is not None:
                target = self.tables_by_id.get(function.return_type_relation_id)
                if target is None:
                    continue
                names[table.relation.id].add(function.name)
                relations.append(
                    _RelationMember(
                        base_name=member_name(function.name),
                        disambiguated_name=member_name(function.name),
                        target=target,
                        is_to_many=function.prorows is not None
                        and function.prorows > 1,
                        name=function.name,
                        constraint=None,
                        is_computed=True,
                    )
                )
                continue
            # A set of scalars has no PostgREST shape to select it by.
            if function.is_set_returning_function:
                continue
            names[table.relation.id].add(function.name)
            fields.append(
                _ComputedField(function.name, self._type_of_id(function.return_type_id))
            )
        return members

    def _computed_member_table(self, function: Function) -> _Table | None:
        inputs = [
            argument for argument in function.args if argument.mode in _INPUT_MODES
        ]
        if len(inputs) != 1:
            return None
        type_ = self._types_by_id.get(inputs[0].type_id)
        if type_ is None or type_.type_relation_id is None:
            return None
        table = self.tables_by_id.get(type_.type_relation_id)
        if table is None or table.relation.schema != function.schema:
            return None
        return table

    def _relationship_counts(self) -> Counter[tuple[tuple[str, str], ...]]:
        """The number of relationships PostgREST sees between each pair of
        tables: the foreign keys in either direction, and the many-to-many
        relationships through a junction table whose primary key covers a
        foreign key to each of the two."""
        counts: Counter[tuple[tuple[str, str], ...]] = Counter()
        for relationship in self._relationships:
            counts[_pair(_source(relationship), _target(relationship))] += 1
        for junction in self.tables:
            primary_key = set(junction.primary_key)
            keys = [
                relationship
                for relationship in self._relationships
                if _source(relationship) == junction.key
                and relationship.referenced_schema == junction.relation.schema
                and relationship.referenced_relation != junction.relation.name
                and primary_key.issuperset(relationship.columns)
            ]
            for index, first in enumerate(keys):
                for second in keys[index + 1 :]:
                    counts[_pair(_target(first), _target(second))] += 1
        return counts

    def _relation_members(
        self,
        table: _Table,
        counts: Counter[tuple[tuple[str, str], ...]],
        computed: list[_RelationMember],
    ) -> list[_RelationMember]:
        """The relations of `table`: one to-one relation per foreign key it
        holds, and one to-many relation, or to-one for a unique key, per
        foreign key pointing at it.

        A self-referential key gets no relation, since PostgREST cannot tell
        its two directions apart, and neither does a key into another
        schema, since PostgREST embeds within the schema of the request only.
        A computed relationship named like the table of an unhinted foreign
        key replaces that relation, since PostgREST resolves the name to the
        function.
        """
        members: list[_RelationMember] = []
        for relationship in self._relationships:
            source = self.tables_by_key[_source(relationship)]
            target = self.tables_by_key[_target(relationship)]
            if source is target or source.relation.schema != target.relation.schema:
                continue
            columns = "_".join(relationship.columns)
            ambiguous = counts[_pair(source.key, target.key)] > 1
            constraint = relationship.foreign_key_name if ambiguous else None
            if source is table:
                name = member_name(target.relation.name)
                disambiguated = member_name(f"{target.relation.name}_by_{columns}")
                members.append(
                    _RelationMember(
                        base_name=disambiguated if ambiguous else name,
                        disambiguated_name=disambiguated,
                        target=target,
                        is_to_many=False,
                        name=target.relation.name,
                        constraint=constraint,
                    )
                )
            if target is table:
                name = member_name(source.relation.name)
                disambiguated = member_name(f"{source.relation.name}_via_{columns}")
                members.append(
                    _RelationMember(
                        base_name=disambiguated if ambiguous else name,
                        disambiguated_name=disambiguated,
                        target=source,
                        is_to_many=not relationship.is_one_to_one,
                        name=source.relation.name,
                        constraint=constraint,
                    )
                )
        overridden = {member.name for member in computed}
        members = [
            member
            for member in members
            if member.constraint is not None or member.name not in overridden
        ]
        return members + computed

    def _namespace(
        self,
        table: _Table,
        fields: list[_ComputedField],
        relations: list[_RelationMember],
    ) -> list[str]:
        row = table.row
        used = set(_FIELD_RESERVED) | set(table.members.values())
        field_names = unique_names(
            (computed_field.name for computed_field in fields), reserved=used
        )
        used |= set(field_names.values())
        relation_names = _relation_names(used, relations)
        aliases = _relation_aliases(
            {column.name for column in table.columns} | set(field_names),
            relations,
            relation_names,
        )
        kind = "view" if table.is_view else "table"
        lines = [
            f"class {table.namespace}:",
            *docstring(
                f"The columns and relations of the `{table.display_name}` {kind}, "
                f"and the table `client.table({table.namespace}.table)` queries.",
                indent=INDENT,
            ),
            "",
        ]
        lines += self._column_attributes(table.columns, row, table.members)
        for computed_field in fields:
            annotation = self._annotation(computed_field.type)
            arguments = [string(computed_field.name)]
            if computed_field.type.decodes:
                arguments.append(annotation)
            callee = f"{self._import('ComputedField')}[{row}, {annotation}]"
            lines += Group(
                f"{field_names[computed_field.name]} = {callee}", arguments
            ).lines(INDENT)
        for index, relation in enumerate(relations):
            kind_name = self._import(
                "ToManyRelation" if relation.is_to_many else "ToOneRelation"
            )
            arguments = [string(relation.name), relation.target.row]
            if relation.constraint is not None:
                arguments.append(f"constraint={string(relation.constraint)}")
            alias = aliases[index]
            if alias is not None:
                arguments.append(f"alias={string(alias)}")
            arguments.append(f"target_table=lambda: {relation.target.namespace}.table")
            lines += Group(
                f"{relation_names[index]} = {kind_name}[{row}, {relation.target.row}]",
                arguments,
            ).lines(INDENT)
        never = (
            self._import("Never")
            if table.insert is None or table.update is None
            else ""
        )
        insert = table.insert or never
        update = table.update or never
        arguments: list[str | Group] = [string(table.relation.name), row]
        if table.insert is not None:
            arguments.append(f"insert_type={table.insert}")
        if table.update is not None:
            arguments.append(f"update_type={table.update}")
        if table.primary_key:
            key = [table.members[column] for column in table.primary_key]
            arguments.append(Group("primary_key=", key, is_tuple=True))
        if fields:
            names = [field_names[computed.name] for computed in fields]
            arguments.append(Group("computed_fields=", names, is_tuple=True))
        if relations:
            arguments.append(Group("relations=", relation_names, is_tuple=True))
        arguments.append(f"schema={string(table.relation.schema)}")
        lines += Group(
            f"table: {self._import('Table')}[{row}, {insert}, {update}] = Table",
            arguments,
            explode=True,
        ).lines(INDENT)
        return lines

    def _column_attributes(
        self, columns: Sequence[Column | RpcColumn], row: str, members: dict[str, str]
    ) -> list[str]:
        lines: list[str] = []
        for column in columns:
            if isinstance(column, Column):
                python_type = self._column_type(column)
                comment = column.comment
            else:
                python_type = self._reference_type(column)
                comment = None
            kind = self._import("NullableColumn" if column.is_nullable else "Column")
            lines += Group(
                f"{members[column.name]} = {kind}[{row}, {self._annotation(python_type, sent=True)}]",
                [string(column.name)],
            ).lines(INDENT)
            lines += docstring(comment, indent=INDENT)
        return lines

    def _functions(self) -> list[list[str]]:
        functions = self.rpc_functions()
        methods = self._methods(functions)
        unsupported = [
            (function, overload, reason)
            for function in functions
            for overload in function.overloads
            if overload.computed_field_of is None
            for reason in [_unsupported_reason(overload)]
            if reason is not None
        ]
        if not methods and not unsupported:
            return []
        sections: list[list[str]] = []
        result_rows: dict[int, tuple[str, str]] = {}
        for index, method in enumerate(methods):
            columns = method.overload.returns.columns
            if columns is None:
                continue
            base = pascal_case(method.name)
            row = self._claim_class(f"{base}Row")
            namespace = self._claim_class(base)
            result_rows[index] = (row, namespace)
            sections.append(self._result_row(method, columns, row, namespace))
        name = self._claim_class("Functions")
        lines = [
            f"class {name}:",
            *docstring(
                "Typed calls of the database functions, run with "
                f"`client.rpc({name}.function_name(...))`.",
                "\n".join(
                    f"`{_display_name(function.schema, function.name)}"
                    f"({_signature(overload)})` has no method: {reason}"
                    for function, overload, reason in unsupported
                ),
                indent=INDENT,
            ),
        ]
        for index, method in enumerate(methods):
            lines += ["", *self._method(method, result_rows.get(index))]
        sections.append(lines)
        return sections

    def _methods(self, functions: Iterable[RpcFunction]) -> list[_Method]:
        """The methods of the callable overloads of `functions`.

        A function with one callable overload is named after the function,
        with the schema as a prefix outside `public`. Of several overloads,
        the first one with the fewest arguments keeps that name and every
        other one spells out its arguments, `books_of_with_author_name_and_max_price`.
        """
        used = set(_METHOD_RESERVED)
        methods: list[_Method] = []
        for function in functions:
            callable_overloads = [
                overload
                for overload in function.overloads
                if _unsupported_reason(overload) is None
            ]
            if not callable_overloads:
                continue
            base = member_name(
                function.name
                if function.schema == "public"
                else f"{function.schema}_{function.name}"
            )
            plain = min(callable_overloads, key=lambda overload: len(overload.args))
            for overload in callable_overloads:
                if overload is plain:
                    name = base
                else:
                    spelled = "_and_".join(
                        argument.name or "body" for argument in overload.args
                    )
                    name = f"{base}_with_{snake_case(spelled)}"
                methods.append(_Method(function, overload, claim(used, name)))
        return methods

    def _result_row(
        self, method: _Method, columns: Sequence[RpcColumn], row: str, namespace: str
    ) -> list[str]:
        display = _display_name(method.function.schema, method.function.name)
        members = unique_names(
            (column.name for column in columns), reserved=_FIELD_RESERVED, aliased=True
        )
        lines = [
            f"class {row}({self._import('BaseModel')}):",
            *docstring(f"A row the `{display}` function returns.", indent=INDENT),
            "",
        ]
        for column in columns:
            lines += self._model_field(
                members[column.name],
                column.name,
                self._reference_type(column),
                nullable=column.is_nullable,
            )
        lines += [
            "",
            "",
            f"class {namespace}:",
            *docstring(
                f"The columns of the rows the `{display}` function returns, to "
                "filter and order them by.",
                indent=INDENT,
            ),
            "",
            *self._column_attributes(columns, row, members),
        ]
        return lines

    def _method(self, method: _Method, result_row: tuple[str, str] | None) -> list[str]:
        function, overload = method.function, method.overload
        behavior = self._behaviors.get(overload.function_id)
        offers_read_only = behavior in {"STABLE", "IMMUTABLE"} and all(
            self._is_query_parameter(argument) for argument in overload.args
        )
        names = unique_names(
            (argument.name for argument in overload.args),
            reserved=_PARAMETER_RESERVED,
        )
        required: list[str] = []
        optional: list[str] = []
        entries: list[str] = []
        optional_entries: list[tuple[str, str, str]] = []
        body: str | None = None
        for argument in overload.args:
            python_type = self._argument_type(argument)
            if not argument.name:
                mapping = self._import("Mapping")
                required.append(f"body: {mapping}[str, {self._import('JSON')}]")
                body = "body"
                continue
            name = names[argument.name]
            annotation = self._annotation(python_type, sent=True)
            value = name if python_type.encode is None else python_type.encode(name)
            if argument.has_default:
                optional.append(f"{name}: {annotation} | None = None")
                optional_entries.append((name, string(argument.name), value))
            else:
                required.append(f"{name}: {annotation}")
                entries.append(f"{string(argument.name)}: {value}")
        parameters = [*required, *optional]
        if offers_read_only:
            parameters.append("read_only: bool = False")
        if parameters and body is None:
            parameters.insert(0, "*")

        result = self._result(overload, result_row)
        display = _display_name(function.schema, function.name)
        summary = f"Calls the `{display}` function{result.description}."
        if optional:
            summary += " An argument left out, or `None`, takes its default."
        if offers_read_only:
            summary += (
                " With `read_only`, it is called with a `GET` request in a "
                "read-only transaction, and retried like a select."
            )
        lines = [
            f"{INDENT}@staticmethod",
            *Group(f"def {method.name}", parameters, is_signature=True).lines(
                INDENT, f" -> {result.annotation}:"
            ),
            *docstring(summary, indent=INDENT * 2),
        ]
        call_arguments: list[str | Group] = [string(function.name), result.decoded]
        if body is not None:
            call_arguments.append(f"arguments={body}")
        elif optional_entries:
            json_type = self._import("JSON")
            lines += Group(
                f"arguments: dict[str, {json_type}] = ", entries, brackets="{}"
            ).lines(INDENT * 2)
            for name, key, value in optional_entries:
                lines += [
                    f"{INDENT * 2}if {name} is not None:",
                    f"{INDENT * 3}arguments[{key}] = {value}",
                ]
            call_arguments.append("arguments=arguments")
        elif entries:
            call_arguments.append(Group("arguments=", entries, brackets="{}"))
        call_arguments.append(f"schema={string(function.schema)}")
        if offers_read_only:
            call_arguments.append("read_only=read_only")
        function_call = self._import("FunctionCall")
        lines += Group(f"return {function_call}.{result.method}", call_arguments).lines(
            INDENT * 2
        )
        return lines

    def _argument_type(self, argument: RpcArgument) -> _PythonType:
        if argument.relation_id is not None:
            table = self.tables_by_id.get(argument.relation_id)
            if table is not None:
                return _PythonType(
                    table.row, _model_dump, decodes=True, fits_query=False
                )
        return self._reference_type(argument)

    def _is_query_parameter(self, argument: RpcArgument) -> bool:
        """Whether a read-only call can send `argument` as a query parameter:
        it is named, PostgREST does not read the name as an option of the
        request or an embed path, and it is neither a row, a composite value
        nor `json`, which only a request body carries."""
        return (
            bool(argument.name)
            and "." not in argument.name
            and argument.name not in _RESERVED_QUERY_PARAMETERS
            and self._argument_type(argument).fits_query
        )

    def _result(
        self, overload: RpcOverload, result_row: tuple[str, str] | None
    ) -> _Result:
        function_call = self._import("FunctionCall")
        never = "Never"
        returns = overload.returns

        def rows(row: str, description: str) -> _Result:
            return _Result(
                f"{function_call}[{row}, list[{row}]]", "rows", row, description
            )

        def value(annotation: str, decoded: str, description: str = "") -> _Result:
            self._import(never)
            result = (
                annotation
                if annotation in {"None", "object"}
                else f"{annotation} | None"
            )
            return _Result(
                f"{function_call}[{never}, {result}]", "value", decoded, description
            )

        if result_row is not None:
            row, namespace = result_row
            return rows(row, f", which returns rows to filter by `{namespace}`")
        table = (
            None
            if returns.relation_id is None
            else self.tables_by_id.get(returns.relation_id)
        )
        if table is not None:
            if overload.is_set_returning:
                return rows(
                    table.row,
                    f", which returns rows of `{table.display_name}` to filter by "
                    f"`{table.namespace}`",
                )
            return value(
                table.row,
                table.row,
                f", which returns a row of `{table.display_name}`",
            )
        if returns.format == "void" and returns.type_schema == _CATALOG:
            return value("None", "type(None)")
        if returns.relation_id is not None or returns.format == "record":
            python_type = _JSON_VALUE
        else:
            python_type = self._reference_type(returns)
        if python_type.is_json:
            annotation = "list[object]" if overload.is_set_returning else "object"
            return value(annotation, annotation)
        annotation = self._annotation(python_type)
        if overload.is_set_returning:
            annotation = f"list[{annotation} | None]"
        return value(annotation, annotation)


@dataclass(frozen=True)
class _Result:
    """What the method of a function returns."""

    annotation: str
    method: str
    """`rows` or `value`, the `FunctionCall` constructor it calls."""
    decoded: str
    """The type the result, or each row of it, decodes into."""
    description: str = ""


def _unsupported_reason(overload: RpcOverload) -> str | None:
    """Why the module cannot call `overload`, or `None` when it can.

    PostgREST passes an unnamed parameter only when it is the sole parameter
    and of type `json` or `jsonb`, as the whole request body.
    """
    if overload.error is not None:
        return overload.error
    unnamed = [argument for argument in overload.args if not argument.name]
    if not unnamed:
        return None
    if (
        len(overload.args) == 1
        and overload.args[0].relation_id is None
        and overload.args[0].format in {"json", "jsonb"}
    ):
        return None
    return (
        "PostgREST only passes an unnamed parameter that is the sole one and of "
        "type json or jsonb; call it through `client.rpc` with its name instead"
    )


def _signature(overload: RpcOverload) -> str:
    return ", ".join(
        f"{argument.name} {argument.format}" if argument.name else str(argument.format)
        for argument in overload.args
    )


def _is_writable(column: Column) -> bool:
    return (
        column.identity_generation != "ALWAYS"
        and not column.is_generated
        and column.is_updatable
    )


def _is_required(column: Column, *, is_view: bool) -> bool:
    """Whether an insert must give `column`: it is not nullable and has no
    default. A view column does not carry the default of the column it
    reads, so an insert through a view may leave any column out."""
    has_default = (
        column.default_value is not None or column.is_identity or column.is_generated
    )
    return not is_view and not column.is_nullable and not has_default


def _source(relationship: Relationship) -> tuple[str, str]:
    return (relationship.schema, relationship.relation)


def _target(relationship: Relationship) -> tuple[str, str]:
    return (relationship.referenced_schema, relationship.referenced_relation)


def _pair(
    first: tuple[str, str], second: tuple[str, str]
) -> tuple[tuple[str, str], ...]:
    return tuple(sorted((first, second)))


def _relation_names(used: set[str], relations: list[_RelationMember]) -> list[str]:
    """The attribute names of `relations` next to the names in `used`, which
    claiming them adds to."""
    counts = Counter(relation.base_name for relation in relations)
    return [
        claim(
            used,
            relation.disambiguated_name
            if relation.base_name in used or counts[relation.base_name] > 1
            else relation.base_name,
        )
        for relation in relations
    ]


def _relation_aliases(
    field_names: set[str], relations: list[_RelationMember], names: list[str]
) -> list[str | None]:
    """The alias of each of `relations`, or `None` for one that comes back
    under its plain name.

    A hinted relation comes back under its attribute name, and so does one
    whose plain name is also the name of a column or computed field of the
    table, which would otherwise come back under the same key. Aliases are
    kept apart from every other key of the table.
    """

    def needs_alias(relation: _RelationMember) -> bool:
        return relation.constraint is not None or relation.name in field_names

    used = field_names | {
        relation.name for relation in relations if not needs_alias(relation)
    }
    aliases: list[str | None] = []
    for relation, name in zip(relations, names, strict=True):
        if not needs_alias(relation):
            aliases.append(None)
            continue
        alias = candidate = snake_case(name)
        number = 2
        while alias in used:
            alias = f"{candidate}_{number}"
            number += 1
        used.add(alias)
        aliases.append(alias)
    return aliases


def _type_base_name(schema: str, name: str) -> str:
    """The PascalCase base of the class names of a schema object: the name
    alone in `public`, prefixed with the schema elsewhere."""
    return pascal_case(name if schema == "public" else f"{schema}_{name}")


def _display_name(schema: str, name: str) -> str:
    """How documentation refers to a schema object: bare in `public`,
    qualified with its schema elsewhere."""
    return LINE_TERMINATORS.sub(" ", name if schema == "public" else f"{schema}.{name}")
