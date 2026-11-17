from datetime import UTC, date, datetime
from typing import Annotated, NotRequired, TypedDict
from uuid import UUID, uuid4

import pytest
from pydantic import Field
from supabase_utils.http.request import Response

from postgrest import CountMethod, SyncPostgrestClient
from postgrest.exceptions import APIError


def test_multivalued_param_httpx(postgrest_client: SyncPostgrestClient) -> None:
    res = (
        postgrest_client.from_("countries")
        .select("country_name, iso", count=CountMethod.exact)
        .lte("numcode", 8)
        .gte("numcode", 4)
        .execute()
    )

    assert res.count == 2
    assert res.data == [
        {"country_name": "AFGHANISTAN", "iso": "AF"},
        {"country_name": "ALBANIA", "iso": "AL"},
    ]


def test_multivalued_param(postgrest_client: SyncPostgrestClient) -> None:
    res = (
        postgrest_client.from_("countries")
        .select("country_name, iso", count=CountMethod.exact)
        .lte("numcode", 8)
        .gte("numcode", 4)
        .execute()
    )

    assert res.count == 2
    assert res.data == [
        {"country_name": "AFGHANISTAN", "iso": "AF"},
        {"country_name": "ALBANIA", "iso": "AL"},
    ]


def test_match(postgrest_client: SyncPostgrestClient) -> None:
    res = (
        postgrest_client.from_("countries")
        .select("country_name, iso")
        .match({"numcode": 8, "nicename": "Albania"})
        .single()
        .execute()
    )

    assert res.data == {"country_name": "ALBANIA", "iso": "AL"}


def test_match_maybe_single(postgrest_client: SyncPostgrestClient) -> None:
    res = (
        postgrest_client.from_("countries")
        .select("country_name, iso")
        .match({"numcode": 8, "nicename": "Albania"})
        .maybe_single()
        .execute()
    )
    assert res
    assert res.data == {"country_name": "ALBANIA", "iso": "AL"}


def test_no_match_maybe_single(postgrest_client: SyncPostgrestClient) -> None:
    res = (
        postgrest_client.from_("countries")
        .select("country_name, iso")
        .match({"numcode": 100, "nicename": "Wonderland"})
        .maybe_single()
        .execute()
    )

    assert res is None


def test_maybe_single_multiple_rows(
    postgrest_client: SyncPostgrestClient,
) -> None:
    with pytest.raises(APIError) as exc_info:
        (
            postgrest_client.from_("countries")
            .select("country_name, iso")
            .lte("numcode", 8)
            .gte("numcode", 4)
            .maybe_single()
            .execute()
        )

    assert exc_info.value.code == "406"
    assert exc_info.value.message == "Cannot coerce the result to a single JSON object"
    assert exc_info.value.details == "The result contains more than one row."


def test_head_query_error(postgrest_client: SyncPostgrestClient) -> None:
    with pytest.raises(APIError) as exc_info:
        (
            postgrest_client.from_("countries")
            .select("*", count=CountMethod.exact, head=True)
            .eq("ref.othercol", 123)
            .execute()
        )

    error = exc_info.value
    assert error.code == "PGRST108"
    assert error.message == "Bad Request"
    assert error.hint is None
    assert error.details is None
    assert error.status_code == 400


def test_equals(postgrest_client: SyncPostgrestClient) -> None:
    res = (
        postgrest_client.from_("countries")
        .select("country_name, iso")
        .eq("nicename", "Albania")
        .single()
        .execute()
    )

    assert res.data == {"country_name": "ALBANIA", "iso": "AL"}


def test_not_equal(postgrest_client: SyncPostgrestClient) -> None:
    res = (
        postgrest_client.from_("users")
        .select("id, name")
        .neq("name", "Jane")
        .single()
        .execute()
    )

    assert res.data == {"id": 1, "name": "Michael"}


