import pytest

from postgrest.utils import sanitize_param


@pytest.mark.parametrize(
    "value, expected",
    [
        ("param,name", '"param,name"'),
        ("param:name", '"param:name"'),
        ("param(name", '"param(name"'),
        ("param)name", '"param)name"'),
        ("param,name", '"param,name"'),
        ("table.column", "table.column"),
        ("table_column", "table_column"),
    ],
)
def test_sanitize_params(value: str, expected: str) -> None:
    assert sanitize_param(value) == expected
