from postgrest.types import JSONAdapter


def test_json_adapter_uses_pydantic_json_value_schema():
    assert JSONAdapter.core_schema["schema"]["schema_ref"].startswith(
        "pydantic.types.JsonValue:"
    )


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
