"""A `GeneratorMetadata` document of names and shapes that are hard to
generate: keywords, names the module uses itself, names that convert to the
same identifier, comments that would break out of a docstring, ambiguous
foreign keys, and functions PostgREST calls in unusual ways."""

from __future__ import annotations

from typing import Any

JsonObject = dict[str, Any]

BUILTINS = {
    "bool": 16,
    "bytea": 17,
    "int8": 20,
    "int4": 23,
    "text": 25,
    "json": 114,
    "_text": 1009,
    "date": 1082,
    "time": 1083,
    "timestamptz": 1184,
    "interval": 1186,
    "numeric": 1700,
    "record": 2249,
    "void": 2278,
    "uuid": 2950,
    "_uuid": 2951,
    "jsonb": 3802,
    "_date": 1182,
    "int4range": 3904,
}


def builtin_type(name: str) -> JsonObject:
    return {
        "id": BUILTINS[name],
        "name": name,
        "schema": "pg_catalog",
        "format": f"{name[1:]}[]" if name.startswith("_") else name,
        "enums": [],
        "attributes": [],
        "comment": None,
        "type_relation_id": None,
    }


def user_type(
    type_id: int,
    schema: str,
    name: str,
    *,
    enums: list[str] | None = None,
    attributes: list[tuple[str, int]] | None = None,
    relation_id: int | None = None,
    comment: str | None = None,
) -> JsonObject:
    return {
        "id": type_id,
        "name": name,
        "schema": schema,
        "format": name,
        "enums": enums or [],
        "attributes": [
            {"name": attribute, "type_id": attribute_type}
            for attribute, attribute_type in attributes or []
        ],
        "comment": comment,
        "type_relation_id": relation_id,
    }


def table(
    relation_id: int, schema: str, name: str, comment: str | None = None
) -> JsonObject:
    return {
        "id": relation_id,
        "schema": schema,
        "name": name,
        "rls_enabled": False,
        "rls_forced": False,
        "replica_identity": "DEFAULT",
        "bytes": 0,
        "size": "0 bytes",
        "live_rows_estimate": 0,
        "dead_rows_estimate": 0,
        "comment": comment,
    }


def column(
    relation_id: int,
    schema: str,
    relation: str,
    name: str,
    format: str,
    *,
    type_schema: str = "pg_catalog",
    nullable: bool = False,
    default: str | None = None,
    identity: str | None = None,
    generated: bool = False,
    updatable: bool = True,
    comment: str | None = None,
) -> JsonObject:
    return {
        "table_id": relation_id,
        "schema": schema,
        "table": relation,
        "id": f"{relation_id}.1",
        "ordinal_position": 1,
        "name": name,
        "default_value": default,
        "data_type": "ARRAY" if format.startswith("_") else format,
        "format": format,
        "type_schema": type_schema,
        "is_identity": identity is not None,
        "identity_generation": identity,
        "is_generated": generated,
        "is_nullable": nullable,
        "is_updatable": updatable,
        "is_unique": False,
        "enums": [],
        "check": None,
        "comment": comment,
    }


def relationship(
    name: str,
    source: tuple[str, str, list[str]],
    target: tuple[str, str, list[str]],
    *,
    one_to_one: bool = False,
) -> JsonObject:
    return {
        "foreign_key_name": name,
        "schema": source[0],
        "relation": source[1],
        "columns": source[2],
        "is_one_to_one": one_to_one,
        "referenced_schema": target[0],
        "referenced_relation": target[1],
        "referenced_columns": target[2],
    }


def primary_key(schema: str, relation: str, relation_id: int, name: str) -> JsonObject:
    return {
        "schema": schema,
        "table_name": relation,
        "name": name,
        "table_id": relation_id,
    }


def function(
    function_id: int,
    schema: str,
    name: str,
    args: list[tuple[str, str, int]],
    return_type_id: int,
    *,
    return_relation_id: int | None = None,
    set_returning: bool = False,
    prorows: float | None = None,
    behavior: str = "STABLE",
) -> JsonObject:
    return {
        "id": function_id,
        "schema": schema,
        "name": name,
        "language": "sql",
        "definition": "select 1",
        "complete_statement": "CREATE FUNCTION ...",
        "args": [
            {"mode": mode, "name": arg, "type_id": arg_type, "has_default": False}
            for mode, arg, arg_type in args
        ],
        "argument_types": "",
        "identity_argument_types": "",
        "return_type_id": return_type_id,
        "return_type": "",
        "return_type_relation_id": return_relation_id,
        "is_set_returning_function": set_returning,
        "prorows": prorows,
        "behavior": behavior,
        "security_definer": False,
        "config_params": None,
    }