def test_greater_than(postgrest_client: SyncPostgrestClient) -> None:
    res = (
        postgrest_client.from_("users")
        .select("id, name")
        .gt("id", 1)
        .single()
        .execute()
    )

    assert res.data == {"id": 2, "name": "Jane"}


def test_greater_than_or_equals_to(
    postgrest_client: SyncPostgrestClient,
) -> None:
    res = postgrest_client.from_("users").select("id, name").gte("id", 1).execute()

    assert res.data == [{"id": 1, "name": "Michael"}, {"id": 2, "name": "Jane"}]


def test_contains_dictionary(postgrest_client: SyncPostgrestClient) -> None:
    res = (
        postgrest_client.from_("users")
        .select("name")
        .contains("address", {"postcode": 90210})
        .single()
        .execute()
    )

    assert res.data == {"name": "Michael"}


def test_contains_any_item(postgrest_client: SyncPostgrestClient) -> None:
    res = (
        postgrest_client.from_("issues")
        .select("title")
        .contains("tags", ["is:open", "priority:low"])
        .execute()
    )

    assert res.data == [{"title": "Cache invalidation is not working"}]


def test_contains_on_range(postgrest_client: SyncPostgrestClient) -> None:
    res = (
        postgrest_client.from_("reservations")
        .select("id, room_name")
        .contains("during", "[2000-01-01 13:00, 2000-01-01 13:30)")
        .execute()
    )

    assert res.data == [{"id": 1, "room_name": "Emerald"}]


def test_contained_by_mixed_items(postgrest_client: SyncPostgrestClient) -> None:
    res = (
        postgrest_client.from_("reservations")
        .select("id, room_name")
        .contained_by("during", "[2000-01-01 00:00, 2000-01-01 23:59)")
        .execute()
    )

    assert res.data == [{"id": 1, "room_name": "Emerald"}]


def test_range_greater_than(postgrest_client: SyncPostgrestClient) -> None:
    res = (
        postgrest_client.from_("reservations")
        .select("id, room_name")
        .range_gt("during", "2000-01-02 08:00", "2000-01-02 09:00")
        .execute()
    )

    assert res.data == [{"id": 2, "room_name": "Topaz"}]


def test_range_greater_than_or_equal_to(
    postgrest_client: SyncPostgrestClient,
) -> None:
    res = (
        postgrest_client.from_("reservations")
        .select("id, room_name")
        .range_gte("during", "2000-01-02 08:30", "2000-01-02 09:30")
        .execute()
    )

    assert res.data == [{"id": 2, "room_name": "Topaz"}]


def test_range_less_than(postgrest_client: SyncPostgrestClient) -> None:
    res = (
        postgrest_client.from_("reservations")
        .select("id, room_name")
        .range_lt("during", "2000-01-01 15:00", "2000-01-02 16:00")
        .execute()
    )

    assert res.data == [{"id": 1, "room_name": "Emerald"}]


def test_range_less_than_or_equal_to(
    postgrest_client: SyncPostgrestClient,
) -> None:
    res = (
        postgrest_client.from_("reservations")
        .select("id, room_name")
        .range_lte("during", "2000-01-01 14:00", "2000-01-01 16:00")
        .execute()
    )

    assert res.data == [{"id": 1, "room_name": "Emerald"}]


def test_range_adjacent(postgrest_client: SyncPostgrestClient) -> None:
    res = (
        postgrest_client.from_("reservations")
        .select("id, room_name")
        .range_adjacent("during", "2000-01-01 12:00", "2000-01-01 13:00")
        .execute()
    )

    assert res.data == [{"id": 1, "room_name": "Emerald"}]


def test_overlaps(postgrest_client: SyncPostgrestClient) -> None:
    res = (
        postgrest_client.from_("issues")
        .select("title")
        .overlaps("tags", ["is:closed", "severity:high"])
        .execute()
    )

    assert res.data == [
        {"title": "Cache invalidation is not working"},
        {"title": "Add alias to filters"},
    ]


