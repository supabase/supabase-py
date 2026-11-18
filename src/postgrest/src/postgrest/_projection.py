from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from functools import cache
from types import GenericAlias, NoneType, UnionType
from typing import TYPE_CHECKING, Any, Union, get_args, get_origin

from pydantic import BaseModel

from .column_expression import Column, ComputedField
from .filter import Selectable
from .partial_row import _field_annotations, _without_constraints
from .relation import Embed, Relation, ToManyRelation, ToOneRelation
from .table import Table

if TYPE_CHECKING:
    from pydantic.fields import FieldInfo
    from supabase_utils.types import JSON


@dataclass(frozen=True)
class _Field:
    """A field of a projection: the key its value comes back under, the key
    the model reads it from, and the projection of a nested model."""

    response_key: str
    model_key: str
    nested: _Projection | None = None


@dataclass(frozen=True)
class _Projection:
    """The entries of the `select` list a model is decoded from, and how a
    response row is keyed for the model to read it."""

    columns: tuple[Selectable[Any], ...]
    fields: tuple[_Field, ...]

    def keyed(self, row: Mapping[str, JSON]) -> dict[str, JSON]:
        """`row` keyed by the keys the model reads, with the rows embedded
        in it keyed for their nested models. A key the response leaves out,
        as `strip_nulls()` does, stays out."""
        keyed: dict[str, JSON] = {}
        for field in self.fields:
            if field.response_key not in row:
                continue
            value = row[field.response_key]
            if field.nested is not None:
                value = field.nested._keyed_embed(value)
            keyed[field.model_key] = value
        return keyed

    def _keyed_embed(self, value: JSON) -> JSON:
        match value:
            case Mapping():
                return self.keyed(value)
            case list():
                return [
                    self.keyed(row) if isinstance(row, Mapping) else row
                    for row in value
                ]
            case _:
                return value


@cache
def _projection(table: Table[Any, Any, Any], model: type[BaseModel]) -> _Projection:
    """The projection of `model` on `table`, one entry of the `select` list
    per field, checked against `table` once per table and model.

    Raises `TypeError` listing every field that does not fit the table.
    """
    problems: list[str] = []
    projection = _project(table, model, model.__name__, problems, (model,))
    if problems:
        listed = "\n".join(f"  - {problem}" for problem in problems)
        raise TypeError(
            f"{model.__name__} does not match the {table.name} table:\n{listed}"
        )
    return projection


def _project(
    table: Table[Any, Any, Any],
    model: type[BaseModel],
    path: str,
    problems: list[str],
    enclosing: tuple[type[BaseModel], ...],
) -> _Projection:
    if not model.model_fields:
        problems.append(f"{path} has no fields to select")
    members = _Members.of(table)
    by_alias = model.model_config.get("validate_by_alias", True)
    columns: dict[str, Selectable[Any]] = {}
    fields: list[_Field] = []
    for name, field in model.model_fields.items():
        mapped = _field_entry(
            members, name, field, by_alias, f"{path}.{name}", problems, enclosing
        )
        if mapped is None:
            continue
        entry, mapped_field = mapped
        known = columns.get(entry.response_key)
        if known is not None and (isinstance(entry, Embed) or isinstance(known, Embed)):
            problems.append(
                f"{path}.{name} reads {entry.response_key}, which another field "
                "reads as well; read it through one field"
            )
            continue
        if any(
            other.model_key == mapped_field.model_key
            and other.response_key != mapped_field.response_key
            for other in fields
        ):
            problems.append(
                f"{path}.{name} is read from {mapped_field.model_key}, as "
                "another field reading a different column is"
            )
            continue
        columns.setdefault(entry.response_key, entry)
        fields.append(mapped_field)
    return _Projection(tuple(columns.values()), tuple(fields))


def _field_entry(
    members: _Members,
    name: str,
    field: FieldInfo,
    by_alias: bool,
    path: str,
    problems: list[str],
    enclosing: tuple[type[BaseModel], ...],
) -> tuple[Selectable[Any], _Field] | None:
    """The entry of the `select` list that the field `name` is decoded
    from, with the keys it moves between, or `None` after adding to
    `problems` what does not fit the table."""
    match field.validation_alias:
        case _ if not by_alias:
            key = name
        case str(alias):
            key = alias
        case None:
            key = field.alias or name
        case _:
            problems.append(
                f"{path} is read through an AliasPath or AliasChoices, which "
                "select_as() cannot select"
            )
            return None
    annotation: Any = Any if field.annotation is None else field.annotation
    for candidate in dict.fromkeys((key, name)):
        if candidate in members.columns:
            column_type = members.columns[candidate]
            column = f"{members.table}.{candidate}"
            problems.extend(_type_problems(path, annotation, column, column_type))
            return Column[Any, Any](candidate), _Field(candidate, key)
        if candidate in members.computed_fields:
            computed_field = members.computed_fields[candidate]
            if computed_field.value_type is not None:
                column = f"{members.table}.{candidate}"
                value_type = computed_field.value_type | None
                problems.extend(_type_problems(path, annotation, column, value_type))
            return computed_field, _Field(candidate, key)
        if candidate in members.relations:
            relations = members.relations[candidate]
            relation_name = f"{members.table}.{candidate}"
            if len(relations) > 1:
                problems.append(
                    f"{path} could embed any of {len(relations)} relations that "
                    f"come back as {candidate}; name the field after the "
                    "attribute of one of them"
                )
                return None
            (relation,) = relations
            embed = _embed(
                relation, relation_name, annotation, path, problems, enclosing
            )
            if embed is None:
                return None
            entry, nested = embed
            return entry, _Field(relation.response_key, key, nested)
    problems.append(
        f"{path} matches no column, computed field or relation of {members.table}"
    )
    return None


