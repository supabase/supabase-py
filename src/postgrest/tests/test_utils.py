import pytest
from deprecation import fail_if_not_removed

from postgrest.utils import SyncClient, sanitize_param


@fail_if_not_removed
def test_sync_client() -> None:
    client = SyncClient()  # pyrefly: ignore[deprecated]
    # Verify that aclose method exists and calls close
    assert hasattr(client, "aclose")
    assert callable(client.aclose)  # pyrefly: ignore[deprecated]
    client.aclose()  # pyrefly: ignore[deprecated]


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
