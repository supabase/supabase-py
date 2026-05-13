from pydantic import TypeAdapter
from pydantic.types import JsonValue

from postgrest.types import JSONAdapter


def test_json_adapter_schema_matches_pydantic_json_value():
    assert JSONAdapter.core_schema == TypeAdapter(JsonValue).core_schema


def test_json_adapter_validates_nested_json_bytes():
    payload = (
        b'{"items":[{"id":1,"tags":["a","b"],'
        b'"meta":{"score":0.9,"active":true,"note":null}}]}'
    )

    assert JSONAdapter.validate_json(payload) == {
        "items": [
            {
                "id": 1,
                "tags": ["a", "b"],
                "meta": {"score": 0.9, "active": True, "note": None},
            }
        ]
    }
