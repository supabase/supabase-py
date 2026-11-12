import platform
import re

import pytest
from supabase_utils.http.headers import Headers


def test_empty_has_no_headers() -> None:
    headers = Headers.empty()
    assert len(headers) == 0
    assert list(headers) == []
    assert headers.get("anything") is None


def test_from_mapping_lowercases_keys() -> None:
    headers = Headers.from_mapping({"Content-Type": "application/json"})
    assert list(headers.keys()) == ["content-type"]
    assert headers.get("CONTENT-TYPE") == "application/json"
    assert "Content-Type" in headers
    assert "content-type" in headers


def test_set_appends_values() -> None:
    headers = Headers.empty().set("Accept", "text/plain").set("accept", "text/html")
    assert headers.get("Accept") == "text/plain, text/html"
    assert headers.get_list("ACCEPT") == ["text/plain", "text/html"]
    assert headers.iter_items() == [("accept", "text/plain"), ("accept", "text/html")]


def test_override_replaces_values() -> None:
    headers = Headers.empty().set("Accept", "text/plain").set("Accept", "text/html")
    overridden = headers.override("ACCEPT", "application/json")
    assert overridden.get_list("accept") == ["application/json"]


def test_remove_drops_every_value() -> None:
    headers = Headers.empty().set("Accept", "text/plain").set("Accept", "text/html")
    assert "accept" not in headers.remove("ACCEPT")
    assert headers.remove("missing").get_list("accept") == ["text/plain", "text/html"]


def test_headers_are_immutable() -> None:
    original = Headers.from_mapping({"a": "1"})
    original.set("a", "2")
    original.override("a", "3")
    original.remove("a")
    original.update(Headers.from_mapping({"b": "4"}))
    assert original.get_list("a") == ["1"]
    assert "b" not in original


def test_update_replaces_keys_from_other() -> None:
    base = Headers.empty().set("a", "1").set("a", "2").set("b", "3")
    other = Headers.from_mapping({"A": "4", "c": "5"})
    merged = base.update(other)
    assert merged.get_list("a") == ["4"]
    assert merged.get("b") == "3"
    assert merged.get("c") == "5"
    assert len(merged) == 3


def test_getitem() -> None:
    headers = Headers.from_mapping({"Authorization": "Bearer token"})
    assert headers["authorization"] == "Bearer token"
    with pytest.raises(KeyError):
        headers["missing"]


def test_get_list_of_missing_key_is_none() -> None:
    assert Headers.empty().get_list("missing") is None


def test_dict_conversion_joins_values() -> None:
    headers = Headers.empty().set("a", "1").set("a", "2").set("b", "3")
    assert dict(headers) == {"a": "1, 2", "b": "3"}


def test_str_and_repr() -> None:
    headers = Headers.empty().set("a", "1").set("a", "2")
    assert str(headers) == 'Headers("a"="1, 2")'
    assert repr(headers) == str(headers)


def test_supabase_client_headers() -> None:
    headers = Headers.supabase_client_headers("supabase_test", "1.2.3")
    x_client_info = headers["X-Client-Info"]
    assert re.fullmatch(
        r"supabase-py/supabase_test v1\.2\.3; platform=.*; platform-version=.*;"
        r" runtime=python; runtime-version=\S+",
        x_client_info,
    )
    assert f"runtime-version={platform.python_version()}" in x_client_info
    assert len(headers) == 1


def test_supabase_client_headers_list_the_features_last() -> None:
    headers = Headers.supabase_client_headers(
        "supabase_test", "1.2.3", features=["typed-api", "b", "typed-api"]
    )
    assert headers["X-Client-Info"].endswith(
        f"; runtime-version={platform.python_version()}; features=b,typed-api"
    )


def test_with_client_info_features_appends_a_features_segment() -> None:
    headers = Headers.from_mapping(
        {"X-Client-Info": "supabase-py/3.0.0; runtime=python"}
    )
    featured = headers.with_client_info_features(["typed-api"])
    assert featured["X-Client-Info"] == (
        "supabase-py/3.0.0; runtime=python; features=typed-api"
    )
    assert headers["X-Client-Info"] == "supabase-py/3.0.0; runtime=python"


def test_with_client_info_features_merges_with_the_features_listed() -> None:
    headers = Headers.from_mapping(
        {"x-client-info": "client/1.0; Features=b, a,; runtime=python"}
    )
    featured = headers.with_client_info_features(["typed-api", "a"])
    assert (
        featured["X-Client-Info"]
        == "client/1.0; runtime=python; features=a,b,typed-api"
    )


def test_with_client_info_features_leaves_other_headers_alone() -> None:
    headers = Headers.from_mapping({"X-Client-Info": "client/1.0", "apikey": "key"})
    featured = headers.with_client_info_features(["typed-api"])
    assert featured["apikey"] == "key"
    assert len(featured) == 2


def test_with_client_info_features_changes_nothing_without_the_header() -> None:
    headers = Headers.from_mapping({"apikey": "key"})
    assert headers.with_client_info_features(["typed-api"]) is headers


def test_with_client_info_features_changes_nothing_without_features() -> None:
    headers = Headers.from_mapping({"X-Client-Info": "client/1.0"})
    assert headers.with_client_info_features([]) is headers
