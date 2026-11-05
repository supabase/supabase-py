import pytest
from supabase_utils.http.query import URLQuery
from yarl import URL


def test_empty_has_no_parameters() -> None:
    query = URLQuery.empty()
    assert len(query) == 0
    assert query.as_query() == {}
    assert query.get("anything") is None
    assert query.get_list("anything") is None


def test_from_mapping() -> None:
    query = URLQuery.from_mapping({"select": "*", "limit": 10})
    assert query.get_list("select") == ["*"]
    assert query.get_list("limit") == [10]
    assert "select" in query
    assert len(query) == 2


def test_keys_are_case_sensitive() -> None:
    query = URLQuery.from_mapping({"Key": "value"})
    assert "Key" in query
    assert "key" not in query


def test_set_appends_values() -> None:
    query = URLQuery.empty().set("id", "eq.1").set("id", 2)
    assert query.get_list("id") == ["eq.1", 2]
    assert query.get("id") == "eq.1&2"
    assert query["id"] == "eq.1&2"


def test_set_is_immutable() -> None:
    query = URLQuery.empty()
    query.set("a", "1")
    assert "a" not in query


def test_getitem_of_missing_key_raises() -> None:
    with pytest.raises(KeyError):
        URLQuery.empty()["missing"]


def test_merge_replaces_keys_from_other() -> None:
    base = URLQuery.empty().set("a", "1").set("a", "2").set("b", "3")
    merged = base.merge(URLQuery.from_mapping({"a": "4", "c": "5"}))
    assert merged.get_list("a") == ["4"]
    assert merged.get_list("b") == ["3"]
    assert merged.get_list("c") == ["5"]


def test_as_query_repeats_keys_in_url() -> None:
    query = URLQuery.empty().set("id", "gt.1").set("id", "lt.5").set("order", "id")
    url = URL("https://example.com/rest/v1/table").with_query(query.as_query())
    assert url.query.getall("id") == ["gt.1", "lt.5"]
    assert url.query.getall("order") == ["id"]


def test_as_query_encodes_values() -> None:
    query = URLQuery.from_mapping({"name": "a b&c", "count": 3, "ratio": 0.5})
    url = URL("https://example.com").with_query(query.as_query())
    assert url.query.getall("name") == ["a b&c"]
    assert url.query["count"] == "3"
    assert url.query["ratio"] == "0.5"


def test_repr() -> None:
    query = URLQuery.empty().set("a", "1").set("a", 2)
    assert repr(query) == 'URLQuery("a"="[\'1\', 2]")'
