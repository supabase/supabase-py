import pytest
from httpx import Client, Headers, QueryParams

from postgrest import SyncFilterRequestBuilder


@pytest.fixture
def filter_request_builder():
    with Client() as client:
        yield SyncFilterRequestBuilder(
            client, "/example_table", "GET", Headers(), QueryParams(), {}
        )


def test_constructor(filter_request_builder: SyncFilterRequestBuilder):
    builder = filter_request_builder

    assert builder.path == "/example_table"
    assert len(builder.headers) == 0
    assert len(builder.params) == 0
    assert builder.http_method == "GET"
    assert builder.json is None
    assert not builder.negate_next


def test_not_(filter_request_builder):
    builder = filter_request_builder.not_

    assert builder.negate_next


def test_filter(filter_request_builder):
    builder = filter_request_builder.filter(":col.name", "eq", "val")

    assert builder.params['":col.name"'] == "eq.val"


@pytest.mark.parametrize(
    "col_name, expected_query_prefix",
    [
        ("col:name", "%22col%3Aname%22"),
        ("col.name", "col.name"),
    ],
)
def test_filter_special_characters(
    filter_request_builder, col_name, expected_query_prefix
):
    builder = filter_request_builder.filter(col_name, "eq", "val")

    assert str(builder.params) == f"{expected_query_prefix}=eq.val"


def test_multivalued_param(filter_request_builder):
    builder = filter_request_builder.lte("x", "a").gte("x", "b")

    assert str(builder.params) == "x=lte.a&x=gte.b"


def test_match(filter_request_builder):
    builder = filter_request_builder.match({"id": "1", "done": "false"})
    assert str(builder.params) == "id=eq.1&done=eq.false"


def test_equals(filter_request_builder):
    builder = filter_request_builder.eq("x", "a")

    assert str(builder.params) == "x=eq.a"


def test_not_equal(filter_request_builder):
    builder = filter_request_builder.neq("x", "a")

    assert str(builder.params) == "x=neq.a"


def test_greater_than(filter_request_builder):
    builder = filter_request_builder.gt("x", "a")

    assert str(builder.params) == "x=gt.a"


def test_greater_than_or_equals_to(filter_request_builder):
    builder = filter_request_builder.gte("x", "a")

    assert str(builder.params) == "x=gte.a"


def test_contains(filter_request_builder):
    builder = filter_request_builder.contains("x", "a")

    assert str(builder.params) == "x=cs.a"


def test_contains_dictionary(filter_request_builder):
    builder = filter_request_builder.contains("x", {"a": "b"})

    # {"a":"b"}
    assert str(builder.params) == "x=cs.%7B%22a%22%3A+%22b%22%7D"


def test_contains_any_item(filter_request_builder):
    builder = filter_request_builder.contains("x", ["a", "b"])

    # {a,b}
    assert str(builder.params) == "x=cs.%7Ba%2Cb%7D"


def test_contains_in_list(filter_request_builder):
    builder = filter_request_builder.contains("x", '[{"a": "b"}]')

    # [{"a":+"b"}] (the + represents the space)
    assert str(builder.params) == "x=cs.%5B%7B%22a%22%3A+%22b%22%7D%5D"


def test_contained_by_mixed_items(filter_request_builder):
    builder = filter_request_builder.contained_by("x", ["a", '["b", "c"]'])

    # {a,["b",+"c"]}
    assert str(builder.params) == "x=cd.%7Ba%2C%5B%22b%22%2C+%22c%22%5D%7D"


def test_range_greater_than(filter_request_builder):
    builder = filter_request_builder.range_gt(
        "x", ["2000-01-02 08:30", "2000-01-02 09:30"]
    )

    # {a,["b",+"c"]}
    assert str(builder.params) == "x=sr.%282000-01-02+08%3A30%2C2000-01-02+09%3A30%29"