def test_overlaps_with_timestamp_range(
    postgrest_client: SyncPostgrestClient,
) -> None:
    res = (
        postgrest_client.from_("reservations")
        .select("room_name")
        .overlaps("during", "[2000-01-01 12:45, 2000-01-01 13:15)")
        .execute()
    )

    assert res.data == [
        {"room_name": "Emerald"},
    ]


def test_like(postgrest_client: SyncPostgrestClient) -> None:
    res = (
        postgrest_client.from_("countries")
        .select("country_name, iso")
        .like("nicename", "%Alba%")
        .execute()
    )

    assert res.data == [{"country_name": "ALBANIA", "iso": "AL"}]


def test_ilike(postgrest_client: SyncPostgrestClient) -> None:
    res = (
        postgrest_client.from_("countries")
        .select("country_name, iso")
        .ilike("nicename", "%alban%")
        .execute()
    )

    assert res.data == [{"country_name": "ALBANIA", "iso": "AL"}]


def test_like_all_of(postgrest_client: SyncPostgrestClient) -> None:
    res = (
        postgrest_client.from_("countries")
        .select("nicename, iso")
        .like_all_of("nicename", "A*,*n")
        .execute()
    )

    assert res.data == [{"iso": "AF", "nicename": "Afghanistan"}]


def test_like_any_of(postgrest_client: SyncPostgrestClient) -> None:
    res = (
        postgrest_client.from_("countries")
        .select("nicename, iso")
        .like_any_of("nicename", "Al*,*ia")
        .execute()
    )

    assert res.data == [
        {"iso": "AL", "nicename": "Albania"},
        {"iso": "DZ", "nicename": "Algeria"},
    ]


def test_ilike_all_of(postgrest_client: SyncPostgrestClient) -> None:
    res = (
        postgrest_client.from_("countries")
        .select("nicename, iso")
        .ilike_all_of("nicename", "a*,*n")
        .execute()
    )

    assert res.data == [{"iso": "AF", "nicename": "Afghanistan"}]


def test_ilike_any_of(postgrest_client: SyncPostgrestClient) -> None:
    res = (
        postgrest_client.from_("countries")
        .select("nicename, iso")
        .ilike_any_of("nicename", "al*,*ia")
        .execute()
    )

    assert res.data == [
        {"iso": "AL", "nicename": "Albania"},
        {"iso": "DZ", "nicename": "Algeria"},
    ]


def test_is_(postgrest_client: SyncPostgrestClient) -> None:
    res = (
        postgrest_client.from_("countries")
        .select("country_name, iso")
        .is_("numcode", "null")
        .limit(1)
        .order("nicename")
        .execute()
    )

    assert res.data == [{"country_name": "ANTARCTICA", "iso": "AQ"}]


def test_is_not(postgrest_client: SyncPostgrestClient) -> None:
    res = (
        postgrest_client.from_("countries")
        .select("country_name, iso")
        .not_.is_("numcode", "null")
        .limit(1)
        .order("nicename")
        .execute()
    )

    assert res.data == [{"country_name": "AFGHANISTAN", "iso": "AF"}]


def test_in_(postgrest_client: SyncPostgrestClient) -> None:
    res = (
        postgrest_client.from_("countries")
        .select("country_name, iso")
        .in_("nicename", ["Albania", "Algeria"])
        .execute()
    )

    assert res.data == [
        {"country_name": "ALBANIA", "iso": "AL"},
        {"country_name": "ALGERIA", "iso": "DZ"},
    ]


def test_or_(postgrest_client: SyncPostgrestClient) -> None:
    res = (
        postgrest_client.from_("countries")
        .select("country_name, iso")
        .or_("iso.eq.DZ,nicename.eq.Albania")
        .execute()
    )

    assert res.data == [
        {"country_name": "ALBANIA", "iso": "AL"},
        {"country_name": "ALGERIA", "iso": "DZ"},
    ]


