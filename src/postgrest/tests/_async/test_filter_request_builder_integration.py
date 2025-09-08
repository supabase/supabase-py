from postgrest import CountMethod

from .client import rest_client, rest_client_httpx


async def test_multivalued_param_httpx():
    res = (
        await rest_client_httpx()
        .from_("countries")
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


async def test_multivalued_param():
    res = (
        await rest_client()
        .from_("countries")
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


async def test_match():
    res = (
        await rest_client()
        .from_("countries")
        .select("country_name, iso")
        .match({"numcode": 8, "nicename": "Albania"})
        .single()
        .execute()
    )

    assert res.data == {"country_name": "ALBANIA", "iso": "AL"}


async def test_equals():
    res = (
        await rest_client()
        .from_("countries")
        .select("country_name, iso")
        .eq("nicename", "Albania")
        .single()
        .execute()
    )

    assert res.data == {"country_name": "ALBANIA", "iso": "AL"}


async def test_not_equal():
    res = (
        await rest_client()
        .from_("users")
        .select("id, name")
        .neq("name", "Jane")
        .single()
        .execute()
    )

    assert res.data == {"id": 1, "name": "Michael"}


async def test_greater_than():
    res = (
        await rest_client()
        .from_("users")
        .select("id, name")
        .gt("id", 1)
        .single()
        .execute()
    )

    assert res.data == {"id": 2, "name": "Jane"}


async def test_greater_than_or_equals_to():
    res = await rest_client().from_("users").select("id, name").gte("id", 1).execute()

    assert res.data == [{"id": 1, "name": "Michael"}, {"id": 2, "name": "Jane"}]


async def test_contains_dictionary():
    res = (
        await rest_client()
        .from_("users")
        .select("name")
        .contains("address", {"postcode": 90210})
        .single()
        .execute()
    )

    assert res.data == {"name": "Michael"}


async def test_contains_any_item():
    res = (
        await rest_client()
        .from_("issues")
        .select("title")
        .contains("tags", ["is:open", "priority:low"])
        .execute()
    )

    assert res.data == [{"title": "Cache invalidation is not working"}]


async def test_contains_on_range():
    res = (
        await rest_client()
        .from_("reservations")
        .select("id, room_name")
        .contains("during", "[2000-01-01 13:00, 2000-01-01 13:30)")
        .execute()
    )

    assert res.data == [{"id": 1, "room_name": "Emerald"}]


async def test_contained_by_mixed_items():
    res = (
        await rest_client()
        .from_("reservations")
        .select("id, room_name")
        .contained_by("during", "[2000-01-01 00:00, 2000-01-01 23:59)")
        .execute()
    )

    assert res.data == [{"id": 1, "room_name": "Emerald"}]


async def test_range_greater_than():
    res = (
        await rest_client()
        .from_("reservations")
        .select("id, room_name")
        .range_gt("during", ["2000-01-02 08:00", "2000-01-02 09:00"])
        .execute()
    )

    assert res.data == [{"id": 2, "room_name": "Topaz"}]


async def test_range_greater_than_or_equal_to():
    res = (
        await rest_client()
        .from_("reservations")
        .select("id, room_name")
        .range_gte("during", ["2000-01-02 08:30", "2000-01-02 09:30"])
        .execute()
    )

    assert res.data == [{"id": 2, "room_name": "Topaz"}]


async def test_range_less_than():
    res = (
        await rest_client()
        .from_("reservations")
        .select("id, room_name")
        .range_lt("during", ["2000-01-01 15:00", "2000-01-02 16:00"])
        .execute()
    )

    assert res.data == [{"id": 1, "room_name": "Emerald"}]


async def test_range_less_than_or_equal_to():
    res = (
        await rest_client()
        .from_("reservations")
        .select("id, room_name")
        .range_lte("during", ["2000-01-01 14:00", "2000-01-01 16:00"])
        .execute()
    )

    assert res.data == [{"id": 1, "room_name": "Emerald"}]


async def test_range_adjacent():
    res = (
        await rest_client()
        .from_("reservations")
        .select("id, room_name")
        .range_adjacent("during", ["2000-01-01 12:00", "2000-01-01 13:00"])
        .execute()
    )

    assert res.data == [{"id": 1, "room_name": "Emerald"}]


async def test_overlaps():
    res = (
        await rest_client()
        .from_("issues")
        .select("title")
        .overlaps("tags", ["is:closed", "severity:high"])
        .execute()
    )

    assert res.data == [
        {"title": "Cache invalidation is not working"},
        {"title": "Add alias to filters"},
    ]


async def test_overlaps_with_timestamp_range():
    res = (
        await rest_client()
        .from_("reservations")
        .select("room_name")
        .overlaps("during", "[2000-01-01 12:45, 2000-01-01 13:15)")
        .execute()
    )

    assert res.data == [
        {"room_name": "Emerald"},
    ]


async def test_like():
    res = (
        await rest_client()
        .from_("countries")
        .select("country_name, iso")
        .like("nicename", "%Alba%")
        .execute()
    )

    assert res.data == [{"country_name": "ALBANIA", "iso": "AL"}]


async def test_ilike():
    res = (
        await rest_client()
        .from_("countries")
        .select("country_name, iso")
        .ilike("nicename", "%alban%")
        .execute()
    )

    assert res.data == [{"country_name": "ALBANIA", "iso": "AL"}]


async def test_like_all_of():
    res = (
        await rest_client()
        .from_("countries")
        .select("nicename, iso")
        .like_all_of("nicename", "A*,*n")
        .execute()
    )

    assert res.data == [{"iso": "AF", "nicename": "Afghanistan"}]


async def test_like_any_of():
    res = (
        await rest_client()
        .from_("countries")
        .select("nicename, iso")
        .like_any_of("nicename", "Al*,*ia")
        .execute()
    )

    assert res.data == [
        {"iso": "AL", "nicename": "Albania"},
        {"iso": "DZ", "nicename": "Algeria"},
    ]


async def test_ilike_all_of():
    res = (
        await rest_client()
        .from_("countries")
        .select("nicename, iso")
        .ilike_all_of("nicename", "a*,*n")
        .execute()
    )

    assert res.data == [{"iso": "AF", "nicename": "Afghanistan"}]


async def test_ilike_any_of():
    res = (
        await rest_client()
        .from_("countries")
        .select("nicename, iso")
        .ilike_any_of("nicename", "al*,*ia")
        .execute()
    )

    assert res.data == [
        {"iso": "AL", "nicename": "Albania"},
        {"iso": "DZ", "nicename": "Algeria"},
    ]


async def test_is_():
    res = (
        await rest_client()
        .from_("countries")
        .select("country_name, iso")
        .is_("numcode", "null")
        .limit(1)
        .order("nicename")
        .execute()
    )

    assert res.data == [{"country_name": "ANTARCTICA", "iso": "AQ"}]


async def test_is_not():
    res = (
        await rest_client()
        .from_("countries")
        .select("country_name, iso")
        .not_.is_("numcode", "null")
        .limit(1)
        .order("nicename")
        .execute()
    )

    assert res.data == [{"country_name": "AFGHANISTAN", "iso": "AF"}]


async def test_in_():
    res = (
        await rest_client()
        .from_("countries")
        .select("country_name, iso")
        .in_("nicename", ["Albania", "Algeria"])
        .execute()
    )

    assert res.data == [
        {"country_name": "ALBANIA", "iso": "AL"},
        {"country_name": "ALGERIA", "iso": "DZ"},
    ]


async def test_or_():
    res = (
        await rest_client()
        .from_("countries")
        .select("country_name, iso")
        .or_("iso.eq.DZ,nicename.eq.Albania")
        .execute()
    )

    assert res.data == [
        {"country_name": "ALBANIA", "iso": "AL"},
        {"country_name": "ALGERIA", "iso": "DZ"},
    ]


async def test_or_with_and():
    res = (
        await rest_client()
        .from_("countries")
        .select("country_name, iso")
        .or_("phonecode.gt.506,and(iso.eq.AL,nicename.eq.Albania)")
        .execute()
    )

    assert res.data == [
        {"country_name": "ALBANIA", "iso": "AL"},
        {"country_name": "TRINIDAD AND TOBAGO", "iso": "TT"},
    ]


async def test_or_in():
    res = (
        await rest_client()
        .from_("issues")
        .select("id, title")
        .or_("id.in.(1,4),tags.cs.{is:open,priority:high}")
        .execute()
    )

    assert res.data == [
        {"id": 1, "title": "Cache invalidation is not working"},
        {"id": 3, "title": "Add missing postgrest filters"},
        {"id": 4, "title": "Add alias to filters"},
    ]


async def test_or_on_reference_table():
    res = (
        await rest_client()
        .from_("countries")
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


async def test_explain_json():
    res = (
        await rest_client()
        .from_("countries")
        .select("country_name, cities!inner(name)")
        .or_("country_id.eq.10,name.eq.Paris", reference_table="cities")
        .explain(format="json", analyze=True)
        .execute()
    )
    assert res.data[0]["Plan"]["Node Type"] == "Aggregate"


async def test_csv():
    res = (
        await rest_client()
        .from_("countries")
        .select("country_name, iso")
        .in_("nicename", ["Albania", "Algeria"])
        .csv()
        .execute()
    )
    assert "ALBANIA,AL\nALGERIA,DZ" in res.data


async def test_explain_text():
    res = (
        await rest_client()
        .from_("countries")
        .select("country_name, cities!inner(name)")
        .or_("country_id.eq.10,name.eq.Paris", reference_table="cities")
        .explain(analyze=True, verbose=True, settings=True, buffers=True, wal=True)
        .execute()
    )
    assert (
        "((cities_1.country_id = countries.id) AND ((cities_1.country_id = '10'::bigint) OR (cities_1.name = 'Paris'::text)))"
        in res
    )


async def test_rpc_with_single():
    res = (
        await rest_client()
        .rpc("list_stored_countries", {})
        .select("nicename, country_name, iso")
        .eq("nicename", "Albania")
        .single()
        .execute()
    )

    assert res.data == {"nicename": "Albania", "country_name": "ALBANIA", "iso": "AL"}


async def test_rpc_with_limit():
    res = (
        await rest_client()
        .rpc("list_stored_countries", {})
        .select("nicename, country_name, iso")
        .eq("nicename", "Albania")
        .limit(1)
        .execute()
    )

    assert res.data == [{"nicename": "Albania", "country_name": "ALBANIA", "iso": "AL"}]


async def test_rpc_with_range():
    res = (
        await rest_client()
        .rpc("list_stored_countries", {})
        .select("nicename, iso")
        .range(1, 2)
        .execute()
    )

    assert res.data == [
        {"nicename": "Albania", "iso": "AL"},
        {"nicename": "Algeria", "iso": "DZ"},
    ]


async def test_rpc_post_with_args():
    res = (
        await rest_client()
        .rpc("search_countries_by_name", {"search_name": "Alban"})
        .select("nicename, iso")
        .execute()
    )
    assert res.data == [{"nicename": "Albania", "iso": "AL"}]


async def test_rpc_get_with_args():
    res = (
        await rest_client()
        .rpc("search_countries_by_name", {"search_name": "Alger"}, get=True)
        .select("nicename, iso")
        .execute()
    )
    assert res.data == [{"nicename": "Algeria", "iso": "DZ"}]


async def test_rpc_get_with_count():
    res = (
        await rest_client()
        .rpc(
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


async def test_rpc_head_count():
    res = (
        await rest_client()
        .rpc(
            "search_countries_by_name",
            {"search_name": "Al"},
            head=True,
            count=CountMethod.exact,
        )
        .execute()
    )

    assert res.count == 2
    assert res.data == []


async def test_order():
    res = (
        await rest_client()
        .from_("countries")
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


async def test_order_on_foreign_table():
    res = (
        await rest_client()
        .from_("orchestral_sections")
        .select("name, instruments(name)")
        .order("name", desc=True, foreign_table="instruments")
        .execute()
    )

    assert res.data == [
        {"name": "strings", "instruments": [{"name": "violin"}, {"name": "harp"}]},
        {"name": "woodwinds", "instruments": []},
    ]