def test_range_greater_than_or_equal_to(filter_request_builder):
    builder = filter_request_builder.range_gte(
        "x", ["2000-01-02 08:30", "2000-01-02 09:30"]
    )

    # {a,["b",+"c"]}
    assert str(builder.params) == "x=nxl.%282000-01-02+08%3A30%2C2000-01-02+09%3A30%29"


def test_range_less_than(filter_request_builder):
    builder = filter_request_builder.range_lt(
        "x", ["2000-01-02 08:30", "2000-01-02 09:30"]
    )

    # {a,["b",+"c"]}
    assert str(builder.params) == "x=sl.%282000-01-02+08%3A30%2C2000-01-02+09%3A30%29"


def test_range_less_than_or_equal_to(filter_request_builder):
    builder = filter_request_builder.range_lte(
        "x", ["2000-01-02 08:30", "2000-01-02 09:30"]
    )

    # {a,["b",+"c"]}
    assert str(builder.params) == "x=nxr.%282000-01-02+08%3A30%2C2000-01-02+09%3A30%29"


def test_range_adjacent(filter_request_builder):
    builder = filter_request_builder.range_adjacent(
        "x", ["2000-01-02 08:30", "2000-01-02 09:30"]
    )

    # {a,["b",+"c"]}
    assert str(builder.params) == "x=adj.%282000-01-02+08%3A30%2C2000-01-02+09%3A30%29"


def test_overlaps(filter_request_builder):
    builder = filter_request_builder.overlaps("x", ["is:closed", "severity:high"])

    # {a,["b",+"c"]}
    assert str(builder.params) == "x=ov.%7Bis%3Aclosed%2Cseverity%3Ahigh%7D"


def test_overlaps_with_timestamp_range(filter_request_builder):
    builder = filter_request_builder.overlaps(
        "x", "[2000-01-01 12:45, 2000-01-01 13:15)"
    )

    # {a,["b",+"c"]}
    assert str(builder.params) == "x=ov.%5B2000-01-01+12%3A45%2C+2000-01-01+13%3A15%29"


def test_like(filter_request_builder):
    builder = filter_request_builder.like("x", "%a%")

    assert str(builder.params) == "x=like.%25a%25"


def test_ilike(filter_request_builder):
    builder = filter_request_builder.ilike("x", "%a%")

    assert str(builder.params) == "x=ilike.%25a%25"


def test_like_all_of(filter_request_builder):
    builder = filter_request_builder.like_all_of("x", "A*,*b")

    assert str(builder.params) == "x=like%28all%29.%7BA%2A%2C%2Ab%7D"


def test_like_any_of(filter_request_builder):
    builder = filter_request_builder.like_any_of("x", "a*,*b")

    assert str(builder.params) == "x=like%28any%29.%7Ba%2A%2C%2Ab%7D"


def test_ilike_all_of(filter_request_builder):
    builder = filter_request_builder.ilike_all_of("x", "A*,*b")

    assert str(builder.params) == "x=ilike%28all%29.%7BA%2A%2C%2Ab%7D"


def test_ilike_any_of(filter_request_builder):
    builder = filter_request_builder.ilike_any_of("x", "A*,*b")

    assert str(builder.params) == "x=ilike%28any%29.%7BA%2A%2C%2Ab%7D"


def test_is_(filter_request_builder):
    builder = filter_request_builder.is_("x", "a")

    assert str(builder.params) == "x=is.a"


def test_in_(filter_request_builder):
    builder = filter_request_builder.in_("x", ["a", "b"])

    assert str(builder.params) == "x=in.%28a%2Cb%29"


def test_or_(filter_request_builder):
    builder = filter_request_builder.or_("x.eq.1")

    assert str(builder.params) == "or=%28x.eq.1%29"


def test_or_in_contain(filter_request_builder):
    builder = filter_request_builder.or_("id.in.(5,6,7), arraycol.cs.{'a','b'}")

    assert (
        str(builder.params)
        == "or=%28id.in.%285%2C6%2C7%29%2C+arraycol.cs.%7B%27a%27%2C%27b%27%7D%29"
    )
