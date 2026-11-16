from dataclasses import FrozenInstanceError
from datetime import datetime

import pytest

from postgrest import Column, ColumnExpression, ComputedField, NullableColumn


class TodoRow:
    pass


class Todos:
    id = Column[TodoRow, int]("id")
    due = NullableColumn[TodoRow, datetime]("due")
    full_name = ComputedField[TodoRow, str]("full_name")


def test_a_column_renders_its_name_as_the_expression() -> None:
    assert Todos.id.name == "id"
    assert Todos.id.expression == "id"
    assert Todos.due.expression == "due"
    assert Todos.full_name.name == "full_name"
    assert Todos.full_name.expression == "full_name"


def test_a_column_is_a_value() -> None:
    assert Todos.id == Column("id")
    assert Todos.id == Column[TodoRow, int]("id")
    assert Todos.id != Column("other")
    assert Column("id") != NullableColumn("id")
    assert Column("id") != ComputedField("id")
    assert hash(Todos.id) == hash(Column("id"))
    assert {Todos.id: "selected"}[Column("id")] == "selected"


def test_a_column_is_frozen() -> None:
    with pytest.raises(FrozenInstanceError):
        Todos.id.name = "other"  # pyrefly: ignore[read-only]


def test_a_column_has_a_readable_repr() -> None:
    assert repr(Todos.id) == "Column(name='id')"
    assert repr(Todos.due) == "NullableColumn(name='due')"
    assert repr(Todos.full_name) == "ComputedField(name='full_name', value_type=None)"


def test_a_nullable_column_is_not_a_column() -> None:
    assert not isinstance(Todos.due, Column)
    assert isinstance(Todos.due, ColumnExpression)
    assert not isinstance(Todos.id, NullableColumn)


def test_a_computed_field_is_not_a_column() -> None:
    assert not isinstance(Todos.full_name, Column)
    assert isinstance(Todos.full_name, ColumnExpression)


def test_only_a_nullable_column_and_a_computed_field_test_for_null() -> None:
    assert not hasattr(Todos.id, "is_null")
    assert Todos.due.is_null().comparison is not None
    assert Todos.full_name.is_null().comparison is not None


def test_an_ad_hoc_column_needs_no_type_arguments() -> None:
    assert Column("deleted_at") == Column("deleted_at")
    assert NullableColumn("deleted_at").is_null().comparison is not None


def test_a_column_expression_cannot_be_instantiated() -> None:
    with pytest.raises(TypeError):
        ColumnExpression()  # pyrefly: ignore[bad-instantiation]