def reference(type_id: int, format: str | None, type_schema: str | None) -> JsonObject:
    return {"type_id": type_id, "format": format, "type_schema": type_schema}


def builtin_reference(name: str) -> JsonObject:
    return reference(BUILTINS[name], name, "pg_catalog")


def argument(
    name: str,
    type_reference: JsonObject,
    *,
    default: bool = False,
    relation_id: int | None = None,
) -> JsonObject:
    return {
        **type_reference,
        "name": name,
        "mode": "in",
        "has_default": default,
        "relation_id": relation_id,
    }


def overload(
    function_id: int,
    args: list[JsonObject],
    returns: JsonObject,
    *,
    set_returning: bool = False,
    relation_id: int | None = None,
    columns: list[JsonObject] | None = None,
    computed_field_of: int | None = None,
    error: str | None = None,
) -> JsonObject:
    return {
        "function_id": function_id,
        "args": args,
        "returns": {**returns, "relation_id": relation_id, "columns": columns},
        "is_set_returning": set_returning,
        "rows_estimate": None,
        "setof_options": None,
        "computed_field_of": computed_field_of,
        "error": error,
    }


HOSTILE_COMMENT = (
    'Says """hi""" with a \\ backslash,\r\na\ttab, a trailing quote "\n'
    "    and an indented line\u2028after a line separator"
)

# Relation ids.
CLASS_TABLE = 100
TABLE_TABLE = 101
PEOPLE = 102
FRIENDSHIPS = 103
DOCUMENTS = 104
TAGS = 105
DOCUMENT_TAGS = 106
OTHER_ITEMS = 107
REMOTE = 108
READ_ONLY_REMOTE = 109
LEGACY_VIEW = 110
FUNCTIONS_TABLE = 111

# User type ids.
STATUS = 200
ADDRESS = 201
GEO = 202
OTHER_STATUS = 203
PEOPLE_ROW_TYPE = 204
DOCUMENTS_ROW_TYPE = 205
STATUS_ARRAY = 206
CLASS_ROW_TYPE = 208
DOCUMENT_TAGS_ROW_TYPE = 209


