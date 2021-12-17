from supabase.lib.client_options import ClientOptions


def test__client_options__replace__returns_updated_options():
    options = ClientOptions(
        schema="schema",
        headers={"key": "value"},
        auto_refresh_token=False,
        persist_session=False,
        detect_session_in_url=False,
        local_storage={"key": "value"},
        realtime={"key": "value"},
    )

    actual = options.replace(schema="new schema")
    expected = ClientOptions(
        schema="new schema",
        headers={"key": "value"},
        auto_refresh_token=False,
        persist_session=False,
        detect_session_in_url=False,
        local_storage={"key": "value"},
        realtime={"key": "value"},
    )

    assert actual == expected


def test__client_options__replace__updates_only_new_options():
    # Arrange
    options = ClientOptions(local_storage={"key": "value"})
    new_options = options.replace()

    # Act
    new_options.local_storage["key"] = "new_value"

    # Assert
    assert options.local_storage["key"] == "value"
    assert new_options.local_storage["key"] == "new_value"