def test_or_with_and(postgrest_client: SyncPostgrestClient) -> None:
    res = (
        postgrest_client.from_("countries")
        .select("country_name, iso")
        .or_("phonecode.gt.506,and(iso.eq.AL,nicename.eq.Albania)")
        .execute()
    )

    assert res.data == [
        {"country_name": "ALBANIA", "iso": "AL"},
        {"country_name": "TRINIDAD AND TOBAGO", "iso": "TT"},
    ]


def test_or_in(postgrest_client: SyncPostgrestClient) -> None:
    res = (
        postgrest_client.from_("issues")
        .select("id, title")
        .or_("id.in.(1,4),tags.cs.{is:open,priority:high}")
        .execute()
    )

    assert res.data == [
        {"id": 1, "title": "Cache invalidation is not working"},
        {"id": 3, "title": "Add missing postgrest filters"},
        {"id": 4, "title": "Add alias to filters"},
    ]


def test_or_on_reference_table(postgrest_client: SyncPostgrestClient) -> None:
    res = (
        postgrest_client.from_("countries")
        .select("country_name, cities!inner(name)")
        .or_("country_id.eq.10,name.eq.Paris", reference_table="cities")
        .execute()
    )

    assert res.data == [
        {
            "country_name": "UNITED KINGDOM",
            "cities": [
                {"name": "London"},
                {"name": "Manchester"},
                {"name": "Liverpool"},
                {"name": "Bristol"},
            ],
        },
    ]


def test_explain_json(postgrest_client: SyncPostgrestClient) -> None:
    res = (
        postgrest_client.from_("countries")
        .select("country_name, cities!inner(name)")
        .or_("country_id.eq.10,name.eq.Paris", reference_table="cities")
        .explain(
            format="json",
            analyze=True,
            verbose=False,
            settings=False,
            wal=False,
            buffers=False,
        )
        .execute()
    )
    assert isinstance(res.data, list)
    assert isinstance(res.data[0], dict)
    assert isinstance(res.data[0]["Plan"], dict)
    assert res.data[0]["Plan"]["Node Type"] == "Aggregate"


def test_csv(postgrest_client: SyncPostgrestClient) -> None:
    res = (
        postgrest_client.from_("countries")
        .select("country_name, iso")
        .in_("nicename", ["Albania", "Algeria"])
        .csv()
        .execute()
    )
    assert "ALBANIA,AL\nALGERIA,DZ" in res.data


def test_explain_text(postgrest_client: SyncPostgrestClient) -> None:
    res = (
        postgrest_client.from_("countries")
        .select("country_name, cities!inner(name)")
        .or_("country_id.eq.10,name.eq.Paris", reference_table="cities")
        .explain(
            analyze=True,
            verbose=True,
            settings=True,
            wal=True,
            buffers=True,
            format="text",
        )
        .execute()
    )
    assert (
        "((cities_1.country_id = countries.id) AND ((cities_1.country_id = '10'::bigint) OR (cities_1.name = 'Paris'::text)))"
        in res
    )


def test_rpc_with_single(postgrest_client: SyncPostgrestClient) -> None:
    res = (
        postgrest_client.rpc("list_stored_countries", {})
        .select("nicename, country_name, iso")
        .eq("nicename", "Albania")
        .single()
        .execute()
    )

    assert res.data == {"nicename": "Albania", "country_name": "ALBANIA", "iso": "AL"}


def test_rpc_with_maybe_single(postgrest_client: SyncPostgrestClient) -> None:
    res = (
        postgrest_client.rpc("list_stored_countries", {})
        .select("nicename, country_name, iso")
        .eq("nicename", "Albania")
        .maybe_single()
        .execute()
    )

    assert res
    assert res.data == {"nicename": "Albania", "country_name": "ALBANIA", "iso": "AL"}


def test_rpc_with_maybe_single_no_match(
    postgrest_client: SyncPostgrestClient,
) -> None:
    res = (
        postgrest_client.rpc("list_stored_countries", {})
        .select("nicename, country_name, iso")
        .eq("nicename", "Wonderland")
        .maybe_single()
        .execute()
    )

    assert res is None


