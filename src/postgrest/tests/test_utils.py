import pytest
from deprecation import fail_if_not_removed

from postgrest.utils import SyncClient, sanitize_param


@fail_if_not_removed
def test_sync_client():
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
        ("param,name", '"param,name"'),
        ("table.column", "table.column"),
        ("table_column", "table_column"),
    ],
)
def test_sanitize_params(value, expected):
    assert sanitize_param(value) == expected
