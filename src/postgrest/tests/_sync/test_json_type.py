"""
Tests for flexible Json type annotation (Issue #1597)
=====================================================
Verifies that Json fields in Pydantic models correctly accept both:
1. Already-deserialized Python objects (dicts, lists, scalars returned by PostgREST).
2. Raw JSON strings (parsing them automatically).
"""

from typing import Any, Dict, List
import json
import pytest
from pydantic import BaseModel, ValidationError
from postgrest.types import Json


class SimpleJsonModel(BaseModel):
    id: int
    data: Json


class SubModel(BaseModel):
    name: str
    count: int


class TypedJsonModel(BaseModel):
    id: int
    data: Json[SubModel]


class DictJsonModel(BaseModel):
    id: int
    data: Json[Dict[str, int]]


def test_unsubscripted_json_with_dict():
    """Verify Json accepts already-deserialized dict (PostgREST response)."""
    input_data = {"id": 1, "data": {"foo": "bar", "num": 42}}
    model = SimpleJsonModel.model_validate(input_data)
    assert model.id == 1
    assert model.data == {"foo": "bar", "num": 42}


def test_unsubscripted_json_with_list():
    """Verify Json accepts already-deserialized list."""
    input_data = {"id": 2, "data": [1, 2, 3, 4]}
    model = SimpleJsonModel.model_validate(input_data)
    assert model.id == 2
    assert model.data == [1, 2, 3, 4]


def test_unsubscripted_json_with_json_string():
    """Verify Json parses raw JSON string into Python object."""
    json_str = json.dumps({"foo": "bar", "num": 42})
    input_data = {"id": 3, "data": json_str}
    model = SimpleJsonModel.model_validate(input_data)
    assert model.id == 3
    assert model.data == {"foo": "bar", "num": 42}


def test_subscripted_json_with_deserialized_dict():
    """Verify Json[SubModel] validates against deserialized dict."""
    input_data = {"id": 4, "data": {"name": "TestItem", "count": 100}}
    model = TypedJsonModel.model_validate(input_data)
    assert model.id == 4
    assert isinstance(model.data, SubModel)
    assert model.data.name == "TestItem"
    assert model.data.count == 100


def test_subscripted_json_with_json_string():
    """Verify Json[SubModel] parses JSON string and validates into SubModel."""
    json_str = json.dumps({"name": "TestItem", "count": 100})
    input_data = {"id": 5, "data": json_str}
    model = TypedJsonModel.model_validate(input_data)
    assert model.id == 5
    assert isinstance(model.data, SubModel)
    assert model.data.name == "TestItem"
    assert model.data.count == 100


def test_subscripted_json_with_typed_dict():
    """Verify Json[Dict[str, int]] validates against dict and json string."""
    dict_input = {"id": 6, "data": {"a": 1, "b": 2}}
    model1 = DictJsonModel.model_validate(dict_input)
    assert model1.data == {"a": 1, "b": 2}

    str_input = {"id": 7, "data": '{"a": 3, "b": 4}'}
    model2 = DictJsonModel.model_validate(str_input)
    assert model2.data == {"a": 3, "b": 4}


def test_invalid_json_validation_error():
    """Verify invalid structure or json string raises ValidationError."""
    with pytest.raises(ValidationError):
        TypedJsonModel.model_validate({"id": 8, "data": "invalid json { string"})

    with pytest.raises(ValidationError):
        TypedJsonModel.model_validate({"id": 9, "data": {"name": "TestOnly"}})  # missing count