def test_rpc_with_maybe_single_multiple_rows(
    postgrest_client: SyncPostgrestClient,
) -> None:
    with pytest.raises(APIError) as exc_info:
        (
            postgrest_client.rpc("list_stored_countries", {})
            .select("nicename, country_name, iso")
            .maybe_single()
            .execute()
        )

    assert exc_info.value.code == "406"
    assert exc_info.value.message == "Cannot coerce the result to a single JSON object"
    assert exc_info.value.details == "The result contains more than one row."


def test_rpc_with_limit(postgrest_client: SyncPostgrestClient) -> None:
    res = (
        postgrest_client.rpc("list_stored_countries", {})
        .select("nicename, country_name, iso")
        .eq("nicename", "Albania")
        .limit(1)
        .execute()
    )

    assert res.data == [{"nicename": "Albania", "country_name": "ALBANIA", "iso": "AL"}]


def test_rpc_with_range(postgrest_client: SyncPostgrestClient) -> None:
    res = (
        postgrest_client.rpc("list_stored_countries", {})
        .select("nicename, iso")
        .range(1, 2)
        .execute()
    )

    assert res.data == [
        {"nicename": "Albania", "iso": "AL"},
        {"nicename": "Algeria", "iso": "DZ"},
    ]


def test_rpc_post_with_args(postgrest_client: SyncPostgrestClient) -> None:
    res = (
        postgrest_client.rpc("search_countries_by_name", {"search_name": "Alban"})
        .select("nicename, iso")
        .execute()
    )
    assert res.data == [{"nicename": "Albania", "iso": "AL"}]


def test_rpc_get_with_args(postgrest_client: SyncPostgrestClient) -> None:
    res = (
        postgrest_client.rpc(
            "search_countries_by_name", {"search_name": "Alger"}, get=True
        )
        .select("nicename, iso")
        .execute()
    )
    assert res.data == [{"nicename": "Algeria", "iso": "DZ"}]


def test_rpc_get_with_count(postgrest_client: SyncPostgrestClient) -> None:
    res = (
        postgrest_client.rpc(
            "search_countries_by_name",
            {"search_name": "Al"},
            get=True,
            count=CountMethod.exact,
        )
        .select("nicename")
        .execute()
    )
    assert res.count == 2
    assert res.data == [{"nicename": "Albania"}, {"nicename": "Algeria"}]


def test_rpc_head_count(postgrest_client: SyncPostgrestClient) -> None:
    res = postgrest_client.rpc(
        "search_countries_by_name",
        {"search_name": "Al"},
        head=True,
        count=CountMethod.exact,
    ).execute()

    assert res == 2


def test_order(postgrest_client: SyncPostgrestClient) -> None:
    res = (
        postgrest_client.from_("countries")
        .select("country_name, iso")
        .limit(3)
        .order("nicename", desc=True)
        .execute()
    )

    assert res.data == [
        {"country_name": "ZIMBABWE", "iso": "ZW"},
        {"country_name": "UNITED STATES", "iso": "US"},
        {"country_name": "UNITED KINGDOM", "iso": "GB"},
    ]


def test_order_on_foreign_table(postgrest_client: SyncPostgrestClient) -> None:
    res = (
        postgrest_client.from_("orchestral_sections")
        .select("name, instruments(name)")
        .order("name", desc=True, foreign_table="instruments")
        .execute()
    )

    assert res.data == [
        {"name": "strings", "instruments": [{"name": "violin"}, {"name": "harp"}]},
        {"name": "woodwinds", "instruments": []},
    ]