def hostile_metadata() -> JsonObject:
    """The document, sorted as `sortGeneratorMetadata` sorts it."""
    status_labels = [
        "Happy",
        "happy",
        "very-happy",
        "2nd",
        "-",
        'say "hi"',
        "back\\slash",
    ]
    return {
        "version": 1,
        "schemas": [
            {"id": 1, "name": "other", "owner": "postgres"},
            {"id": 2, "name": "public", "owner": "postgres"},
        ],
        "tables": [
            table(OTHER_ITEMS, "other", "items"),
            table(CLASS_TABLE, "public", "class", HOSTILE_COMMENT),
            table(DOCUMENT_TAGS, "public", "document_tags"),
            table(DOCUMENTS, "public", "documents"),
            table(FRIENDSHIPS, "public", "friendships"),
            table(FUNCTIONS_TABLE, "public", "functions"),
            table(PEOPLE, "public", "people"),
            table(TABLE_TABLE, "public", "table"),
            table(TAGS, "public", "tags"),
        ],
        "foreignTables": [
            {**table(READ_ONLY_REMOTE, "public", "read_only_remote"), "columns": None},
            {**table(REMOTE, "public", "remote"), "columns": None},
        ],
        "views": [
            {
                **table(LEGACY_VIEW, "public", "legacy_view"),
                "is_updatable": True,
            }
        ],
        "materializedViews": [],
        "columns": [
            column(OTHER_ITEMS, "other", "items", "id", "int8"),
            column(
                OTHER_ITEMS,
                "other",
                "items",
                "status",
                "status",
                type_schema="other",
            ),
            column(CLASS_TABLE, "public", "class", "2fa", "bool", default="false"),
            column(CLASS_TABLE, "public", "class", "Name", "text", nullable=True),
            column(
                CLASS_TABLE,
                "public",
                "class",
                "address",
                "address",
                type_schema="public",
                nullable=True,
            ),
            column(CLASS_TABLE, "public", "class", "createdAt", "timestamptz"),
            column(CLASS_TABLE, "public", "class", "datetime", "date", nullable=True),
            column(
                CLASS_TABLE,
                "public",
                "class",
                "embedding",
                "vector",
                type_schema="extensions",
                nullable=True,
            ),
            column(CLASS_TABLE, "public", "class", "from", "int4", identity="ALWAYS"),
            column(
                CLASS_TABLE,
                "public",
                "class",
                "id",
                "uuid",
                default="gen_random_uuid()",
            ),
            column(CLASS_TABLE, "public", "class", "json", "jsonb", nullable=True),
            column(
                CLASS_TABLE, "public", "class", "model_config", "text", nullable=True
            ),
            column(
                CLASS_TABLE,
                "public",
                "class",
                "mystery",
                "tsvector",
                type_schema="other_extension",
                nullable=True,
            ),
            column(CLASS_TABLE, "public", "class", "name", "text"),
            column(CLASS_TABLE, "public", "class", "payload", "bytea", nullable=True),
            column(
                CLASS_TABLE, "public", "class", "period", "int4range", nullable=True
            ),
            column(
                CLASS_TABLE,
                "public",
                "class",
                "schema",
                "text",
                generated=True,
                comment=HOSTILE_COMMENT,
            ),
            column(CLASS_TABLE, "public", "class", "starts", "time", nullable=True),
            column(
                CLASS_TABLE,
                "public",
                "class",
                "statuses",
                "_status",
                type_schema="public",
                nullable=True,
            ),
            column(CLASS_TABLE, "public", "class", "str", "text", nullable=True),
            column(CLASS_TABLE, "public", "class", "table", "text", nullable=True),
            column(CLASS_TABLE, "public", "class", "took", "interval", nullable=True),
            column(
                CLASS_TABLE, "public", "class", "victory road", "text", nullable=True
            ),
            column(
                CLASS_TABLE,
                "public",
                "class",
                "статус",
                "status",
                type_schema="public",
                nullable=True,
            ),
            column(DOCUMENT_TAGS, "public", "document_tags", "document_id", "int8"),
            column(DOCUMENT_TAGS, "public", "document_tags", "tag_id", "int8"),
            column(DOCUMENTS, "public", "documents", "author_id", "int8"),
            column(
                DOCUMENTS, "public", "documents", "editor_id", "int8", nullable=True
            ),
            column(
                DOCUMENTS, "public", "documents", "id", "int8", identity="BY DEFAULT"
            ),
            column(
                DOCUMENTS, "public", "documents", "other_item_id", "int8", nullable=True
            ),
            column(DOCUMENTS, "public", "documents", "people", "text", nullable=True),
            column(FRIENDSHIPS, "public", "friendships", "friend_id", "int8"),
            column(FRIENDSHIPS, "public", "friendships", "person_id", "int8"),
            column(FUNCTIONS_TABLE, "public", "functions", "id", "int8"),
            column(LEGACY_VIEW, "public", "legacy_view", "id", "int8"),
            column(PEOPLE, "public", "people", "id", "int8"),
            column(PEOPLE, "public", "people", "mentor_id", "int8", nullable=True),
            column(PEOPLE, "public", "people", "name", "text"),
            column(
                READ_ONLY_REMOTE,
                "public",
                "read_only_remote",
                "id",
                "int8",
                updatable=False,
            ),
            column(REMOTE, "public", "remote", "id", "int8"),
            column(TABLE_TABLE, "public", "table", "id", "int8"),
            column(TAGS, "public", "tags", "document_tags", "text", nullable=True),
            column(TAGS, "public", "tags", "id", "int8"),
            column(TAGS, "public", "tags", "label", "text"),
        ],
        "primaryKeys": [
            primary_key("public", "class", CLASS_TABLE, "id"),
            primary_key("public", "document_tags", DOCUMENT_TAGS, "document_id"),
            primary_key("public", "document_tags", DOCUMENT_TAGS, "tag_id"),
            primary_key("public", "documents", DOCUMENTS, "id"),
            primary_key("public", "friendships", FRIENDSHIPS, "person_id"),
            primary_key("public", "friendships", FRIENDSHIPS, "friend_id"),
            primary_key("public", "people", PEOPLE, "id"),
        ],
        "relationships": [
            relationship(
                "document_tags_document_id_fkey",
                ("public", "document_tags", ["document_id"]),
                ("public", "documents", ["id"]),
            ),
            relationship(
                "document_tags_tag_id_fkey",
                ("public", "document_tags", ["tag_id"]),
                ("public", "tags", ["id"]),
            ),
            relationship(
                "documents_author_id_fkey",
                ("public", "documents", ["author_id"]),
                ("public", "people", ["id"]),
            ),
            relationship(
                "documents_editor_id_fkey",
                ("public", "documents", ["editor_id"]),
                ("public", "people", ["id"]),
            ),
            relationship(
                "documents_other_item_id_fkey",
                ("public", "documents", ["other_item_id"]),
                ("other", "items", ["id"]),
            ),
            relationship(
                "friendships_friend_id_fkey",
                ("public", "friendships", ["friend_id"]),
                ("public", "people", ["id"]),
            ),
            relationship(
                "friendships_person_id_fkey",
                ("public", "friendships", ["person_id"]),
                ("public", "people", ["id"]),
            ),
            relationship(
                "people_mentor_id_fkey",
                ("public", "people", ["mentor_id"]),
                ("public", "people", ["id"]),
            ),
        ],
        "functions": [
            function(
                300,
                "public",
                "class_label",
                [("in", "", CLASS_ROW_TYPE)],
                BUILTINS["text"],
            ),
            function(
                301,
                "public",
                "tags",
                [("in", "", DOCUMENTS_ROW_TYPE)],
                0,
                return_relation_id=TAGS,
                set_returning=True,
                prorows=1000,
            ),
            function(
                302,
                "public",
                "people",
                [("in", "document", DOCUMENTS_ROW_TYPE)],
                0,
                return_relation_id=PEOPLE,
                prorows=0,
            ),
            function(
                303,
                "public",
                "staticmethod",
                [("in", "from", BUILTINS["int4"])],
                BUILTINS["int4"],
            ),
            function(304, "public", "touch", [], BUILTINS["void"], behavior="VOLATILE"),
            function(305, "public", "addresses", [], ADDRESS, set_returning=True),
            function(306, "public", "pick", [], BUILTINS["record"], set_returning=True),
            function(307, "other", "ping", [], BUILTINS["text"]),
            function(
                308,
                "public",
                "echo_text",
                [("in", "", BUILTINS["text"])],
                BUILTINS["text"],
            ),
            function(
                309,
                "public",
                "people_named",
                [("in", "name", BUILTINS["text"])],
                0,
                return_relation_id=PEOPLE,
                set_returning=True,
                prorows=1000,
            ),
            function(
                310, "public", "keywords", [], BUILTINS["record"], set_returning=True
            ),
            function(311, "public", "first_person", [], 0, return_relation_id=PEOPLE),
            function(
                315,
                "public",
                "tags",
                [("in", "", DOCUMENT_TAGS_ROW_TYPE)],
                0,
                return_relation_id=TAGS,
                set_returning=True,
                prorows=1000,
            ),
        ],
        "types": [
            builtin_type("bool"),
            builtin_type("bytea"),
            builtin_type("int8"),
            builtin_type("int4"),
            builtin_type("text"),
            builtin_type("json"),
            builtin_type("_text"),
            builtin_type("date"),
            builtin_type("_date"),
            builtin_type("time"),
            builtin_type("timestamptz"),
            builtin_type("interval"),
            builtin_type("numeric"),
            builtin_type("record"),
            builtin_type("void"),
            builtin_type("uuid"),
            builtin_type("_uuid"),
            builtin_type("jsonb"),
            builtin_type("int4range"),
            user_type(OTHER_STATUS, "other", "status", enums=["on", "off"]),
            user_type(
                ADDRESS,
                "public",
                "address",
                attributes=[
                    ("street", BUILTINS["text"]),
                    ("class", BUILTINS["text"]),
                    ("geo", GEO),
                    ("moved_on", BUILTINS["_date"]),
                ],
                comment="A postal address",
            ),
            user_type(
                GEO,
                "public",
                "geo",
                attributes=[("lat", BUILTINS["numeric"]), ("lng", BUILTINS["numeric"])],
            ),
            user_type(CLASS_ROW_TYPE, "public", "class", relation_id=CLASS_TABLE),
            user_type(DOCUMENTS_ROW_TYPE, "public", "documents", relation_id=DOCUMENTS),
            user_type(
                DOCUMENT_TAGS_ROW_TYPE,
                "public",
                "document_tags",
                relation_id=DOCUMENT_TAGS,
            ),
            user_type(PEOPLE_ROW_TYPE, "public", "people", relation_id=PEOPLE),
            user_type(
                STATUS,
                "public",
                "status",
                enums=status_labels,
                comment='Where a "class" stands',
            ),
            user_type(STATUS_ARRAY, "public", "_status"),
        ],
        "rpcFunctions": [
            {
                "schema": "other",
                "name": "ping",
                "overloads": [overload(307, [], builtin_reference("text"))],
            },
            {
                "schema": "public",
                "name": "addresses",
                "overloads": [
                    overload(
                        305,
                        [],
                        reference(ADDRESS, "address", "public"),
                        set_returning=True,
                    )
                ],
            },
            {
                "schema": "public",
                "name": "class_label",
                "overloads": [
                    overload(
                        300,
                        [
                            argument(
                                "",
                                reference(CLASS_ROW_TYPE, "class", "public"),
                                relation_id=CLASS_TABLE,
                            )
                        ],
                        builtin_reference("text"),
                        computed_field_of=CLASS_TABLE,
                        error="the function public.class_label is a computed field",
                    )
                ],
            },
            {
                "schema": "public",
                "name": "echo_text",
                "overloads": [
                    overload(
                        308,
                        [argument("", builtin_reference("text"))],
                        builtin_reference("text"),
                    )
                ],
            },
            {
                "schema": "public",
                "name": "first_person",
                "overloads": [
                    overload(
                        311,
                        [],
                        reference(PEOPLE_ROW_TYPE, "people", "public"),
                        relation_id=PEOPLE,
                    )
                ],
            },
            {
                "schema": "public",
                "name": "keywords",
                "overloads": [
                    overload(
                        310,
                        [],
                        builtin_reference("record"),
                        set_returning=True,
                        columns=[
                            {**builtin_reference("text"), "name": "class"},
                            {
                                **builtin_reference("int8"),
                                "name": "table",
                                "is_nullable": False,
                            },
                            {**builtin_reference("text"), "name": "Weird Name"},
                        ],
                    )
                ],
            },
            {
                "schema": "public",
                "name": "pick",
                "overloads": [
                    overload(306, [], builtin_reference("record"), set_returning=True)
                ],
            },
            {
                "schema": "public",
                "name": "search",
                "overloads": [
                    overload(
                        312,
                        [
                            argument("arguments", builtin_reference("text")),
                            argument("from", builtin_reference("date"), default=True),
                            argument("ids", builtin_reference("_uuid"), default=True),
                            argument("limit", builtin_reference("int4"), default=True),
                            argument(
                                "read_only", builtin_reference("bool"), default=True
                            ),
                            argument("type", builtin_reference("text")),
                        ],
                        reference(PEOPLE_ROW_TYPE, "people", "public"),
                        relation_id=PEOPLE,
                        set_returning=True,
                    ),
                    overload(
                        313,
                        [
                            argument("payload", builtin_reference("bytea")),
                            argument("place", reference(ADDRESS, "address", "public")),
                            argument("status", reference(STATUS, "status", "public")),
                            argument("when", builtin_reference("timestamptz")),
                        ],
                        builtin_reference("jsonb"),
                    ),
                    overload(
                        314,
                        [
                            argument(
                                "document",
                                reference(DOCUMENTS_ROW_TYPE, "documents", "public"),
                                relation_id=DOCUMENTS,
                            )
                        ],
                        builtin_reference("void"),
                    ),
                ],
            },
            {
                "schema": "public",
                "name": "staticmethod",
                "overloads": [
                    overload(
                        303,
                        [argument("from", builtin_reference("int4"))],
                        builtin_reference("int4"),
                    )
                ],
            },
            {
                "schema": "public",
                "name": "touch",
                "overloads": [overload(304, [], builtin_reference("void"))],
            },
        ],
    }