def _embed(
    relation: Relation[Any, Any],
    relation_name: str,
    annotation: Any,
    path: str,
    problems: list[str],
    enclosing: tuple[type[BaseModel], ...],
) -> tuple[Embed[Any, Any], _Projection] | None:
    """The embed of `relation` that a nested model, or a list of them,
    is decoded from, with the projection of the nested model."""
    members, _ = _union_members(annotation)
    shape = "a list of rows" if isinstance(relation, ToManyRelation) else "a row"
    if len(members) != 1:
        problems.append(
            f"{path} is {_type_name(annotation)}, but {relation_name} "
            f"embeds {shape}; declare it as a model"
        )
        return None
    (member,) = members
    is_list = get_origin(member) is list
    nested = get_args(member)[0] if is_list and get_args(member) else member
    if not (isinstance(nested, type) and issubclass(nested, BaseModel)):
        problems.append(
            f"{path} is {_type_name(annotation)}, but {relation_name} "
            f"embeds {shape}; declare it as a model"
        )
        return None
    if isinstance(relation, ToManyRelation) and not is_list:
        problems.append(
            f"{path} is one {nested.__name__}, but {relation_name} is a "
            f"to-many relation; declare it as list[{nested.__name__}]"
        )
        return None
    if isinstance(relation, ToOneRelation) and is_list:
        problems.append(
            f"{path} is a list, but {relation_name} is a to-one "
            f"relation; declare it as {nested.__name__} or "
            f"{nested.__name__} | None"
        )
        return None
    if nested in enclosing:
        problems.append(
            f"{path} embeds {nested.__name__} inside itself, which has no end"
        )
        return None
    target = _target_table(relation)
    projection = _project(target, nested, path, problems, (*enclosing, nested))
    return Embed(relation, projection.columns), projection


def _target_table(relation: Relation[Any, Any]) -> Table[Any, Any, Any]:
    if relation.target_table is not None:
        return relation.target_table()
    return Table(relation.name, relation.target_type)


@dataclass(frozen=True)
class _Members:
    """What a field of a projection can name on a table, by the key it is
    named by."""

    table: str
    columns: dict[str, Any]
    computed_fields: dict[str, ComputedField[Any, Any]]
    relations: dict[str, list[Relation[Any, Any]]]

    @classmethod
    def of(cls, table: Table[Any, Any, Any]) -> _Members:
        """The stored columns of `table` by name, with the type the row type
        declares for them, its computed fields by name, and its relations by
        the attribute they are declared as and by their response key."""
        relations: dict[str, list[Relation[Any, Any]]] = {}
        for relation in table.relations:
            relations.setdefault(relation.response_key, []).append(relation)
        for relation in table.relations:
            if relation._attribute is not None:
                relations[relation._attribute] = [relation]
        return cls(
            table=table.name,
            columns=dict(_field_annotations(table.row_type)),
            computed_fields={field.name: field for field in table.computed_fields},
            relations=relations,
        )


def _type_problems(
    path: str, annotation: Any, column: str, column_type: Any
) -> list[str]:
    """The ways the type `annotation` of a field cannot hold the values of
    `column`, whose row type declares `column_type`.

    The types have to be the same, apart from the constraints of a `Field`
    and an `Any` on either side, at any depth, which matches anything. A
    field may be nullable when the column is not, but not the other way
    around.
    """
    field_members, field_nullable = _union_members(annotation)
    column_members, column_nullable = _union_members(column_type)
    problems: list[str] = []
    if not _same_members(field_members, column_members):
        problems.append(
            f"{path} is {_type_name(annotation)}, but {column} is "
            f"{_type_name(_without_constraints(column_type))}"
        )
    elif column_nullable and not field_nullable:
        problems.append(
            f"{path} is {_type_name(annotation)}, but {column} can be NULL; "
            f"declare it as {_type_name(annotation)} | None"
        )
    return problems


def _same_members(left: frozenset[Any], right: frozenset[Any]) -> bool:
    """Whether every member of each union matches a member of the other."""
    if Any in left or Any in right:
        return True
    return all(any(_same(one, other) for other in right) for one in left) and all(
        any(_same(one, other) for one in left) for other in right
    )


def _same(left: Any, right: Any) -> bool:
    """Whether `left` and `right` are the same type, see `_type_problems`."""
    left, right = _without_constraints(left), _without_constraints(right)
    if left is Any or right is Any or left == right:
        return True
    origin: object = get_origin(left)
    if origin is None or origin != get_origin(right):
        return False
    if origin is Union or origin is UnionType:
        left_members, left_nullable = _union_members(left)
        right_members, right_nullable = _union_members(right)
        return left_nullable == right_nullable and _same_members(
            left_members, right_members
        )
    left_arguments, right_arguments = get_args(left), get_args(right)
    return len(left_arguments) == len(right_arguments) and all(
        map(_same, left_arguments, right_arguments)
    )


def _union_members(annotation: Any) -> tuple[frozenset[Any], bool]:
    """The types other than `None` that `annotation` is a union of, without
    the constraints of a `Field`, and whether `None` is one of them."""
    stripped = _without_constraints(annotation)
    origin: object = get_origin(stripped)
    members = (
        get_args(stripped) if origin is Union or origin is UnionType else (stripped,)
    )
    return frozenset(member for member in members if member is not NoneType), (
        NoneType in members
    )


def _type_name(annotation: Any) -> str:
    if isinstance(annotation, type) and not isinstance(annotation, GenericAlias):
        return annotation.__name__
    return repr(annotation).replace("typing.", "")