def test_get_retry_503(postgrest_client: SyncPostgrestClient) -> None:
    from supabase_utils.http.headers import Headers
    from supabase_utils.http.request import Request

    retry_count = 0
    original_send = postgrest_client.executor.session.send

    def fake_send(request: Request) -> Response:
        nonlocal retry_count
        if retry_count > 0:
            assert request.headers["X-Retry-Count"] == str(retry_count)
        if retry_count < 3:
            retry_count += 1
            return Response(
                content=b"error", status=503, headers=Headers.empty(), request=request
            )
        return original_send(request)

    from unittest.mock import patch

    with patch.object(
        postgrest_client.executor.session, "send", wraps=fake_send
    ) as _mock_send:
        query = (
            postgrest_client.from_("orchestral_sections")
            .select("name, instruments(name)")
            .order("name", desc=True, foreign_table="instruments")
        )
        res = query.execute()

        assert res.data == [
            {"name": "strings", "instruments": [{"name": "violin"}, {"name": "harp"}]},
            {"name": "woodwinds", "instruments": []},
        ]
        assert retry_count > 0


def test_get_retry_503_does_not_retry_when_disabled(
    postgrest_client: SyncPostgrestClient,
) -> None:
    from supabase_utils.http.headers import Headers
    from supabase_utils.http.request import Request

    retry_count = 0
    original_send = postgrest_client.executor.session.send

    def fake_send(request: Request) -> Response:
        nonlocal retry_count
        if retry_count > 0:
            assert request.headers["X-Retry-Count"] == str(retry_count)
        if retry_count < 3:
            retry_count += 1
            return Response(
                content=b"error", status=503, headers=Headers.empty(), request=request
            )
        return original_send(request)

    from unittest.mock import patch

    import pytest

    from postgrest.exceptions import APIError

    with patch.object(
        postgrest_client.executor.session, "send", wraps=fake_send
    ) as _mock_send:
        query = (
            postgrest_client.from_("orchestral_sections")
            .select("name, instruments(name)")
            .order("name", desc=True, foreign_table="instruments")
            .retry(False)
        )
        with pytest.raises(APIError):
            query.execute()

        assert retry_count == 1


def test_order_retry_400_doesnt_retry(postgrest_client: SyncPostgrestClient) -> None:
    from supabase_utils.http.headers import Headers
    from supabase_utils.http.request import Request

    retry_count = 0
    original_send = postgrest_client.executor.session.send

    def fake_send(request: Request) -> Response:
        nonlocal retry_count
        if retry_count < 3:
            retry_count += 1
            return Response(
                status=400,
                content=b'{"message": "JSON could not be generated", "code": "400", "hint": "Refer to full message for details", "details": ""}',
                headers=Headers.empty(),
                request=request,
            )
        return original_send(request)

    from unittest.mock import patch

    import pytest

    from postgrest.exceptions import APIError

    with patch.object(
        postgrest_client.executor.session, "send", wraps=fake_send
    ) as _mock_send:
        query = (
            postgrest_client.from_("orchestral_sections")
            .select("name, instruments(name)")
            .order("name", desc=True, foreign_table="instruments")
        )
        with pytest.raises(APIError):
            query.execute()

        assert retry_count == 1


def test_rpc_returning_a_number(postgrest_client: SyncPostgrestClient) -> None:
    res = postgrest_client.rpc("count_stored_countries", {}).execute()

    assert isinstance(res.data, int)
    assert res.data > 0


def test_rpc_returning_text(postgrest_client: SyncPostgrestClient) -> None:
    res = postgrest_client.rpc("country_iso", {"search_name": "Albania"}).execute()

    assert res.data == "AL"


def test_rpc_returning_a_single_row(postgrest_client: SyncPostgrestClient) -> None:
    res = (
        postgrest_client.rpc("stored_country", {"search_name": "Albania"})
        .select("nicename, iso")
        .execute()
    )

    assert res.data == {"nicename": "Albania", "iso": "AL"}


def test_rpc_as_csv(postgrest_client: SyncPostgrestClient) -> None:
    res = (
        postgrest_client.rpc("stored_country", {"search_name": "Albania"})
        .select("iso")
        .csv()
        .execute()
    )

    assert res.data == "iso\nAL"


