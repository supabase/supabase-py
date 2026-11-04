from types import MappingProxyType

from postgrest.request_builder import _unique_columns


def test_unique_columns_reads_keys_from_every_mapping_row() -> None:
    columns = _unique_columns([{"a": 1}, MappingProxyType({"b": 2}), "not a row"])
    assert set(columns.split(",")) == {'"a"', '"b"'}
