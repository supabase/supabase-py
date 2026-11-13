from types import MappingProxyType

from postgrest.request_builder import _unique_columns


def test_unique_columns_reads_keys_from_every_mapping_row() -> None:
    columns = _unique_columns([{"a": 1}, MappingProxyType({"b": 2}), "not a row"])
    assert columns == '"a","b"'


def test_unique_columns_keeps_first_seen_order() -> None:
    columns = _unique_columns(
        [{"zeta": 1, "alpha": 2}, {"mu": 3, "zeta": 4}, {"beta": 5, "alpha": 6}]
    )
    assert columns == '"zeta","alpha","mu","beta"'