@pytest.mark.parametrize(
    ("column", "value"),
    [
        ("data->>a.b", "dotted"),
        ("data->>a,b", "comma"),
        ('data->>"0"', "text zero"),
        ("data->items->>0", "first"),
        ("data->items->>-1", "second"),
        ("data->items->>0::text", "first"),
    ],
)
def test_eq_on_a_json_path(
    postgrest_client: SyncPostgrestClient, column: str, value: str
) -> None:
    res = postgrest_client.from_("documents").select("id").eq(column, value).execute()

    assert res.data == [{"id": 1}]


class FilesInsert(TypedDict):
    id: NotRequired[Annotated[UUID, Field(alias="id")]]
    name: Annotated[str, Field(alias="name")]
    content: NotRequired[Annotated[bytes | None, Field(alias="content")]]
    uploaded_at: NotRequired[Annotated[datetime | None, Field(alias="uploaded_at")]]
    uploaded_on: NotRequired[Annotated[date | None, Field(alias="uploaded_on")]]


class FilesUpdate(TypedDict, total=False):
    name: Annotated[str, Field(alias="name")]
    content: Annotated[bytes | None, Field(alias="content")]


def test_writes_of_a_generated_row_round_trip(
    postgrest_client: SyncPostgrestClient,
) -> None:
    file_id = uuid4()
    row: FilesInsert = {
        "id": file_id,
        "name": "notes.txt",
        "content": b"\x00\xffab",
        "uploaded_at": datetime(2024, 5, 1, 12, 30, tzinfo=UTC),
        "uploaded_on": date(2024, 5, 1),
    }
    files = postgrest_client.from_("files")
    try:
        inserted = files.insert(row).execute()
        assert inserted.data == [
            {
                "id": str(file_id),
                "name": "notes.txt",
                "content": "\\x00ff6162",
                "uploaded_at": "2024-05-01T12:30:00+00:00",
                "uploaded_on": "2024-05-01",
            }
        ]

        changes: FilesUpdate = {"content": b"xy"}
        updated = files.update(changes).eq("id", str(file_id)).execute()
        assert updated.data == [{**inserted.data[0], "content": "\\x7879"}]

        upserted = (
            files.upsert({"id": file_id, "name": "renamed.txt", "content": None})
            .select("name, content")
            .execute()
        )
        assert upserted.data == [{"name": "renamed.txt", "content": None}]
    finally:
        files.delete().eq("id", str(file_id)).execute()


def test_is_distinct(postgrest_client: SyncPostgrestClient) -> None:
    res = (
        postgrest_client.from_("books")
        .select("id")
        .is_distinct("isbn", "9780441013593")
        .order("id")
        .execute()
    )

    assert res.data == [{"id": 2}, {"id": 3}]


def test_geojson(postgrest_client: SyncPostgrestClient) -> None:
    res = postgrest_client.from_("places").select("*").order("id").geojson().execute()

    assert res.data["type"] == "FeatureCollection"
    features = res.data["features"]
    assert isinstance(features, list)
    assert len(features) == 2
    null_island = features[0]
    assert isinstance(null_island, dict)
    assert null_island["geometry"] == {"type": "Point", "coordinates": [0, 0]}


def test_dry_run_of_an_insert(postgrest_client: SyncPostgrestClient) -> None:
    books = postgrest_client.from_("books")

    res = books.insert({"title": "Ghost"}).single().dry_run().execute()

    assert res.data["title"] == "Ghost"
    count = books.select("id", count=CountMethod.exact).eq("title", "Ghost").execute()
    assert count.count == 0


def test_dry_run_of_an_update(postgrest_client: SyncPostgrestClient) -> None:
    books = postgrest_client.from_("books")

    res = books.update({"pages": 1}).all().dry_run().select("pages").execute()

    assert res.data == [{"pages": 1}] * 3
    dune = books.select("pages").eq("id", 1).single().execute()
    assert dune.data == {"pages": 412}
