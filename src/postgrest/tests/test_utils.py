import json
from collections import UserDict, deque
from datetime import UTC, date, datetime, time, timedelta, timezone
from decimal import Decimal
from types import MappingProxyType
from uuid import UUID

import pytest
from deprecation import fail_if_not_removed

from postgrest.utils import (
    SyncClient,
    encode_json_body,
    is_row_list,
    sanitize_param,
)


@fail_if_not_removed
def test_sync_client() -> None:
    client = SyncClient()
    # Verify that aclose method exists and calls close
    assert hasattr(client, "aclose")
    assert callable(client.aclose)
    client.aclose()  # Should not raise any exception


@pytest.mark.parametrize(
    "value, expected",
    [
        ("param,name", '"param,name"'),
        ("param:name", '"param:name"'),
        ("param(name", '"param(name"'),
        ("param)name", '"param)name"'),
        ("table.column", "table.column"),
        ("table_column", "table_column"),
    ],
)
def test_sanitize_params(value, expected) -> None:
    assert sanitize_param(value) == expected


def test_encode_json_body_plain_json() -> None:
    body = {"name": "ü", "count": 1, "ratio": 0.5, "tags": ["a"], "none": None}

    assert encode_json_body(body) == (
        '{"name":"ü","count":1,"ratio":0.5,"tags":["a"],"none":null}'.encode()
    )


def test_encode_json_body_generated_types() -> None:
    body = {
        "id": UUID("6f1b6c1e-1d2f-4e8b-9a43-6b3c2f0a7d11"),
        "created_at": datetime(2024, 5, 1, 12, 30, tzinfo=UTC),
        "local": datetime(2024, 5, 1, 12, 30, 15, 500),
        "offset": datetime(2024, 5, 1, tzinfo=timezone(timedelta(hours=2))),
        "day": date(2024, 5, 1),
        "starts_at": time(9, 15),
        "payload": b"\x00\xffab",
        "nested": [{"at": date(2020, 1, 2)}],
    }

    assert json.loads(encode_json_body(body)) == {
        "id": "6f1b6c1e-1d2f-4e8b-9a43-6b3c2f0a7d11",
        "created_at": "2024-05-01T12:30:00+00:00",
        "local": "2024-05-01T12:30:15.000500",
        "offset": "2024-05-01T00:00:00+02:00",
        "day": "2024-05-01",
        "starts_at": "09:15:00",
        "payload": "\\x00ff6162",
        "nested": [{"at": "2020-01-02"}],
    }


@pytest.mark.parametrize("value", [Decimal("1.5"), {1, 2}, object()])
def test_encode_json_body_rejects_unsupported_types(value: object) -> None:
    with pytest.raises(TypeError, match="is not JSON serializable"):
        encode_json_body({"value": value})


def test_encode_json_body_rejects_nan() -> None:
    with pytest.raises(ValueError, match="Out of range float values"):
        encode_json_body({"value": float("nan")})


def test_encode_json_body_other_mappings_and_sequences() -> None:
    body = deque([MappingProxyType({"a": (1, 2)}), UserDict({"b": deque([3])})])

    assert json.loads(encode_json_body(body)) == [{"a": [1, 2]}, {"b": [3]}]


@pytest.mark.parametrize(
    "body, expected",
    [
        ([{"a": 1}], True),
        (({"a": 1},), True),
        (deque([{"a": 1}]), True),
        ({"a": 1}, False),
        ("abc", False),
        (b"abc", False),
        (None, False),
    ],
)
def test_is_row_list(body: object, expected: bool) -> None:
    assert is_row_list(body) is expected
