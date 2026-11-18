from __future__ import annotations

from dataclasses import dataclass, replace
from functools import cache
from types import GenericAlias, NoneType, UnionType
from typing import TYPE_CHECKING, Any, Union, get_args, get_origin, override

from pydantic import BaseModel

from .column_expression import Column, ComputedField
from .filter import Selectable
from .partial_row import _field_annotations, _without_constraints
from .relation import Embed, Relation, ToManyRelation, ToOneRelation
from .table import Table
from .utils import _quote

if TYPE_CHECKING:
    from pydantic.fields import FieldInfo


@cache
def _projection(
    table: Table[Any, Any, Any], model: type[BaseModel]
) -> tuple[Selectable[Any], ...]:
    """The entries of the `select` list that `model` is decoded from, one
    per field, checked against `table` once per table and model.

    Raises `TypeError` listing every field that does not fit the table.
    """
    problems: list[str] = []
    selected = _project(table, model, model.__name__, problems, (model,))
    if problems:
        listed = "\n".join(f"  - {problem}" for problem in problems)
        raise TypeError(
            f"{model.__name__} does not match the {table.name} table:\n{listed}"
        )
    return selected


def _project(
    table: Table[Any, Any, Any],
    model: type[BaseModel],
    path: str,
    problems: list[str],
    enclosing: tuple[type[BaseModel], ...],
) -> tuple[Selectable[Any], ...]:
    if not model.model_fields:
        problems.append(f"{path} has no fields to select")
        return ()
    members = _Members.of(table)
    selected: list[Selectable[Any]] = []
    for name, field in model.model_fields.items():
        entry = _field_entry(
            members, name, field, f"{path}.{name}", problems, enclosing
        )
        if entry is not None:
            selected.append(entry)
    return tuple(selected)


def _field_entry(
    members: _Members,
    name: str,
    field: FieldInfo,
    path: str,
    problems: list[str],
    enclosing: tuple[type[BaseModel], ...],
) -> Selectable[Any] | None:
    """The entry of the `select` list that the field `name` is decoded
    from, coming back under the key the model reads it from, or `None`
    after adding to `problems` what does not fit the table."""
    match field.validation_alias:
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
            return _keyed(Column[Any, Any](candidate), key)
        if candidate in members.computed_fields:
            computed_field = members.computed_fields[candidate]
            if computed_field.value_type is not None:
                column = f"{members.table}.{candidate}"
                value_type = computed_field.value_type | None
                problems.extend(_type_problems(path, annotation, column, value_type))
            return _keyed(computed_field, key)
        if candidate in members.relations:
            relation = members.relations[candidate]
            return _embed(
                relation,
                f"{members.table}.{candidate}",
                key,
                annotation,
                path,
                problems,
                enclosing,
            )
    problems.append(
        f"{path} matches no column, computed field or relation of {members.table}"
    )
    return None


def _embed(
    relation: Relation[Any, Any],
    relation_name: str,
    key: str,
    annotation: Any,
    path: str,
    problems: list[str],
    enclosing: tuple[type[BaseModel], ...],
) -> Selectable[Any] | None:
    """The embed of `relation` that a nested model, or a list of them,
    is decoded from."""
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
    columns = _project(target, nested, path, problems, (*enclosing, nested))
    if relation.response_key != key:
        relation = replace(relation, alias=key)
    return Embed(relation, columns)


def _target_table(relation: Relation[Any, Any]) -> Table[Any, Any, Any]:
    if relation.target_table is not None:
        return relation.target_table()
    return Table(relation.name, relation.target_type)


def _keyed(
    entry: Column[Any, Any] | ComputedField[Any, Any], key: str
) -> Selectable[Any]:
    """`entry`, renamed in the `select` list when the model reads it from
    another key than its name."""
    return entry if entry.response_key == key else _Renamed(entry, key)


@dataclass(frozen=True)
class _Renamed(Selectable[Any]):
    """A column or a computed field that comes back under `key`, sent as
    `"key":name`."""

    entry: Column[Any, Any] | ComputedField[Any, Any]
    key: str

    @property
    @override
    def response_key(self) -> str:
        return self.key

    @property
    @override
    def _selected_as(self) -> str:
        return f"{_quote(self.key)}:{self.entry._selected_as}"


@dataclass(frozen=True)
class _Members:
    """What a field of a projection can name on a table, by the key it is
    named by."""

    table: str
    columns: dict[str, Any]
    computed_fields: dict[str, ComputedField[Any, Any]]
    relations: dict[str, Relation[Any, Any]]

    @classmethod
    def of(cls, table: Table[Any, Any, Any]) -> _Members:
        """The stored columns of `table` by name, with the type the row type
        declares for them, its computed fields by name, and its relations by
        the attribute they are declared as and by their response key."""
        relations: dict[str, Relation[Any, Any]] = {}
        for relation in table.relations:
            relations.setdefault(relation.response_key, relation)
            if relation._attribute is not None:
                relations[relation._attribute] = relation
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

    The types have to be the same, apart from the constraints of a `Field`.
    A field may be nullable when the column is not, but not the other way
    around. `Any` on either side matches anything.
    """
    field_members, field_nullable = _union_members(annotation)
    column_members, column_nullable = _union_members(column_type)
    if Any in field_members or Any in column_members:
        return []
    problems: list[str] = []
    if field_members != column_members:
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
